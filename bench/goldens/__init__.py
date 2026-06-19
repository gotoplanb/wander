"""Harness-authored golden test suites for the algorithm spec corpus.

Issue #4. For each spec in `bench/specs/`, a corresponding `.rs` file in this
directory contains authoritative example-based tests defining correctness.
The harness submits these to Conduct `code_eval` (gotoplanb/conduct#26) to
run against each generated function in the sandbox — the golden pass-rate
per spec per model is the headline dimension of the bench report (#6).

Convention
----------
- One file per spec; filename is `<spec_id>.rs`.
- Each file contains a `#[cfg(test)] mod tests { ... }` block.
- Inside the block: `use super::<function_name>;` and a series of
  `#[test] fn ...` cases.
- Tests are written assuming the model's generated function is exposed at
  the parent module level. The sandbox wraps the model's code at the
  parent module so `super::<function_name>` resolves at compile time.

Why this layout
---------------
- **Provenance separation.** Golden tests are harness-authored, never
  model-authored. Mutation testing (gotoplanb/conduct#28) only catches
  shallow model tests; keeping the two provenance-distinct is the whole
  point of #4.
- **Stable shape.** Same convention across all 20 specs — the harness
  doesn't need per-spec knowledge to wrap and run a suite.
- **No external crates.** Tests use `assert_eq!` / `assert!` only, no
  third-party assertion libraries. Keeps the sandbox build small and
  matches the spec corpus's "stdlib only" rule.

Usage
-----
    from bench.goldens import load_golden, list_goldens

    rs_source = load_golden("reverse_string")
    # → str containing the full .rs file
"""

from __future__ import annotations

from pathlib import Path

GOLDENS_DIR = Path(__file__).parent


def load_golden(spec_id: str) -> str:
    """Return the raw Rust source of the golden suite for `spec_id`."""
    path = GOLDENS_DIR / f"{spec_id}.rs"
    if not path.exists():
        raise FileNotFoundError(f"no golden suite at {path}")
    source = path.read_text()
    _validate(source, path)
    return source


def list_goldens() -> dict[str, str]:
    """Return {spec_id: rs_source} for every golden in the corpus."""
    out: dict[str, str] = {}
    for path in sorted(GOLDENS_DIR.glob("*.rs")):
        source = path.read_text()
        _validate(source, path)
        out[path.stem] = source
    return out


def _validate(source: str, path: Path) -> None:
    """Cheap structural checks. Real validation is the sandbox compile."""
    if "#[test]" not in source:
        raise ValueError(f"{path.name}: no #[test] annotations found")
    if "#[cfg(test)]" not in source:
        raise ValueError(f"{path.name}: expected a #[cfg(test)] block")
    if "mod tests" not in source:
        raise ValueError(f"{path.name}: expected a `mod tests` block")
    if "use super::" not in source:
        raise ValueError(
            f"{path.name}: expected `use super::<function_name>;` — the "
            f"sandbox exposes the model's function at the parent module"
        )
