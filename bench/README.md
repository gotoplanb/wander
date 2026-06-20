# bench/ — code-generation eval flywheel

Client-side orchestration for [gotoplanb/wander#1](https://github.com/gotoplanb/wander/issues/1). Companion to the [Conduct primitives epic](https://github.com/gotoplanb/conduct/issues/22).

Wander is the **client harness**; Conduct supplies the primitives (`code_generation` and `code_eval` task types, sandboxed evaluator, artifact storage, dataset export). The bench drives the loop:

> generate (fan out the fleet) → build + eval (via Conduct) → collect → report → extract preferences → fine-tune → register → re-run → measure lift.

## Layout

| Path | Issue | Status |
|---|---|---|
| `specs/` | [#3](https://github.com/gotoplanb/wander/issues/3) | shipped — 20 algorithm specs, schema-versioned |
| `goldens/` | [#4](https://github.com/gotoplanb/wander/issues/4) | shipped — 118 Rust tests, cargo-validated |
| `runner/` | [#2](https://github.com/gotoplanb/wander/issues/2) | shipped — `python -m bench.runner --spec <id>` |
| `runs/runs.db` | — | gitignored; SQLite store of runs/gen_jobs/eval_jobs/dimensions |
| `properties/` | [#5](https://github.com/gotoplanb/wander/issues/5) | pending — proptest property layer |
| `reports/` | [#6](https://github.com/gotoplanb/wander/issues/6), [#8](https://github.com/gotoplanb/wander/issues/8) | pending — committed bench artifacts |

Shared scaffolding (HTTP client to Conduct, mechanical scorers, judge rubric helpers) lives in `harness/`.

## Running

Set up env once:

```sh
cp .env.example .env  # then fill in CONDUCT_BASE_URL + CONDUCT_TOKEN
```

Then run one spec across the fleet:

```sh
python -m bench.runner --spec bubble_sort
```

By default the fleet is "every local Ollama model Conduct reports as `resident`" — i.e. anything the worker can call without paying a model-swap cost. Override with repeated `--model` flags:

```sh
python -m bench.runner --spec bubble_sort \
  --model gemma4:e4b --model qwen3.5:4b --model claude-sonnet-4-6
```

Results land in `bench/runs/runs.db` (a single SQLite file with `runs`, `gen_jobs`, `eval_jobs`, `dimensions` tables) plus a per-model summary printed to stdout.

## The contract with Conduct

The runner uses exactly two Conduct task types:

- **`code_generation`** ([conduct#23](https://github.com/gotoplanb/conduct/issues/23)). The runner submits one job per (spec, model) with `inputs={"artifact": "cargo"}` so the worker stores the generated function as a Cargo tarball. The artifact URL lands at `metadata.artifact.url`.
- **`code_eval`** ([conduct#25](https://github.com/gotoplanb/conduct/issues/25), [conduct#26](https://github.com/gotoplanb/conduct/issues/26)). For each completed gen, the runner submits one evaluator job with:

  ```python
  inputs = {
    "target_job_id": "<gen-job-id>",
    "commands":      ["check", "build", "test"],
    "suites":        [{"dimension": "golden",
                       "files":     {"tests/golden.rs": "<golden source>"}}],
    "apply_to_target": True,
  }
  ```

  Conduct ships the artifact + overlay files to the sandbox, runs the commands, parses pass rates into 1-5 dimensions, and (since `apply_to_target=True`) writes them back to the gen job's `quality_scores` under `via="code-eval"`. The verdict comes back on `job.response` (JSON) and `job.metadata.code_eval` (dict).

Dimensions delivered today: `compile`, `golden`. `property` joins once [#5](https://github.com/gotoplanb/wander/issues/5) lands and the proptest suites exist. The composite fold ([conduct#30](https://github.com/gotoplanb/conduct/issues/30)) is computed read-time by `/eval/compare` — the bench reads it from there, not from the runner.

## Why harness-driven fan-out (not Conduct's eval-shadows)

Conduct can fan out to several models on a single job via the `fanout` + `force_shadows` knobs on `POST /jobs`. The bench deliberately doesn't use them:

- The runner needs to submit one *artifact-producing* job per model so each gets its own tarball and its own `code_eval` follow-up. Shadows in Conduct don't get artifacts stored separately — only the primary does.
- Fleet changes shouldn't require operator routing-rule edits. Adding `--model qwen3.5:7b` to a run should work without any Conduct admin call.

Conduct's shadow path remains the right tool for "same prompt, two models, real-time human eval"; the bench just isn't that workload.
