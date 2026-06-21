# bench/properties/ — harness-authored proptest property suites

Issue [#5](https://github.com/gotoplanb/wander/issues/5). For each invariant-bearing spec in `bench/specs/`, a corresponding `.rs` file in this directory contains a [proptest](https://github.com/proptest-rs/proptest)-style property test the Conduct `code_eval` sandbox ([conduct#26](https://github.com/gotoplanb/conduct/issues/26)) runs against the model's generated function. Property failures land on a separate dimension from the example-based goldens, and the **minimized counterexample** is captured in the verdict.

## Convention

- One file per spec that has a useful invariant. **Not every spec qualifies** — e.g. `factorial`/`fibonacci_nth` (pure recursive defs with no extra invariant), `fizzbuzz` (pattern is the spec), `roman_to_int` (no inverse function to round-trip against).
- Filename: `<spec_id>.rs`. Stem must match a spec id.
- Each file imports `proptest::prelude::*` and `model_solution::<fn>`, then a `proptest! { ... }` block with one or more property tests.
- Tests use `prop_assert!` / `prop_assert_eq!` so proptest can shrink failing inputs to minimal counterexamples.

## Sandbox contract

Each suite is submitted to Conduct `code_eval` with `dimension: "property"` and `property: true`. Two overlay files per submission:

- `Cargo.toml` — the standard `model_solution` crate manifest plus `[dev-dependencies] proptest = "1"` (exposed as `CARGO_TOML_WITH_PROPTEST` from `bench.properties`).
- `tests/<spec_id>_prop.rs` — the suite source.

Conduct's sandbox writes these into the workdir, runs `cargo test --test <spec_id>_prop`, parses the pass-rate into a 1-5 dimension, and on failure scrapes the `minimal failing input: ...` line proptest emits. Both pass-rate and counterexample come back in the verdict — see [conduct#26](https://github.com/gotoplanb/conduct/issues/26) closing comment.

## Coverage

16 of 20 specs have property suites today:

| Spec | Invariants asserted |
|---|---|
| `bubble_sort` / `insertion_sort` / `mergesort` / `quicksort` | output is a sorted permutation of input |
| `binary_search_sorted` | found index resolves to target; not-found means absent; inserted element findable |
| `max_in_slice` | None iff empty; result is in slice and ≥ all elements |
| `sum_to_n` | matches closed-form `n*(n+1)/2` |
| `count_vowels` | matches manual ASCII-vowel count; bounded by string length |
| `reverse_string` | involution (`reverse(reverse(s)) == s`); char count preserved |
| `is_palindrome` | invariant under filtered reverse; `s + reverse(s)` is a palindrome |
| `is_anagram` | symmetric; reflexive; case-folding preserves anagram-ness |
| `longest_common_prefix` | result is a prefix of every element; empty element → empty result; single → self |
| `longest_common_subsequence` | symmetric; `lcs(s,s) == s.chars().count()`; bounded by min length; either-empty → 0 |
| `levenshtein_distance` | symmetric; `lev(s,s) == 0`; empty-vs-s costs char count; bounded by max length |
| `bfs_shortest_path` | reflexive (`bfs(g,v,v) == Some(0)`); reachable distance < |V| |
| `dijkstra_shortest_path` | reflexive; distance bounded by sum of all edge weights |

The four with no property suite (`factorial`, `fibonacci_nth`, `fizzbuzz`, `roman_to_int`) have no useful invariant beyond what the example-based goldens already assert.

## Why this layer

Example-based goldens catch the obviously-wrong cases but miss "compiles + my hand-picked tests pass + still subtly wrong" — a `mergesort` that drops duplicates, a `quicksort` that's actually a `sort_unstable` wrapper, a `reverse_string` that's a byte-reverse instead of a char-reverse. Properties sample the input space and tell you which inputs break the invariant. Combined with conduct's mutation-testing layer ([conduct#28](https://github.com/gotoplanb/conduct/issues/28)) they get closer to "the model actually understood the spec."

## Usage

```python
from bench.properties import (
    CARGO_TOML_WITH_PROPTEST, has_property, load_property, list_properties,
)

rs = load_property("bubble_sort")    # raw .rs source
all_props = list_properties()        # {spec_id: rs_source}
has_property("factorial")            # False — no invariant suite
```

The bench runner ([`bench/runner/orchestrator.py`](../runner/orchestrator.py)) automatically includes the property suite in each `code_eval` submission when one exists.
