"""Pull preference pairs from Conduct's `/datasets/preferences` endpoint.

Streams the composite-score DPO export (conduct#31) to a versioned local
directory under ``bench/dpo/datasets/``::

    bench/dpo/datasets/v20260620-143055/
        pairs.jsonl         # raw NDJSON, one {prompt, system, chosen, rejected, meta} per line
        manifest.json       # query params, row count, model distribution, SHA-256 of pairs.jsonl

Idempotent: if a recent export's manifest hash matches the freshly-pulled
content, the new export is skipped and the existing version is reused.

Auth: uses ``CONDUCT_TOKEN`` (the same client key the rest of the harness
uses). Per conduct#41, `/datasets/preferences` accepts a client key and
scopes the export to that client's own jobs — no admin token crosses the
service boundary, no cross-tenant leakage. See ``conduct/docs/datasets.md``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

DEFAULT_OUT_ROOT = Path("bench/dpo/datasets")
DEFAULT_LIMIT = 10_000  # Conduct's documented cap
REQUEST_TIMEOUT_S = 120.0


class ExportError(RuntimeError):
    """Anything that prevents producing a clean versioned dataset."""


def _stamp() -> str:
    return "v" + datetime.now(UTC).strftime("%Y%m%d-%H%M%S")


def _resolve_auth() -> tuple[str, str]:
    base = os.environ.get("CONDUCT_BASE_URL")
    token = os.environ.get("CONDUCT_TOKEN")
    if not base:
        raise ExportError("CONDUCT_BASE_URL not set")
    if not token:
        raise ExportError(
            "CONDUCT_TOKEN not set — mint a client API key (cdt_<random>) "
            "per conduct/docs/auth.md; /datasets/preferences scopes the "
            "export to this client's own jobs."
        )
    return base.rstrip("/"), token


def _query(
    *,
    task_type: str | None,
    method: str,
    min_gap: int | None,
    label_dim: str | None,
    prompt_version: int | None,
    limit: int,
) -> dict[str, str | int]:
    q: dict[str, str | int] = {"method": method, "limit": limit}
    if task_type:
        q["task_type"] = task_type
    if min_gap is not None:
        q["min_gap"] = min_gap
    if label_dim:
        q["label_dim"] = label_dim
    if prompt_version is not None:
        q["prompt_version"] = prompt_version
    return q


def _fetch_pairs(base: str, token: str, query: dict[str, str | int]) -> list[dict[str, Any]]:
    """Stream NDJSON from Conduct and return one parsed row per line.

    Rows are buffered in memory — bounded by Conduct's `limit` cap of 10000.
    At ~1KB/row that's ~10MB worst case, fine for one-shot CLI use.
    """
    rows: list[dict[str, Any]] = []
    headers = {"Authorization": f"Bearer {token}"}
    with httpx.Client(base_url=base, headers=headers, timeout=REQUEST_TIMEOUT_S) as client:
        with client.stream("GET", "/datasets/preferences", params=query) as resp:
            if resp.status_code >= 400:
                body = resp.read().decode("utf-8", errors="replace")[:400]
                raise ExportError(
                    f"GET /datasets/preferences: {resp.status_code} {body}"
                )
            for line in resp.iter_lines():
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as e:
                    raise ExportError(f"malformed NDJSON row: {e}: {line[:200]}") from e
    return rows


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    chosen_models: Counter[str] = Counter()
    rejected_models: Counter[str] = Counter()
    task_types: Counter[str] = Counter()
    prompt_versions: Counter[int] = Counter()
    for row in rows:
        meta = row.get("meta") or {}
        if cm := meta.get("chosen_model"):
            chosen_models[str(cm)] += 1
        if rm := meta.get("rejected_model"):
            rejected_models[str(rm)] += 1
        if tt := meta.get("task_type"):
            task_types[str(tt)] += 1
        if (pv := meta.get("prompt_version")) is not None:
            prompt_versions[int(pv)] += 1
    return {
        "row_count": len(rows),
        "chosen_models": dict(chosen_models),
        "rejected_models": dict(rejected_models),
        "task_types": dict(task_types),
        "prompt_versions": dict(prompt_versions),
    }


def _content_hash(rows: list[dict[str, Any]]) -> str:
    """SHA-256 over canonically-serialized rows (sort keys, no whitespace).

    Lets a re-run notice it's pulling the same data even if Conduct's row
    ordering shifted between calls — idempotency check is content-based,
    not byte-based.
    """
    h = hashlib.sha256()
    for row in sorted(
        (json.dumps(r, sort_keys=True, separators=(",", ":")) for r in rows)
    ):
        h.update(row.encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def _find_matching_version(out_root: Path, content_hash: str) -> Path | None:
    """Return an existing version dir whose manifest hash matches, else None."""
    if not out_root.exists():
        return None
    for child in sorted(out_root.iterdir(), reverse=True):
        manifest = child / "manifest.json"
        if not manifest.is_file():
            continue
        try:
            data = json.loads(manifest.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("content_hash") == content_hash:
            return child
    return None


def _write_version(
    out_dir: Path,
    rows: list[dict[str, Any]],
    *,
    base: str,
    query: dict[str, str | int],
    content_hash: str,
    summary: dict[str, Any],
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    pairs_path = out_dir / "pairs.jsonl"
    with pairs_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, separators=(",", ":")))
            f.write("\n")
    manifest = {
        "version": out_dir.name,
        "exported_at": datetime.now(UTC).isoformat(),
        "conduct_base_url": base,
        "query": query,
        "content_hash": content_hash,
        **summary,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )


def export(
    *,
    task_type: str | None = "code_generation",
    method: str = "composite",
    min_gap: int | None = None,
    label_dim: str | None = None,
    prompt_version: int | None = None,
    limit: int = DEFAULT_LIMIT,
    out_root: Path = DEFAULT_OUT_ROOT,
    version: str | None = None,
    force: bool = False,
) -> Path:
    """Pull pairs and write a versioned directory. Returns the dir path.

    With ``force=False`` (default), if a prior export has the same content
    hash the function short-circuits and returns that version's path.
    """
    base, token = _resolve_auth()
    query = _query(
        task_type=task_type,
        method=method,
        min_gap=min_gap,
        label_dim=label_dim,
        prompt_version=prompt_version,
        limit=limit,
    )
    rows = _fetch_pairs(base, token, query)
    if not rows:
        raise ExportError(
            "0 pairs returned — has the bench accumulated any same-input "
            "comparisons yet? Check Conduct's /eval/compare for code_generation."
        )
    summary = _summarize(rows)
    content_hash = _content_hash(rows)

    if not force and version is None:
        match = _find_matching_version(out_root, content_hash)
        if match is not None:
            return match

    out_dir = out_root / (version or _stamp())
    if out_dir.exists() and not force:
        raise ExportError(
            f"{out_dir} already exists — pass --force to overwrite or pick a new --version"
        )
    _write_version(
        out_dir, rows,
        base=base, query=query,
        content_hash=content_hash, summary=summary,
    )
    return out_dir


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="bench.dpo.export")
    p.add_argument("--task-type", default="code_generation",
                   help="Restrict export to one task type (default: code_generation; pass '' for all).")
    p.add_argument("--method", default="composite", choices=["composite", "score", "pairwise"],
                   help="Pair-derivation method (default: composite — uses conduct#30's weighted code-eval fold).")
    p.add_argument("--min-gap", type=int, default=None,
                   help="(score method) Minimum score gap to form a pair.")
    p.add_argument("--label-dim", default=None,
                   help="(score method) Compare on one named dimension instead of overall.")
    p.add_argument("--prompt-version", type=int, default=None,
                   help="Restrict to one resolved prompt version.")
    p.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                   help=f"Max rows (Conduct cap 10000; default {DEFAULT_LIMIT}).")
    p.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT,
                   help=f"Output root (default: {DEFAULT_OUT_ROOT}).")
    p.add_argument("--version", default=None,
                   help="Force a specific version slug instead of the auto-timestamped one.")
    p.add_argument("--force", action="store_true",
                   help="Write a new version even if content matches an existing one.")
    args = p.parse_args(argv)
    try:
        out_dir = export(
            task_type=args.task_type or None,
            method=args.method,
            min_gap=args.min_gap,
            label_dim=args.label_dim,
            prompt_version=args.prompt_version,
            limit=args.limit,
            out_root=args.out_root,
            version=args.version,
            force=args.force,
        )
    except ExportError as e:
        print(f"export failed: {e}", file=sys.stderr)
        return 2
    manifest = json.loads((out_dir / "manifest.json").read_text())
    print(f"version: {out_dir}")
    print(f"  rows:           {manifest['row_count']}")
    print(f"  chosen_models:  {manifest['chosen_models']}")
    print(f"  rejected_models:{manifest['rejected_models']}")
    print(f"  content_hash:   {manifest['content_hash'][:16]}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
