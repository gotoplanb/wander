# bench/goldens/ — harness-authored golden test suites

Issue [#4](https://github.com/gotoplanb/wander/issues/4). One Rust test file per spec in `bench/specs/`. Authored by the harness, never by the model — separation of provenance is what makes mutation testing ([conduct#28](https://github.com/gotoplanb/conduct/issues/28)) downstream meaningful.

## Convention

- One file per spec: `bench/goldens/<spec_id>.rs`
- Each file is a Cargo **integration test**: top-level `#[test] fn ...` cases plus one `use model_solution::<function_name>;` import. No `#[cfg(test)]` wrapper, no `mod tests { ... }` block.
- Standard library only — `assert_eq!` / `assert!` only, no third-party assertion crates.

## Sandbox contract

These files are submitted to Conduct `code_eval` ([conduct#26](https://github.com/gotoplanb/conduct/issues/26)) as suite payloads. The sandbox ([watchtower rust-build](https://github.com/gotoplanb/watchtower/tree/main/services/rust-build)) overlays each golden at `tests/<spec_id>.rs` and runs `cargo test --test <spec_id>`. Because that's a separate test target (its own crate), the model's function is imported via the pinned crate name `model_solution` — set in [`bench/specs/__init__.py`](../specs/__init__.py) as `CODE_GENERATION_CRATE_NAME` and required by the system prompt the model sees. Pass rate per spec per model is the golden dimension of the bench report ([#6](https://github.com/gotoplanb/wander/issues/6)).

## Usage

```python
from bench.goldens import load_golden, list_goldens

rs = load_golden("dijkstra_shortest_path")
# → str containing the full .rs file

all_suites = list_goldens()
# → {spec_id: rs_source} for every golden
```

## Coverage rationale per category

| Category | What every suite covers |
|---|---|
| **string** | empty, single char, basic example, non-trivial case (and Unicode if the spec calls for it) |
| **math** | the boundary values (0, 1), small known values, a non-trivial value from the spec's examples |
| **sort** | empty, single, already-sorted, reverse-sorted, duplicates, negatives, mixed |
| **search** | found at start / middle / end, not-found, single-element, empty |
| **dp** | empty either side, identical inputs, disjoint inputs, the spec's named examples |
| **graph** | start == target, disconnected (None), linear chain, alternative-path case |

5–8 tests per spec; sweet spot for a meaningful pass-rate granularity without overwhelming sandbox time.
