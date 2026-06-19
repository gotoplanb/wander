# bench/ — code-generation eval flywheel

Client-side orchestration for [gotoplanb/wander#1](https://github.com/gotoplanb/wander/issues/1). Companion to the [Conduct primitives epic](https://github.com/gotoplanb/conduct/issues/22).

Wander is the **client harness**; Conduct supplies the primitives (`code_generation` and `code_eval` task types, sandboxed evaluator, artifact storage, dataset export). The bench drives the loop:

> generate (fan out the fleet) → build + eval (via Conduct) → collect → report → extract preferences → fine-tune → register → re-run → measure lift.

## Layout (planned)

| Path | Issue | Owner |
|---|---|---|
| `specs/` | [#3](https://github.com/gotoplanb/wander/issues/3) | harness — algorithm spec corpus |
| `goldens/` | [#4](https://github.com/gotoplanb/wander/issues/4) | harness — golden test suites |
| `properties/` | [#5](https://github.com/gotoplanb/wander/issues/5) | harness — proptest properties |
| `reports/` | [#6](https://github.com/gotoplanb/wander/issues/6), [#8](https://github.com/gotoplanb/wander/issues/8) | committed bench artifacts |
| `orchestrator.py` | [#2](https://github.com/gotoplanb/wander/issues/2) | the loop itself |

Shared scaffolding (mechanical scorers, judge rubric helpers, Conduct MCP wrapper) lives in `harness/`.

## Currently

Stub package. The first thing to land here is [#2](https://github.com/gotoplanb/wander/issues/2) (bench-harness skeleton), which depends on Conduct landing [#23](https://github.com/gotoplanb/conduct/issues/23), [#25](https://github.com/gotoplanb/conduct/issues/25), and [#26](https://github.com/gotoplanb/conduct/issues/26) first.
