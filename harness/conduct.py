"""Thin synchronous HTTP client for Conduct's `/jobs` + `/models` APIs.

Used by the bench runner to orchestrate `code_generation` -> `code_eval`
loops harness-side (per the "clients orchestrate, primitives are dumb"
stance from gotoplanb/conduct#22 and the README framing). Mirrors only the
endpoints the bench needs; not a full SDK.

Auth: `CONDUCT_BASE_URL` + `CONDUCT_TOKEN` env vars. Token is a client API
key minted by Conduct's `make seed` / `POST /clients` / Clients UI — format
`cdt_<random>`. See conduct/docs/auth.md for details. The admin key is
NOT what bench runs should use — admin bypasses per-client rate limits
and ownership scoping that keep multi-client deployments honest.

The MCP wrapper (mcp_server.py) sits in front of the same routes and adds
an OAuth-bearer principal layer; the bench skips that and goes direct.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import httpx

TERMINAL_STATUSES = frozenset({"complete", "failed", "cancelled"})


class ConductError(RuntimeError):
    """Any non-2xx response, transport failure, or terminal-failed job."""


@dataclass(frozen=True)
class Job:
    """Subset of Conduct's `JobOut` the bench actually reads."""

    job_id: str
    status: str
    task_type: str
    model_used: str | None
    response: str | None
    error: str | None
    media_url: str | None
    metadata: dict[str, Any]

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Job:
        return cls(
            job_id=str(d["job_id"]),
            status=str(d["status"]),
            task_type=str(d["task_type"]),
            model_used=d.get("model_used"),
            response=d.get("response"),
            error=d.get("error"),
            media_url=d.get("media_url"),
            metadata=d.get("metadata") or {},
        )


class ConductClient:
    """Synchronous wrapper. One instance per run; reuses an httpx.Client."""

    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        *,
        timeout_s: float = 30.0,
    ) -> None:
        resolved_base = base_url or os.environ.get("CONDUCT_BASE_URL")
        resolved_token = token or os.environ.get("CONDUCT_TOKEN")
        if not resolved_base:
            raise ConductError(
                "CONDUCT_BASE_URL not set (and no base_url passed)"
            )
        if not resolved_token:
            raise ConductError(
                "CONDUCT_TOKEN not set (and no token passed) — mint a client "
                "API key (cdt_<random>) per conduct/docs/auth.md"
            )
        self._client = httpx.Client(
            base_url=resolved_base.rstrip("/"),
            headers={"Authorization": f"Bearer {resolved_token}"},
            timeout=timeout_s,
        )

    def __enter__(self) -> ConductClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    # ----- endpoints ----------------------------------------------------

    def create_job(
        self,
        *,
        task_type: str,
        prompt: str,
        system_prompt: str = "",
        model: str | None = None,
        inputs: dict[str, Any] | None = None,
        is_async: bool = False,
    ) -> Job:
        """POST /jobs. Returns the job (possibly still pending if async)."""
        body: dict[str, Any] = {
            "task_type": task_type,
            "prompt": prompt,
            "system_prompt": system_prompt,
            "inputs": inputs or {},
            "async": is_async,
        }
        if model is not None:
            body["model"] = model
        resp = self._post("/jobs", json=body)
        # Async enqueue returns a minimal {job_id, status, poll_url} 202;
        # sync returns a full JobOut. Normalize by re-fetching when needed.
        if "task_type" not in resp:
            return self.get_job(str(resp["job_id"]))
        return Job.from_dict(resp)

    def get_job(self, job_id: str) -> Job:
        """GET /jobs/{job_id}."""
        return Job.from_dict(self._get(f"/jobs/{job_id}"))

    def list_local_models(self) -> list[dict[str, Any]]:
        """GET /models — returns the locally-installed Ollama models.
        Each entry: {name, status, resident, size_gb, last_used}. Cloud
        providers are not included here.
        """
        data = self._get("/models")
        return list(data.get("local") or [])

    # ----- polling ------------------------------------------------------

    def poll_until_terminal(
        self,
        job_id: str,
        *,
        interval_s: float = 2.0,
        timeout_s: float = 600.0,
    ) -> Job:
        """Block until the job hits complete/failed/cancelled, or raise on
        timeout. The interval intentionally stays short — Conduct's worker
        is fast for local jobs and we want responsive failure reporting.
        """
        deadline = time.monotonic() + timeout_s
        while True:
            job = self.get_job(job_id)
            if job.status in TERMINAL_STATUSES:
                return job
            if time.monotonic() >= deadline:
                raise ConductError(
                    f"job {job_id} did not reach terminal state within "
                    f"{timeout_s}s (last status: {job.status})"
                )
            time.sleep(interval_s)

    # ----- internals ----------------------------------------------------

    def _get(self, path: str) -> dict[str, Any]:
        try:
            r = self._client.get(path)
        except httpx.HTTPError as e:
            raise ConductError(f"GET {path}: transport error: {e}") from e
        return self._unwrap(r, "GET", path)

    def _post(self, path: str, *, json: dict[str, Any]) -> dict[str, Any]:
        try:
            r = self._client.post(path, json=json)
        except httpx.HTTPError as e:
            raise ConductError(f"POST {path}: transport error: {e}") from e
        return self._unwrap(r, "POST", path)

    @staticmethod
    def _unwrap(
        r: httpx.Response, method: str, path: str
    ) -> dict[str, Any]:
        if r.status_code >= 400:
            raise ConductError(
                f"{method} {path}: {r.status_code} {r.text[:400]}"
            )
        # 202 Accepted (async enqueue) carries {job_id, status, poll_url} —
        # we'll re-fetch via get_job; either shape is a dict here.
        return r.json()
