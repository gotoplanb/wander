"""Per-spec multi-model orchestrator.

Submits ONE `code_generation` job per spec with `force_shadows=True`.
Conduct's routing engine — not the client — decides which models compete:
the rule's `preferred_model` runs as the primary, every entry in
`eval_shadow_models` runs as a parallel JobShadow with its own Cargo
artifact (conduct#35). After the primary completes, the harness calls
`list_shadows` and submits one `code_eval` against each target_job_id
(primary first, then every shadow), so per-model dimensions land on
each generated artifact independently. That's also what makes the
`/datasets/preferences?method=composite` export produce clean
same-input (chosen, rejected) pairs for the eventual DPO run (#7).

What the client owns:
- "evaluate this spec"
- the golden suite payload
- per-target code_eval orchestration + result persistence

What Conduct owns:
- which models are in the fleet (via the routing rule)
- whether/when each model runs
- artifact storage per (primary, shadow)

There is no `--model` flag and no `models=` orchestrator argument by
design. If you want a different fleet, change the routing rule.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from bench.goldens import load_golden
from bench.properties import CARGO_TOML_WITH_PROPTEST, has_property, load_property
from bench.specs import load_spec
from harness.conduct import ConductClient, ConductError, Job, Shadow

from .store import Store

log = logging.getLogger(__name__)


@dataclass
class TargetResult:
    """One model's outcome — either the primary gen or one of its shadows."""

    kind: str  # "job" | "shadow"
    model: str
    conduct_job_id: str
    parent_conduct_job_id: str | None = None
    gen_status: str = "pending"
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
    results: list[TargetResult]


_EVAL_COMMANDS = ("check", "build", "test")


def _submit_primary_gen(
    client: ConductClient, *, spec_id: str
) -> Job:
    spec = load_spec(spec_id)
    kwargs = spec.code_generation_kwargs()
    return client.create_job(
        task_type=kwargs["task_type"],
        prompt=kwargs["prompt"],
        system_prompt=kwargs["system_prompt"],
        inputs={"artifact": "cargo"},  # opt-in to tarball storage (conduct#23)
        is_async=True,                 # let the worker own the model swap
        force_shadows=True,            # fan out the rule's eval_shadow_models
    )


def _artifact_url_from(job: Job) -> str | None:
    artifact = (job.metadata or {}).get("artifact") or {}
    if "error" in artifact:
        return None
    return artifact.get("url")


def _submit_eval(
    client: ConductClient, *, target_job_id: str, golden_src: str, spec_id: str,
    property_src: str | None = None,
) -> Job:
    """Build a code_eval payload with a golden suite and (when available) a
    property suite. Property suites carry a Cargo.toml overlay that adds the
    proptest dev-dep — Conduct's sandbox handles the rest, and marking the
    suite `property: True` makes it capture the minimized counterexample on
    failure (conduct#26)."""
    suites: list[dict] = [
        {"dimension": "golden", "files": {f"tests/{spec_id}.rs": golden_src}}
    ]
    if property_src is not None:
        suites.append({
            "dimension": "property",
            "property": True,
            "files": {
                "Cargo.toml": CARGO_TOML_WITH_PROPTEST,
                f"tests/{spec_id}_prop.rs": property_src,
            },
        })
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


def _eval_one_target(
    *,
    client: ConductClient,
    store: Store,
    run_id: int,
    result: TargetResult,
    gen_row_id: int,
    golden_src: str,
    property_src: str | None,
    spec_id: str,
    poll_timeout_s: float,
) -> None:
    """Submit + poll + persist the code_eval for one target (primary or shadow).
    Mutates `result` in place and writes to the store."""
    try:
        ev = _submit_eval(
            client,
            target_job_id=result.conduct_job_id,
            golden_src=golden_src,
            spec_id=spec_id,
            property_src=property_src,
        )
    except ConductError as e:
        log.error("[%s] eval submit failed: %s", result.model, e)
        result.eval_status = "submit_failed"
        result.eval_error = str(e)
        store.upsert_eval_job(
            run_id=run_id, gen_job_id=gen_row_id, conduct_job_id=None,
            status=result.eval_status, error=result.eval_error,
        )
        return

    result.eval_job_id = ev.job_id
    eval_row_id = store.upsert_eval_job(
        run_id=run_id, gen_job_id=gen_row_id, conduct_job_id=ev.job_id,
        status=ev.status, error=None,
    )

    try:
        ev = client.poll_until_terminal(ev.job_id, timeout_s=poll_timeout_s)
    except ConductError as e:
        log.error("[%s] eval poll failed: %s", result.model, e)
        result.eval_status = "poll_failed"
        result.eval_error = str(e)
        store.upsert_eval_job(
            run_id=run_id, gen_job_id=gen_row_id, conduct_job_id=result.eval_job_id,
            status=result.eval_status, error=result.eval_error,
        )
        return

    result.eval_status = ev.status
    result.eval_error = ev.error
    store.upsert_eval_job(
        run_id=run_id, gen_job_id=gen_row_id, conduct_job_id=ev.job_id,
        status=ev.status, error=ev.error,
    )

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


def _persist_target(store: Store, *, run_id: int, r: TargetResult) -> int:
    return store.upsert_gen_job(
        run_id=run_id, kind=r.kind, model=r.model,
        conduct_job_id=r.conduct_job_id,
        parent_conduct_job_id=r.parent_conduct_job_id,
        status=r.gen_status, artifact_url=r.artifact_url, error=r.gen_error,
    )


def _target_from_primary(job: Job) -> TargetResult:
    return TargetResult(
        kind="job",
        model=job.model_used or "(unknown)",
        conduct_job_id=job.job_id,
        gen_status=job.status,
        artifact_url=_artifact_url_from(job),
        gen_error=job.error,
    )


def _target_from_shadow(s: Shadow, *, parent_id: str) -> TargetResult:
    # Shadow rows from /jobs/{id}/shadows don't carry the artifact URL on
    # the wire (the route's ShadowOut model omits shadow_metadata). We
    # don't need it client-side: code_eval's `_resolve_code_eval_target`
    # reads the shadow's artifact server-side off shadow_metadata. The
    # gen_status of "complete" (with no error) is sufficient signal to
    # proceed with the eval.
    return TargetResult(
        kind="shadow",
        model=s.model,
        conduct_job_id=s.shadow_id,
        parent_conduct_job_id=parent_id,
        gen_status=s.status,
        artifact_url=None,
        gen_error=s.error,
    )


def run_spec(
    spec_id: str,
    *,
    client: ConductClient | None = None,
    store: Store | None = None,
    poll_timeout_s: float = 600.0,
) -> RunSummary:
    """Run one spec across the Conduct-configured fleet end-to-end.

    No fleet argument by design — the harness doesn't pick models. To
    change which models compete on `code_generation`, edit the routing
    rule's `eval_shadow_models` in Conduct.
    """
    golden_src = load_golden(spec_id)  # fail fast if missing
    property_src = load_property(spec_id) if has_property(spec_id) else None

    owned_client = client is None
    owned_store = store is None
    client = client or ConductClient()
    store = store or Store()
    try:
        started = datetime.now(UTC).isoformat(timespec="seconds")
        run_id = store.start_run(spec_id, started_at=started)

        # 1) Submit the primary code_generation with force_shadows=True.
        try:
            primary = _submit_primary_gen(client, spec_id=spec_id)
        except ConductError as e:
            log.error("primary gen submit failed: %s", e)
            finished = datetime.now(UTC).isoformat(timespec="seconds")
            store.finish_run(run_id, finished_at=finished)
            raise

        # 2) Poll the primary.
        try:
            primary = client.poll_until_terminal(
                primary.job_id, timeout_s=poll_timeout_s
            )
        except ConductError as e:
            log.error("primary gen poll failed: %s", e)
            finished = datetime.now(UTC).isoformat(timespec="seconds")
            store.finish_run(run_id, finished_at=finished)
            raise

        # 3) Build target list: primary + every shadow (in deterministic order).
        primary_result = _target_from_primary(primary)
        shadows = (
            client.list_shadows(primary.job_id)
            if primary.status == "complete"
            else []
        )
        log.info(
            "primary=%s status=%s; %d shadow(s)",
            primary_result.model, primary_result.gen_status, len(shadows),
        )
        targets: list[TargetResult] = [primary_result] + [
            _target_from_shadow(s, parent_id=primary.job_id) for s in shadows
        ]

        # 4) For each target: persist + (if generated cleanly) submit code_eval.
        for t in targets:
            gen_row_id = _persist_target(store, run_id=run_id, r=t)
            if t.gen_status != "complete":
                continue
            _eval_one_target(
                client=client, store=store, run_id=run_id, result=t,
                gen_row_id=gen_row_id, golden_src=golden_src,
                property_src=property_src, spec_id=spec_id,
                poll_timeout_s=poll_timeout_s,
            )

        finished = datetime.now(UTC).isoformat(timespec="seconds")
        store.finish_run(run_id, finished_at=finished)
        return RunSummary(
            run_id=run_id, spec_id=spec_id,
            started_at=started, finished_at=finished, results=targets,
        )
    finally:
        if owned_store:
            store.close()
        if owned_client:
            client.close()
