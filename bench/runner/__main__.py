"""CLI entrypoint: `python -m bench.runner --spec <id> [--model M ...]`.

Prints a per-model summary at the end so a single command tells you which
models compiled, which passed the golden suite, and at what score. The
SQLite store at bench/runs/runs.db keeps the persistent record.
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
            "Fan out one spec to a fleet of models via Conduct's "
            "code_generation + code_eval primitives, persist results to "
            "bench/runs/runs.db, and print a summary."
        ),
    )
    p.add_argument(
        "--spec", required=True,
        help="Spec id (filename stem under bench/specs/*.toml), e.g. bubble_sort",
    )
    p.add_argument(
        "--model", action="append", default=None,
        help=(
            "Model to include in the fleet. Repeatable. Default: every local "
            "Ollama model Conduct reports as `resident`."
        ),
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
    header = f"  {'model':<28} {'gen':<10} {'eval':<10}  dimensions"
    print(header)
    print(f"  {'-' * 26:<28} {'-' * 8:<10} {'-' * 8:<10}  {'-' * 30}")
    for r in summary.results:
        dims = ", ".join(
            f"{k}={v:.2f}" for k, v in sorted(r.dimensions.items())
        ) or "—"
        eval_status = r.eval_status or "(skipped)"
        print(
            f"  {r.model:<28} {r.gen_status:<10} {eval_status:<10}  {dims}"
        )
        if r.gen_error:
            print(f"      gen error:  {r.gen_error}")
        if r.eval_error:
            print(f"      eval error: {r.eval_error}")
    print()


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    try:
        summary = run_spec(
            args.spec, models=args.model, poll_timeout_s=args.poll_timeout_s,
        )
    except ConductError as e:
        print(f"conduct error: {e}", file=sys.stderr)
        return 2
    except FileNotFoundError as e:
        print(f"not found: {e}", file=sys.stderr)
        return 2
    _print_summary(summary)
    # Exit 0 unless every model failed outright at the gen stage — partial
    # runs (some models pass, some fail) are still useful bench data.
    if all(r.gen_status in {"submit_failed", "poll_failed"} for r in summary.results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
