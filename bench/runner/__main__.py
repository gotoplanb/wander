"""CLI entrypoint: `python -m bench.runner --spec <id>`.

The fleet is Conduct's `code_generation` routing rule (preferred_model
+ eval_shadow_models). To change which models compete, change the rule
— the harness has no model-selection knobs by design (clients don't
pick models on Conduct).

Prints a per-model summary after the run: primary first, then every
shadow, with gen + eval status and dimensions. The SQLite store at
bench/runs/runs.db keeps the persistent record.
"""

from __future__ import annotations

import argparse
import logging
import sys

from harness.conduct import ConductError

from .orchestrator import RunSummary, run_spec


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bench.runner",
        description=(
            "Run one spec across the Conduct-configured fleet "
            "(preferred_model + eval_shadow_models on the code_generation "
            "routing rule), persist per-model dimensions to "
            "bench/runs/runs.db, and print a summary."
        ),
    )
    p.add_argument(
        "--spec", required=True,
        help="Spec id (filename stem under bench/specs/*.toml), e.g. bubble_sort",
    )
    p.add_argument(
        "--poll-timeout-s", type=float, default=600.0,
        help="Per-job poll timeout in seconds (default: 600).",
    )
    p.add_argument(
        "-v", "--verbose", action="store_true",
        help="Log every step (otherwise warnings only).",
    )
    return p


def _print_summary(summary: RunSummary) -> None:
    print()
    print(f"run {summary.run_id} · spec={summary.spec_id}")
    print(f"  started:  {summary.started_at}")
    print(f"  finished: {summary.finished_at}")
    print()
    header = (
        f"  {'kind':<7} {'model':<28} {'gen':<10} {'eval':<10}  dimensions"
    )
    print(header)
    print(
        f"  {'-' * 5:<7} {'-' * 26:<28} {'-' * 8:<10} {'-' * 8:<10}  "
        f"{'-' * 30}"
    )
    for r in summary.results:
        dims = ", ".join(
            f"{k}={v:.2f}" for k, v in sorted(r.dimensions.items())
        ) or "—"
        eval_status = r.eval_status or "(skipped)"
        print(
            f"  {r.kind:<7} {r.model:<28} {r.gen_status:<10} "
            f"{eval_status:<10}  {dims}"
        )
        if r.gen_error:
            print(f"      gen error:  {r.gen_error}")
        if r.eval_error:
            print(f"      eval error: {r.eval_error}")
    print()
    if len(summary.results) == 1:
        print(
            "  note: only the primary ran — no shadows for this submission. "
            "Either the routing rule has no eval_shadow_models configured, "
            "or this client doesn't have shadows enabled on code_generation."
        )
        print()


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    try:
        summary = run_spec(
            args.spec, poll_timeout_s=args.poll_timeout_s,
        )
    except ConductError as e:
        print(f"conduct error: {e}", file=sys.stderr)
        return 2
    except FileNotFoundError as e:
        print(f"not found: {e}", file=sys.stderr)
        return 2
    _print_summary(summary)
    # Exit 0 unless the primary itself failed at gen — partial runs (primary
    # ok, some shadows failed) are still useful bench data.
    primary = summary.results[0] if summary.results else None
    if primary is None or primary.gen_status not in {"complete"}:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
