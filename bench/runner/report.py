"""Render the SQLite bench results into a markdown report.

For #6: read every run in `runs.db`, group per-model dimensions across
all specs, and emit one markdown document with two tables — an
aggregate per-model ranking and a per-spec breakdown — plus a header
recording how the report was generated.

Usage::

    python -m bench.runner.report                       # to stdout
    python -m bench.runner.report --out bench/reports/v1/report.md

The aggregate table is the headline result: which model is most
reliable on compile + golden across the corpus.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .store import DEFAULT_DB_PATH


@dataclass(frozen=True)
class _Row:
    spec_id: str
    model: str
    kind: str
    compile: float | None
    golden: float | None


def _load_latest_per_spec(db_path: Path) -> list[_Row]:
    """For each (spec, model) pair, keep only the latest run's
    dimensions. Multiple runs of the same spec are useful for noise
    estimation later, but the headline report shows the current
    state of each model on each spec."""
    conn = sqlite3.connect(db_path)
    try:
        # The "latest" run per spec is max(runs.id) — runs are append-only.
        # Within that run, every (kind, model) has at most one gen_jobs row
        # (UNIQUE(run_id, conduct_job_id) is a stricter constraint), and
        # each gen_job has at most one eval_job (UNIQUE(gen_job_id)).
        cur = conn.execute(
            """
            WITH latest_run AS (
              SELECT spec_id, MAX(id) AS run_id
              FROM runs
              GROUP BY spec_id
            )
            SELECT
              r.spec_id, g.model, g.kind,
              MAX(CASE WHEN d.name = 'compile' THEN d.score END) AS compile,
              MAX(CASE WHEN d.name = 'golden'  THEN d.score END) AS golden
            FROM latest_run r
            JOIN gen_jobs g ON g.run_id = r.run_id
            LEFT JOIN eval_jobs e ON e.gen_job_id = g.id
            LEFT JOIN dimensions d ON d.eval_job_id = e.id
            GROUP BY r.spec_id, g.model, g.kind
            ORDER BY r.spec_id, (g.kind = 'shadow'), g.model
            """
        )
        return [_Row(*row) for row in cur.fetchall()]
    finally:
        conn.close()


def _summarize_per_model(rows: list[_Row]) -> list[dict[str, object]]:
    """Per-model aggregates across all specs in the dataset.
    `compile_rate` = fraction of specs where compile == 5.
    `golden_rate` = fraction of specs where compile==5 AND golden==5
    (golden only ran if compile passed; failing to compile counts
    against the model on golden too)."""
    by_model: dict[str, list[_Row]] = {}
    for r in rows:
        by_model.setdefault(r.model, []).append(r)
    out: list[dict[str, object]] = []
    for model, rs in by_model.items():
        n = len(rs)
        compiled = sum(1 for r in rs if (r.compile or 0) >= 5)
        golden_perfect = sum(1 for r in rs if (r.golden or 0) >= 5)
        # Mean golden score over specs that compiled, 0 otherwise.
        scored = [r.golden or 0.0 for r in rs]
        avg_golden = sum(scored) / n if n else 0.0
        out.append({
            "model": model,
            "kind": next(iter({r.kind for r in rs})) if len({r.kind for r in rs}) == 1 else "mixed",
            "specs": n,
            "compile_rate": compiled / n if n else 0.0,
            "golden_perfect_rate": golden_perfect / n if n else 0.0,
            "avg_golden": avg_golden,
        })
    # Headline ranking: compile rate first, then average golden score.
    out.sort(
        key=lambda r: (-(r["compile_rate"] or 0), -(r["avg_golden"] or 0))
    )
    return out


def _format_score(c: float | None, g: float | None) -> str:
    """Per-cell renderer for the per-spec table."""
    if c is None:
        return "—"
    if c < 5:
        return "✗"  # didn't compile
    if g is None:
        return "?"  # compiled but no golden recorded (shouldn't happen)
    return f"{int(g)}/5"


def render(db_path: Path) -> str:
    rows = _load_latest_per_spec(db_path)
    if not rows:
        return "# Bench report\n\n(no runs in store)\n"

    specs = sorted({r.spec_id for r in rows})
    models = sorted({r.model for r in rows})
    by_pair: dict[tuple[str, str], _Row] = {(r.spec_id, r.model): r for r in rows}

    summary = _summarize_per_model(rows)

    when = datetime.now(UTC).strftime("%Y-%m-%d")
    lines: list[str] = []
    lines.append(f"# Wander bench report — {when}")
    lines.append("")
    lines.append(
        f"Multi-model evaluation of the [algorithm spec corpus](../../specs/) "
        f"across the Conduct `code_generation` fleet, scored on the "
        f"deterministic `compile` and `golden` dimensions from "
        f"[`code_eval`](https://github.com/gotoplanb/conduct/issues/26)."
    )
    lines.append("")
    lines.append(
        f"**{len(specs)} specs × {len(models)} models = "
        f"{len(specs) * len(models)} (spec, model) cells.**"
    )
    lines.append("")

    # --- Headline finding ---
    if summary:
        top = summary[0]
        primary = next((s for s in summary if s["kind"] == "job"), None)
        lines.append("## Headline")
        lines.append("")
        lines.append(
            f"**`{top['model']}` ({top['kind']}) leads** on the corpus — "
            f"compiled {top['compile_rate']:.0%} of submissions and passed "
            f"the full golden suite on {top['golden_perfect_rate']:.0%}, "
            f"with mean golden {top['avg_golden']:.2f}."
        )
        if primary and primary["model"] != top["model"]:
            lines.append("")
            lines.append(
                f"The routing rule's current primary is "
                f"`{primary['model']}` "
                f"(compile {primary['compile_rate']:.0%}, "
                f"golden 5/5 {primary['golden_perfect_rate']:.0%}, "
                f"avg golden {primary['avg_golden']:.2f}) — a candidate "
                f"to demote in favor of `{top['model']}` for this task type."
            )
        lines.append("")

    # --- Aggregate ranking ---
    lines.append("## Per-model summary")
    lines.append("")
    lines.append(
        "`compile_rate` = fraction of specs the model's submission compiled. "
        "`golden_rate` = fraction where all golden tests passed. "
        "`avg_golden` = mean golden score (1–5) across all specs, with "
        "failed-to-compile counting as 1."
    )
    lines.append("")
    lines.append(
        "| Model | Kind | Specs | Compile rate | Golden 5/5 rate | Avg golden |"
    )
    lines.append(
        "|---|---|---:|---:|---:|---:|"
    )
    for s in summary:
        lines.append(
            f"| `{s['model']}` | {s['kind']} | {s['specs']} | "
            f"{s['compile_rate']:.0%} | "
            f"{s['golden_perfect_rate']:.0%} | "
            f"{s['avg_golden']:.2f} |"
        )
    lines.append("")

    # --- Per-spec breakdown ---
    lines.append("## Per-spec breakdown")
    lines.append("")
    lines.append(
        "Each cell shows `golden / 5` if the model compiled, "
        "`✗` if it didn't, `—` if no data."
    )
    lines.append("")
    header = "| Spec | " + " | ".join(f"`{m}`" for m in models) + " |"
    align = "|---|" + "|".join(":---:" for _ in models) + "|"
    lines.append(header)
    lines.append(align)
    for spec in specs:
        cells = []
        for m in models:
            pair = by_pair.get((spec, m))
            if pair is None:
                cells.append("—")
            else:
                cells.append(_format_score(pair.compile, pair.golden))
        lines.append(f"| `{spec}` | " + " | ".join(cells) + " |")
    lines.append("")

    # --- Reproduce ---
    lines.append("## Reproduce")
    lines.append("")
    lines.append("```sh")
    lines.append("# Run every spec across the Conduct-configured fleet:")
    lines.append("python -m bench.runner --all")
    lines.append("")
    lines.append("# Re-render this report from the updated SQLite:")
    lines.append(
        "python -m bench.runner.report --out bench/reports/v1/report.md"
    )
    lines.append("```")
    lines.append("")
    lines.append(
        "Fleet membership lives in Conduct's `code_generation` routing rule "
        "(`preferred_model` + `eval_shadow_models`). To compare a different "
        "set of models, change the rule, not the harness."
    )
    lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="bench.runner.report",
        description="Render the bench results SQLite into markdown.",
    )
    p.add_argument(
        "--db", type=Path, default=DEFAULT_DB_PATH,
        help="Path to runs.db (default: bench/runs/runs.db)",
    )
    p.add_argument(
        "--out", type=Path, default=None,
        help="Write to this path instead of stdout.",
    )
    args = p.parse_args(argv)
    if not args.db.exists():
        print(f"no runs.db at {args.db}", file=sys.stderr)
        return 2
    md = render(args.db)
    if args.out is None:
        sys.stdout.write(md)
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(md)
        print(f"wrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
