"""Harness-authored golden test suites for the algorithm spec corpus.

Issue #4. For each spec in `bench/specs/`, a corresponding `.rs` file in this
directory contains authoritative example-based tests defining correctness.
The harness submits these to Conduct `code_eval` (gotoplanb/conduct#26) to
run against each generated function in the sandbox — the golden pass-rate
per spec per model is the headline dimension of the bench report (#6).

Convention
----------
- One file per spec; filename is `<spec_id>.rs`.
- Each file is a **Cargo integration test**: top-level `#[test] fn ...`
  functions plus a single `use model_solution::<function_name>;` import.
  No `#[cfg(test)]` wrapper, no `mod tests { ... }` block.
- The Conduct sandbox (gotoplanb/watchtower rust-build) overlays the file
  at `tests/<spec_id>.rs` and runs `cargo test --test <spec_id>`. The
  test target is a separate crate, so the model's function is imported
  via the pinned crate name (`model_solution`, set in
  `bench/specs/__init__.py::CODE_GENERATION_CRATE_NAME`) — not via
  `use super::`.

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


_PINNED_CRATE = "model_solution"


def _validate(source: str, path: Path) -> None:
    """Cheap structural checks. Real validation is the sandbox compile."""
    if "#[test]" not in source:
        raise ValueError(f"{path.name}: no #[test] annotations found")
    if f"use {_PINNED_CRATE}::" not in source:
        raise ValueError(
            f"{path.name}: expected `use {_PINNED_CRATE}::<function_name>;` — "
            f"the Conduct sandbox runs goldens as Cargo integration tests "
            f"against a crate pinned to {_PINNED_CRATE!r}"
        )
    # Catch the old `mod tests { ... }` shape so a stale file fails loudly
    # rather than silently silently breaking the live sandbox run.
    if "mod tests" in source or "#[cfg(test)]" in source:
        raise ValueError(
            f"{path.name}: goldens are bare integration tests now — no "
            f"`#[cfg(test)] mod tests {{ ... }}` wrapper"
        )
