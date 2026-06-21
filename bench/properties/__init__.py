"""Harness-authored proptest property suites for the algorithm spec corpus.

Issue #5. For each invariant-bearing spec in `bench/specs/`, a corresponding
`.rs` file in this directory contains a proptest-style property test the
Conduct `code_eval` sandbox (gotoplanb/conduct#26) runs against the model's
generated function. Property failures are scored on the same 1-5 lane as
golden, but on a separate dimension (`property`), and the minimized
counterexample is captured in the verdict.

Convention
----------
- One file per spec that has a useful invariant; not every spec has one
  (e.g. `factorial`, `fibonacci_nth` — recursive defs that proptest can't
  usefully assert beyond the example-based golden).
- Filename is `<spec_id>.rs`. Filename stem must match a spec id.
- Each file is a Cargo integration test: top-level `use proptest::prelude::*;`
  + `use model_solution::<fn>;` + `proptest! { ... }`.
- Sandbox overlays the file at `tests/<spec_id>_prop.rs` and runs
  `cargo test --test <spec_id>_prop`. The harness also overlays a
  Cargo.toml that pins the proptest dev-dep — see
  ``CARGO_TOML_WITH_PROPTEST``.

Why proptest, not handwritten randomized loops
----------------------------------------------
- Shrinks failing inputs to minimal counterexamples — that's what conduct#26
  captures and surfaces in the verdict. A handwritten loop can detect a
  failure but can't tell you the smallest input that triggers it.
- The proptest crate is in the standard ecosystem, no friction in the
  Cargo-based sandbox.

Why this layer at all (vs. just more goldens)
---------------------------------------------
- Example-based goldens catch obvious wrong cases but miss "compiles + my
  hand-picked tests pass + still subtly wrong" — e.g. a sort that drops
  duplicates, a `bfs` that returns *some* path but not the *shortest*.
  Property tests close that gap by sampling the input space.
- Per the v1 bench: every model that passed all goldens on `bubble_sort`
  also implemented bubble sort correctly. But for `quicksort`, the bench
  has no way to distinguish a real quicksort from a `sort_unstable`
  wrapper. Properties don't fix that on their own either, but combined
  with conduct's mutation testing (#28) they get closer.

Usage
-----
    from bench.properties import load_property, list_properties

    rs = load_property("bubble_sort")
    # → str containing the full .rs file

    all_props = list_properties()
    # → {spec_id: rs_source} for every property suite

The Cargo.toml overlay that pins proptest is exposed as
``CARGO_TOML_WITH_PROPTEST`` so callers can include it in the same
suite payload.
"""

from __future__ import annotations

from pathlib import Path

from bench.specs import CODE_GENERATION_CRATE_NAME

PROPERTIES_DIR = Path(__file__).parent


CARGO_TOML_WITH_PROPTEST = f"""\
[package]
name = "{CODE_GENERATION_CRATE_NAME}"
version = "0.1.0"
edition = "2021"

[lib]
path = "src/lib.rs"

[dev-dependencies]
proptest = "1"
"""


def load_property(spec_id: str) -> str:
    """Return the raw Rust source of the property suite for `spec_id`."""
    path = PROPERTIES_DIR / f"{spec_id}.rs"
    if not path.exists():
        raise FileNotFoundError(f"no property suite at {path}")
    source = path.read_text()
    _validate(source, path)
    return source


def list_properties() -> dict[str, str]:
    """Return {spec_id: rs_source} for every property suite in the corpus."""
    out: dict[str, str] = {}
    for path in sorted(PROPERTIES_DIR.glob("*.rs")):
        source = path.read_text()
        _validate(source, path)
        out[path.stem] = source
    return out


def has_property(spec_id: str) -> bool:
    """Whether a property suite exists for `spec_id`. Cheap; no read."""
    return (PROPERTIES_DIR / f"{spec_id}.rs").exists()


def _validate(source: str, path: Path) -> None:
    """Cheap structural checks. Real validation is the sandbox compile."""
    if "use proptest::prelude" not in source:
        raise ValueError(
            f"{path.name}: expected `use proptest::prelude::*;` — proptest "
            f"is the property-test crate the Conduct sandbox supports"
        )
    if f"use {CODE_GENERATION_CRATE_NAME}::" not in source:
        raise ValueError(
            f"{path.name}: expected `use {CODE_GENERATION_CRATE_NAME}::<fn>;` "
            f"— the model's function is exposed via the pinned crate name"
        )
    if "proptest!" not in source:
        raise ValueError(
            f"{path.name}: expected a `proptest! {{ ... }}` block"
        )
