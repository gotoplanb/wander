"""Algorithm spec corpus for the code-generation eval flywheel (issue #3).

Each spec is a TOML file in this directory describing one classic algorithm
the model is asked to implement. Specs are versioned (`schema_version`) and
have stable Rust function signatures so downstream pieces — golden suites
(#4), proptest properties (#5), signature-drift detection (conduct#29) —
can target them deterministically.

Submit a spec as a code_generation job:

    from bench.specs import load_spec
    spec = load_spec("reverse_string")
    create_job(**spec.code_generation_kwargs())

The system prompt that pins the signature and forbids extra items lives in
`CODE_GENERATION_SYSTEM_PROMPT` and is the same for every spec — the
prompt-per-spec is just the natural-language description of what the
function should do.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Difficulty = Literal["easy", "medium", "hard"]

VALID_DIFFICULTIES: frozenset[str] = frozenset({"easy", "medium", "hard"})
VALID_CATEGORIES: frozenset[str] = frozenset(
    {"string", "sort", "search", "math", "dp", "graph", "basic"}
)
CURRENT_SCHEMA_VERSION = 1

SPECS_DIR = Path(__file__).parent


@dataclass(frozen=True)
class Spec:
    """One algorithm spec.

    The `id` doubles as the TOML filename stem; the `signature` is the
    exact Rust function signature the model must produce; the `prompt` is
    the natural-language description fed as the `prompt` to code_generation.
    """

    id: str
    title: str
    difficulty: Difficulty
    categories: tuple[str, ...]
    signature: str
    prompt: str
    schema_version: int

    @classmethod
    def from_toml(cls, path: Path) -> Spec:
        data = tomllib.loads(path.read_text())
        return _validate_and_build(data, path)

    def code_generation_kwargs(self) -> dict[str, str]:
        """Kwargs ready for `create_job(task_type="code_generation", ...)`."""
        return {
            "task_type": "code_generation",
            "prompt": self.prompt,
            "system_prompt": CODE_GENERATION_SYSTEM_PROMPT,
        }


def _validate_and_build(data: dict, path: Path) -> Spec:
    required = {
        "schema_version",
        "id",
        "title",
        "difficulty",
        "categories",
        "signature",
        "prompt",
    }
    missing = required - data.keys()
    if missing:
        raise ValueError(f"{path.name}: missing required keys: {sorted(missing)}")

    schema_version = data["schema_version"]
    if schema_version != CURRENT_SCHEMA_VERSION:
        raise ValueError(
            f"{path.name}: schema_version is {schema_version}, "
            f"loader expects {CURRENT_SCHEMA_VERSION}"
        )

    spec_id = data["id"]
    if path.stem != spec_id:
        raise ValueError(
            f"{path.name}: filename stem must match id ({spec_id!r})"
        )

    difficulty = data["difficulty"]
    if difficulty not in VALID_DIFFICULTIES:
        raise ValueError(
            f"{path.name}: difficulty {difficulty!r} not in "
            f"{sorted(VALID_DIFFICULTIES)}"
        )

    categories = tuple(data["categories"])
    bad_cats = set(categories) - VALID_CATEGORIES
    if bad_cats:
        raise ValueError(
            f"{path.name}: categories {sorted(bad_cats)} not in "
            f"{sorted(VALID_CATEGORIES)}"
        )

    return Spec(
        id=spec_id,
        title=data["title"],
        difficulty=difficulty,
        categories=categories,
        signature=data["signature"].strip(),
        prompt=data["prompt"].strip(),
        schema_version=schema_version,
    )


def load_spec(spec_id: str) -> Spec:
    """Load one spec by id."""
    path = SPECS_DIR / f"{spec_id}.toml"
    if not path.exists():
        raise FileNotFoundError(f"no spec at {path}")
    return Spec.from_toml(path)


def list_specs() -> list[Spec]:
    """Return every spec in the corpus, sorted by (difficulty, id)."""
    difficulty_order = {"easy": 0, "medium": 1, "hard": 2}
    return sorted(
        (Spec.from_toml(p) for p in SPECS_DIR.glob("*.toml")),
        key=lambda s: (difficulty_order[s.difficulty], s.id),
    )


# Pinned across every spec so the harness-authored golden suites
# (`bench/goldens/*.rs`, issue #4) can import via `use model_solution::<fn>;`
# without per-spec template logic. The Conduct sandbox (gotoplanb/watchtower
# rust-build) overlays the golden at `tests/<name>.rs` and runs `cargo test
# --test <name>`, so the test target is an integration test target whose
# `extern crate` name is whatever Cargo.toml declares — pinning it makes
# all 20 goldens compile against any model's submission uniformly.
CODE_GENERATION_CRATE_NAME = "model_solution"


CODE_GENERATION_SYSTEM_PROMPT = f"""\
You implement a single Rust function from a written specification and \
package it as a minimal Cargo crate.

OUTPUT FORMAT
Return exactly TWO fenced code blocks — and nothing else around them. \
The harness identifies each file by the path token after the language \
in the fence info line:

  ```toml Cargo.toml
  ...the manifest...
  ```

  ```rust src/lib.rs
  ...the function...
  ```

Do not return a JSON manifest. Do not include prose, commentary, or any \
extra files. Two fenced blocks, in that order.

Cargo.toml MUST be exactly:

  [package]
  name = "{CODE_GENERATION_CRATE_NAME}"
  version = "0.1.0"
  edition = "2021"

  [lib]
  path = "src/lib.rs"

src/lib.rs MUST contain ONLY the function from the SIGNATURE in the prompt:
- Match the SIGNATURE exactly — parameter names, types, return type, \
mutability, visibility (`pub`). The harness's golden tests import the \
function as `use {CODE_GENERATION_CRATE_NAME}::<function_name>;` and break \
on any signature drift.
- One single public function. If you need helpers, inline them as nested \
functions or closures inside its body.
- Standard library only. No external crates. No `[dependencies]` section.
- Must compile under stable Rust without warnings.
- No `#[cfg(test)]`, no `mod tests`, no test code — the harness supplies \
those at `tests/<name>.rs` as integration tests.
"""
