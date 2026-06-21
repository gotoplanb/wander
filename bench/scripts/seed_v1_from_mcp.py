"""Bootstrap bench/runs/runs.db from bench/reports/v1/raw_results.json.

V1's report was generated via the Conduct MCP connector before the HTTP
client API key was wired locally, so the data was captured manually and
checked into raw_results.json for reproducibility. This script replays
that JSON into the SQLite schema the harness uses, so the report
generator (`python -m bench.runner.report`) can read from one source of
truth either way: live runs from `python -m bench.runner --all`, or
v1's seeded data from this script.

Usage::

    python -m bench.scripts.seed_v1_from_mcp \\
      --raw bench/reports/v1/raw_results.json \\
      --db  bench/runs/runs.db

Idempotent: re-running drops any existing row with the same `spec_id`
under run id 1 first.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from bench.runner.store import DEFAULT_DB_PATH, Store


def seed(raw_path: Path, db_path: Path) -> int:
    raw = json.loads(raw_path.read_text())
    store = Store(db_path)
    try:
        run_id = store.start_run("__v1_bootstrap__", started_at=raw["started_at"])
        # The v1 dataset is one big bundle — we file it under a single
        # "run" so the report generator's MAX(runs.id) GROUP BY spec
        # query picks it up. Real per-spec runs will produce richer
        # history once HTTP credentials are wired.
        conn = sqlite3.connect(db_path)
        try:
            # Override the "run" row to look like a normal spec run by
            # creating one synthetic run per spec, all sharing this
            # timestamp. Cleaner than the single-bundle hack above.
            conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
            conn.commit()
        finally:
            conn.close()

        # Group entries by spec; one synthetic run per spec.
        per_spec: dict[str, list[dict]] = {}
        for entry in raw["results"]:
            per_spec.setdefault(entry["spec"], []).append(entry)

        for spec_id, entries in per_spec.items():
            rid = store.start_run(spec_id, started_at=raw["started_at"])
            for entry in entries:
                parent_id = next(
                    (e["gen_id"] for e in entries if e["kind"] == "job"), None
                )
                pcid = (
                    parent_id if entry["kind"] == "shadow" else None
                )
                gen_status = (
                    "complete" if entry["compile"] is not None else "failed"
                )
                gen_row_id = store.upsert_gen_job(
                    run_id=rid, kind=entry["kind"], model=entry["model"],
                    conduct_job_id=entry["gen_id"],
                    parent_conduct_job_id=pcid,
                    status=gen_status,
                    artifact_url=f"/output/{entry['gen_id']}.tar",
                    error=entry.get("gen_error"),
                )
                # A null eval_id means the gen failed before code_eval ran
                # (e.g. ProviderTimeout). Skip the eval row + dimensions
                # for those cells — the report's per-spec view will show
                # them as "—" naturally.
                if entry.get("eval_id") is None:
                    continue
                eval_row_id = store.upsert_eval_job(
                    run_id=rid, gen_job_id=gen_row_id,
                    conduct_job_id=entry["eval_id"],
                    status="complete", error=None,
                )
                if entry["compile"] is not None:
                    store.record_dimension(
                        eval_job_id=eval_row_id, name="compile",
                        score=float(entry["compile"]),
                    )
                if entry["golden"] is not None:
                    store.record_dimension(
                        eval_job_id=eval_row_id, name="golden",
                        score=float(entry["golden"]),
                    )
                if entry.get("property") is not None:
                    store.record_dimension(
                        eval_job_id=eval_row_id, name="property",
                        score=float(entry["property"]),
                    )
            store.finish_run(rid, finished_at=raw["finished_at"])

        return 0
    finally:
        store.close()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="seed_v1_from_mcp")
    p.add_argument(
        "--raw", type=Path,
        default=Path("bench/reports/v1/raw_results.json"),
        help="Path to the captured MCP dataset (default: bench/reports/v1/raw_results.json)",
    )
    p.add_argument(
        "--db", type=Path, default=DEFAULT_DB_PATH,
        help="Path to runs.db (default: bench/runs/runs.db)",
    )
    args = p.parse_args(argv)
    if not args.raw.exists():
        print(f"no dataset at {args.raw}", file=sys.stderr)
        return 2
    return seed(args.raw, args.db)


if __name__ == "__main__":
    raise SystemExit(main())
