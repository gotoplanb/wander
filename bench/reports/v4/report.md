# Wander bench report — 2026-06-21

Multi-model evaluation of the [algorithm spec corpus](../../specs/) across the Conduct `code_generation` fleet, scored on the deterministic `compile` and `golden` dimensions from [`code_eval`](https://github.com/gotoplanb/conduct/issues/26).

**22 specs × 2 models = 44 (spec, model) cells.**

## Headline

**`gemma4:12b` (shadow) leads** on the corpus — compiled 91% of submissions and passed the full golden suite on 82%, with mean golden 4.45.

The routing rule's current primary is `gemma4:e4b` (compile 82%, golden 5/5 82%, avg golden 4.09) — a candidate to demote in favor of `gemma4:12b` for this task type.

## Per-model summary

`compile_rate` = fraction of specs the model's submission compiled. `golden_rate` = fraction where all golden tests passed. `avg_golden` = mean golden score (1–5) across all specs, with failed-to-compile counting as 1. `property_rate` and `avg_property` use the same convention but are restricted to specs where a property suite exists (see `bench/properties/`).

| Model | Kind | Specs | Compile rate | Golden 5/5 | Avg golden | Prop 5/5 | Avg property |
|---|---|---:|---:|---:|---:|---:|---:|
| `gemma4:12b` | shadow | 22 | 91% | 82% | 4.45 | 94% | 4.94 |
| `gemma4:e4b` | job | 22 | 82% | 82% | 4.09 | 94% | 4.75 |

## Per-spec breakdown

Each cell shows `golden/property` (each 1-5, `—` if no suite) when the model compiled, `✗` if it didn't, `—` if no data.

| Spec | `gemma4:12b` | `gemma4:e4b` |
|---|:---:|:---:|
| `bfs_shortest_path` | 5/5 | 5/5 |
| `binary_search_sorted` | 5/5 | 5/5 |
| `bubble_sort` | 5/5 | 5/5 |
| `count_vowels` | 5/5 | 5/5 |
| `dijkstra_shortest_path` | 5/5 | 5/5 |
| `factorial` | 5/— | 5/— |
| `fibonacci_nth` | 5/— | 5/— |
| `fizzbuzz` | 5/— | 5/— |
| `insertion_sort` | 5/5 | 5/5 |
| `is_anagram` | 4/4 | 5/5 |
| `is_palindrome` | 4/5 | 5/5 |
| `kv_store_cli` | 5/5 | ✗ |
| `levenshtein_distance` | 5/5 | 5/5 |
| `longest_common_prefix` | 5/5 | 5/5 |
| `longest_common_subsequence` | 5/5 | 5/5 |
| `markdown_subset` | ✗ | ✗ |
| `max_in_slice` | 5/5 | 5/5 |
| `mergesort` | 5/5 | 5/5 |
| `quicksort` | ✗ | ✗ |
| `reverse_string` | 5/5 | 5/5 |
| `roman_to_int` | 5/— | ✗ |
| `sum_to_n` | 5/5 | 5/5 |

## Reproduce

```sh
# Run every spec across the Conduct-configured fleet:
python -m bench.runner --all

# Re-render this report from the updated SQLite:
python -m bench.runner.report --out bench/reports/v1/report.md
```

Fleet membership lives in Conduct's `code_generation` routing rule (`preferred_model` + `eval_shadow_models`). To compare a different set of models, change the rule, not the harness.
