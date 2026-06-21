# Wander bench report — 2026-06-21

Multi-model evaluation of the [algorithm spec corpus](../../specs/) across the Conduct `code_generation` fleet, scored on the deterministic `compile` and `golden` dimensions from [`code_eval`](https://github.com/gotoplanb/conduct/issues/26).

**2 specs × 2 models = 4 (spec, model) cells.**

## Headline

**`gemma4:e4b` (job) leads** on the corpus — compiled 0% of submissions and passed the full golden suite on 0%, with mean golden 0.00.

## Per-model summary

`compile_rate` = fraction of specs the model's submission compiled. `golden_rate` = fraction where all golden tests passed. `avg_golden` = mean golden score (1–5) across all specs, with failed-to-compile counting as 1. `property_rate` and `avg_property` use the same convention but are restricted to specs where a property suite exists (see `bench/properties/`).

| Model | Kind | Specs | Compile rate | Golden 5/5 | Avg golden | Prop 5/5 | Avg property |
|---|---|---:|---:|---:|---:|---:|---:|
| `gemma4:e4b` | job | 2 | 0% | 0% | 0.00 | — | — |
| `gemma4:12b` | shadow | 2 | 0% | 0% | 0.00 | — | — |

## Per-spec breakdown

Each cell shows `golden/property` (each 1-5, `—` if no suite) when the model compiled, `✗` if it didn't, `—` if no data.

| Spec | `gemma4:12b` | `gemma4:e4b` |
|---|:---:|:---:|
| `kv_store_cli` | ✗ | ✗ |
| `markdown_subset` | — | ✗ |

## Reproduce

```sh
# Run every spec across the Conduct-configured fleet:
python -m bench.runner --all

# Re-render this report from the updated SQLite:
python -m bench.runner.report --out bench/reports/v1/report.md
```

Fleet membership lives in Conduct's `code_generation` routing rule (`preferred_model` + `eval_shadow_models`). To compare a different set of models, change the rule, not the harness.
