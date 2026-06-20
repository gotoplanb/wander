"""Per-spec multi-model orchestrator.

Sequential by design — code_generation jobs against local Ollama serialize
through one GPU anyway, and the walking skeleton's readability beats any
threading we'd add. When #6 reports a real bench across N specs * M
models, threading-per-spec lives one layer up (a parallel-pipeline driver
above run_spec), not inside it.

The fan-out to "the model fleet" is harness-driven, not delegated to
Conduct's shadow infrastructure: each (spec, model) pair becomes its own
`code_generation` job with an explicit `model=<m>` override. That keeps
the harness in control of which models compete, lets us mix cloud + local
freely, and doesn't require operator routing-rule changes per fleet
change. Conduct's eval-shadow path (`force_shadows`) remains available
for callers who want it, but the bench has no use for it.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from bench.goldens import load_golden
from bench.specs import load_spec
from harness.conduct import ConductClient, ConductError, Job

from .store import Store

log = logging.getLogger(__name__)


@dataclass
class ModelResult:
    """One model's outcome on a single spec."""

    model: str
    gen_status: str
    gen_job_id: str | None = None
    artifact_url: str | None = None
    gen_error: str | None = None
    eval_status: str | None = None
    eval_job_id: str | None = None
    eval_error: str | None = None
    dimensions: dict[str, float] = field(default_factory=dict)


@dataclass
class RunSummary:
    """Aggregate outcome for one `run_spec` invocation."""

    run_id: int
    spec_id: str
    started_at: str
    finished_at: str
    results: list[ModelResult]


# `apply_to_target` writes the evaluator's dimensions back to the gen job's
# `quality_scores`, which is what `/eval/compare` reads when assembling the
# multi-model rollup #6 will eventually print.
_EVAL_COMMANDS = ("check", "build", "test")


def _resolve_fleet(client: ConductClient, override: list[str] | None) -> list[str]:
    if override:
        return list(override)
    models = client.list_local_models()
    fleet = [
        str(m["name"]) for m in models if m.get("resident") and m.get("name")
    ]
    if not fleet:
        raise ConductError(
            "no resident local models found via GET /models — pass an explicit "
            "fleet via --model, or add models to RESIDENT_MODELS in the Conduct "
            "deployment"
        )
    return sorted(fleet)


def _submit_gen(
    client: ConductClient, *, spec_id: str, model: str
) -> Job:
    spec = load_spec(spec_id)
    kwargs = spec.code_generation_kwargs()
    return client.create_job(
        task_type=kwargs["task_type"],
        prompt=kwargs["prompt"],
        system_prompt=kwargs["system_prompt"],
        model=model,
        inputs={"artifact": "cargo"},  # opt-in to tarball storage (conduct#23)
        is_async=True,  # let the worker own the model swap if needed
    )


def _artifact_url_from(job: Job) -> str | None:
    artifact = (job.metadata or {}).get("artifact") or {}
    if "error" in artifact:
        return None
    return artifact.get("url")


def _submit_eval(
    client: ConductClient, *, target_job_id: str, golden_src: str
) -> Job:
    suites = [{"dimension": "golden", "files": {"tests/golden.rs": golden_src}}]
    return client.create_job(
        task_type="code_eval",
        prompt="",  # code_eval is deterministic — no model, no prompt
        inputs={
            "target_job_id": target_job_id,
            "commands": list(_EVAL_COMMANDS),
            "suites": suites,
            "apply_to_target": True,
        },
        is_async=True,
    )


def _parse_eval_verdict(job: Job) -> tuple[dict[str, float], dict[str, Any] | None]:
    """Extract `dimensions` (and the full verdict) from a complete code_eval job.

    The executor writes the verdict both as JSON on `response` and as a
    dict on `metadata.code_eval`. Prefer metadata (already parsed); fall
    back to response.
    """
    code_eval_meta = (job.metadata or {}).get("code_eval")
    if isinstance(code_eval_meta, dict):
        dims = code_eval_meta.get("dimensions") or {}
        return {k: float(v) for k, v in dims.items()}, code_eval_meta
    if job.response:
        try:
            parsed = json.loads(job.response)
            dims = parsed.get("dimensions") or {}
            return {k: float(v) for k, v in dims.items()}, parsed
        except (json.JSONDecodeError, TypeError, ValueError):
            return {}, None
    return {}, None


def _process_model(
    *,
    client: ConductClient,
    store: Store,
    run_id: int,
    spec_id: str,
    model: str,
    golden_src: str,
    poll_timeout_s: float,
) -> ModelResult:
    """Drive one (spec, model) end-to-end. Persists at each step so a
    Ctrl-C still leaves a partial row to inspect."""
    result = ModelResult(model=model, gen_status="pending")

    # 1) submit code_generation
    try:
        gen = _submit_gen(client, spec_id=spec_id, model=model)
    except ConductError as e:
        log.error("[%s] gen submit failed: %s", model, e)
        result.gen_status = "submit_failed"
        result.gen_error = str(e)
        store.upsert_gen_job(
            run_id=run_id, model=model, conduct_job_id=None,
            status=result.gen_status, artifact_url=None, error=result.gen_error,
        )
        return result

    result.gen_job_id = gen.job_id
    gen_row_id = store.upsert_gen_job(
        run_id=run_id, model=model, conduct_job_id=gen.job_id,
        status=gen.status, artifact_url=None, error=None,
    )

    # 2) poll code_generation
    try:
        gen = client.poll_until_terminal(gen.job_id, timeout_s=poll_timeout_s)
    except ConductError as e:
        log.error("[%s] gen poll failed: %s", model, e)
        result.gen_status = "poll_failed"
        result.gen_error = str(e)
        store.upsert_gen_job(
            run_id=run_id, model=model, conduct_job_id=result.gen_job_id,
            status=result.gen_status, artifact_url=None, error=result.gen_error,
        )
        return result

    result.gen_status = gen.status
    result.gen_error = gen.error
    result.artifact_url = _artifact_url_from(gen)
    store.upsert_gen_job(
        run_id=run_id, model=model, conduct_job_id=gen.job_id,
        status=gen.status, artifact_url=result.artifact_url, error=gen.error,
    )

    if gen.status != "complete" or not result.artifact_url:
        # The gen job didn't produce a runnable artifact — skip the eval.
        return result

    # 3) submit code_eval with the golden suite
    try:
        ev = _submit_eval(
            client, target_job_id=gen.job_id, golden_src=golden_src
        )
    except ConductError as e:
        log.error("[%s] eval submit failed: %s", model, e)
        result.eval_status = "submit_failed"
        result.eval_error = str(e)
        store.upsert_eval_job(
            run_id=run_id, gen_job_id=gen_row_id, conduct_job_id=None,
            status=result.eval_status, error=result.eval_error,
        )
        return result

    result.eval_job_id = ev.job_id
    eval_row_id = store.upsert_eval_job(
        run_id=run_id, gen_job_id=gen_row_id, conduct_job_id=ev.job_id,
        status=ev.status, error=None,
    )

    # 4) poll code_eval
    try:
        ev = client.poll_until_terminal(ev.job_id, timeout_s=poll_timeout_s)
    except ConductError as e:
        log.error("[%s] eval poll failed: %s", model, e)
        result.eval_status = "poll_failed"
        result.eval_error = str(e)
        store.upsert_eval_job(
            run_id=run_id, gen_job_id=gen_row_id, conduct_job_id=result.eval_job_id,
            status=result.eval_status, error=result.eval_error,
        )
        return result

    result.eval_status = ev.status
    result.eval_error = ev.error
    store.upsert_eval_job(
        run_id=run_id, gen_job_id=gen_row_id, conduct_job_id=ev.job_id,
        status=ev.status, error=ev.error,
    )

    # 5) extract + persist dimensions
    if ev.status == "complete":
        dims, verdict = _parse_eval_verdict(ev)
        result.dimensions = dims
        for name, score in dims.items():
            detail = (verdict or {}).get(name) if verdict else None
            store.record_dimension(
                eval_job_id=eval_row_id,
                name=name,
                score=score,
                detail=detail if isinstance(detail, dict) else None,
            )

    return result


def run_spec(
    spec_id: str,
    *,
    models: list[str] | None = None,
    client: ConductClient | None = None,
    store: Store | None = None,
    poll_timeout_s: float = 600.0,
) -> RunSummary:
    """Run one spec across the fleet end-to-end, persisting results.

    Models default to whatever local Ollama models Conduct reports as
    `resident=True`. Pass an explicit list to target cloud models or
    specific Ollama tags. The client + store args are for testing —
    callers normally let `run_spec` open both.
    """
    golden_src = load_golden(spec_id)  # fail fast if missing

    owned_client = client is None
    owned_store = store is None
    client = client or ConductClient()
    store = store or Store()
    try:
        fleet = _resolve_fleet(client, models)
        started = datetime.now(UTC).isoformat(timespec="seconds")
        run_id = store.start_run(spec_id, started_at=started)
        log.info(
            "run %d started for spec=%s fleet=%s", run_id, spec_id, fleet
        )

        results: list[ModelResult] = []
        for model in fleet:
            log.info("[%s] starting", model)
            results.append(
                _process_model(
                    client=client, store=store, run_id=run_id, spec_id=spec_id,
                    model=model, golden_src=golden_src,
                    poll_timeout_s=poll_timeout_s,
                )
            )

        finished = datetime.now(UTC).isoformat(timespec="seconds")
        store.finish_run(run_id, finished_at=finished)
        return RunSummary(
            run_id=run_id, spec_id=spec_id,
            started_at=started, finished_at=finished, results=results,
        )
    finally:
        if owned_store:
            store.close()
        if owned_client:
            client.close()
