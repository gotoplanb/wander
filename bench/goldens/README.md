# bench/goldens/ — harness-authored golden test suites

Issue [#4](https://github.com/gotoplanb/wander/issues/4). One Rust test file per spec in `bench/specs/`. Authored by the harness, never by the model — separation of provenance is what makes mutation testing ([conduct#28](https://github.com/gotoplanb/conduct/issues/28)) downstream meaningful.

## Convention

- One file per spec: `bench/goldens/<spec_id>.rs`
- Each file is a `#[cfg(test)] mod tests { ... }` block
- Inside: `use super::<function_name>;` + a series of `#[test] fn ...` cases
- Standard library only — `assert_eq!` / `assert!` only, no third-party assertion crates

## Sandbox contract

These files are submitted to Conduct `code_eval` ([conduct#26](https://github.com/gotoplanb/conduct/issues/26)) when that lands. The sandbox wraps the model's generated function at the parent module so `use super::<function_name>;` resolves at compile time. Pass rate per spec per model is the golden dimension of the bench report ([#6](https://github.com/gotoplanb/wander/issues/6)).

Until [conduct#26](https://github.com/gotoplanb/conduct/issues/26) lands, these files are static reference suites — readable, reviewable, ready to ship the moment the executor is there.

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
