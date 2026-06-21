# Wander bench report — 2026-06-21

Multi-model evaluation of the [algorithm spec corpus](../../specs/) across the Conduct `code_generation` fleet, scored on the deterministic `compile` and `golden` dimensions from [`code_eval`](https://github.com/gotoplanb/conduct/issues/26).

**20 specs × 3 models = 60 (spec, model) cells.**

## Headline

**`gemma4:e4b` (shadow) leads** on the corpus — compiled 95% of submissions and passed the full golden suite on 90%, with mean golden 4.70.

The routing rule's current primary is `qwen3.5:9b` (compile 60%, golden 5/5 50%, avg golden 2.70) — a candidate to demote in favor of `gemma4:e4b` for this task type.

## Per-model summary

`compile_rate` = fraction of specs the model's submission compiled. `golden_rate` = fraction where all golden tests passed. `avg_golden` = mean golden score (1–5) across all specs, with failed-to-compile counting as 1.

| Model | Kind | Specs | Compile rate | Golden 5/5 rate | Avg golden |
|---|---|---:|---:|---:|---:|
| `gemma4:e4b` | shadow | 20 | 95% | 90% | 4.70 |
| `qwen3.5:9b` | job | 20 | 60% | 50% | 2.70 |
| `llama3.2:3b` | shadow | 20 | 25% | 25% | 1.25 |

## Per-spec breakdown

Each cell shows `golden / 5` if the model compiled, `✗` if it didn't, `—` if no data.

| Spec | `gemma4:e4b` | `llama3.2:3b` | `qwen3.5:9b` |
|---|:---:|:---:|:---:|
| `bfs_shortest_path` | 5/5 | ✗ | ✗ |
| `binary_search_sorted` | 5/5 | ✗ | 5/5 |
| `bubble_sort` | 5/5 | ✗ | 5/5 |
| `count_vowels` | 5/5 | 5/5 | ✗ |
| `dijkstra_shortest_path` | 5/5 | ✗ | ✗ |
| `factorial` | 5/5 | 5/5 | 5/5 |
| `fibonacci_nth` | 5/5 | ✗ | 5/5 |
| `fizzbuzz` | 5/5 | 5/5 | 5/5 |
| `insertion_sort` | 5/5 | ✗ | 2/5 |
| `is_anagram` | 4/5 | ✗ | ✗ |
| `is_palindrome` | 5/5 | ✗ | 5/5 |
| `levenshtein_distance` | 5/5 | 5/5 | ✗ |
| `longest_common_prefix` | 5/5 | ✗ | ✗ |
| `longest_common_subsequence` | 5/5 | ✗ | 5/5 |
| `max_in_slice` | 5/5 | ✗ | ✗ |
| `mergesort` | 5/5 | ✗ | 5/5 |
| `quicksort` | 5/5 | ✗ | ✗ |
| `reverse_string` | 5/5 | ✗ | 5/5 |
| `roman_to_int` | ✗ | ✗ | 2/5 |
| `sum_to_n` | 5/5 | 5/5 | 5/5 |

## Reproduce

```sh
# Run every spec across the Conduct-configured fleet:
python -m bench.runner --all

# Re-render this report from the updated SQLite:
python -m bench.runner.report --out bench/reports/v1/report.md
```

Fleet membership lives in Conduct's `code_generation` routing rule (`preferred_model` + `eval_shadow_models`). To compare a different set of models, change the rule, not the harness.
