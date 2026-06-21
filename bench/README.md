# bench/ — code-generation eval flywheel

Client-side orchestration for [gotoplanb/wander#1](https://github.com/gotoplanb/wander/issues/1). Companion to the [Conduct primitives epic](https://github.com/gotoplanb/conduct/issues/22).

Wander is the **client harness**; Conduct supplies the primitives (`code_generation` and `code_eval` task types, sandboxed evaluator, artifact storage, dataset export). The bench drives the loop:

> generate (Conduct fans out via `force_shadows`) → build + eval per target (via Conduct) → collect → report → extract preferences → fine-tune → register → re-run → measure lift.

## Layout

| Path | Issue | Status |
|---|---|---|
| `specs/` | [#3](https://github.com/gotoplanb/wander/issues/3) | shipped — 20 algorithm specs, schema-versioned |
| `goldens/` | [#4](https://github.com/gotoplanb/wander/issues/4) | shipped — 118 Rust integration tests against the pinned `model_solution` crate |
| `properties/` | [#5](https://github.com/gotoplanb/wander/issues/5) | shipped — 16 proptest suites; minimized counterexamples surfaced on failure |
| `runner/` | [#2](https://github.com/gotoplanb/wander/issues/2) | shipped — `python -m bench.runner --spec <id>` or `--all` |
| `runs/runs.db` | — | gitignored; SQLite store of `runs`, `gen_jobs` (primary + shadows), `eval_jobs`, `dimensions` |
| `reports/` | [#6](https://github.com/gotoplanb/wander/issues/6), [#8](https://github.com/gotoplanb/wander/issues/8) | v1 shipped; v2 pending Conduct routing change |

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

That's the whole interface. There is no `--model` flag — clients can't pick models on Conduct, and shouldn't appear to.

The fleet for any given run is whatever Conduct's `code_generation` routing rule says: `preferred_model` runs as the primary, every entry in `eval_shadow_models` runs as a parallel JobShadow with its own Cargo artifact ([conduct#35](https://github.com/gotoplanb/conduct/issues/35)). To change the fleet, change the rule.

Results land in `bench/runs/runs.db` (with `kind` distinguishing the primary `job` from each `shadow`) plus a per-model summary printed to stdout.

## The contract with Conduct

The runner uses exactly two Conduct task types:

- **`code_generation`** ([conduct#23](https://github.com/gotoplanb/conduct/issues/23)). The runner submits **one** job per spec with `inputs={"artifact": "cargo"}` + `force_shadows=true`. The system prompt asks the model for **two path-tagged fenced blocks** (``` ```toml Cargo.toml ``` ``` and ``` ```rust src/lib.rs ``` ```), not a JSON manifest — local fleet models reliably botch the JSON-string-per-file format, while every model in the fleet handles fenced blocks cleanly ([conduct#36](https://github.com/gotoplanb/conduct/issues/36)). The primary stores its artifact at `metadata.artifact.url`; each shadow stores its own at `/output/{shadow.id}.tar` under `shadow_metadata.artifact` ([conduct#35](https://github.com/gotoplanb/conduct/issues/35)). Shadow fan-out is independent of primary success — a flaky primary no longer takes the comparison with it.
- **`code_eval`** ([conduct#25](https://github.com/gotoplanb/conduct/issues/25), [conduct#26](https://github.com/gotoplanb/conduct/issues/26)). For each generated target — primary + every shadow — the runner submits one evaluator job with:

  ```python
  inputs = {
    "target_job_id": "<gen job-or-shadow id>",   # conduct#35: both kinds accepted
    "commands":      ["check", "build", "test"],
    "suites":        [{"dimension": "golden",
                       "files":     {"tests/<spec_id>.rs": "<golden source>"}}],
    "apply_to_target": True,
  }
  ```

  Conduct ships the artifact + overlay files to the sandbox, runs the commands, parses pass rates into 1-5 dimensions, and (since `apply_to_target=True`) writes them back to the target's `quality_scores` under `via="code-eval"`. The verdict comes back on `job.response` (JSON) and `job.metadata.code_eval` (dict).

Dimensions delivered today: `compile`, `golden`, `property` (for the 16 specs with proptest suites). The composite fold ([conduct#30](https://github.com/gotoplanb/conduct/issues/30)) is computed read-time by `/eval/compare` — the bench reads it from there, not from the runner.

When a property suite exists (see [`properties/`](properties/)), the runner attaches a second suite to the same `code_eval` job carrying a Cargo.toml overlay that pins `proptest = "1"` as a dev-dep. Conduct's sandbox fetches proptest, runs `cargo test --test <spec_id>_prop`, and captures the **minimized counterexample** on failure — that lands in the verdict's `suites.property.counterexample` field.

## Why one-job-with-force_shadows (not N independent submissions)

Three reasons the harness drives multi-model bench through Conduct's shadow infrastructure rather than submitting N parallel `code_generation` jobs:

1. **Same-input preference pairs.** `/datasets/preferences?method=composite` only produces clean (chosen, rejected) pairs when both candidates came from the *same submission*. The DPO run in [#7](https://github.com/gotoplanb/wander/issues/7) depends on this — N independent submissions would not yield comparable pairs.
2. **Clients don't pick models on Conduct.** Even the HTTP `model` kwarg on `POST /jobs` only lets the client pick from the rule's allowed set, gated by sensitivity. The MCP create_job tool omits it entirely. Both paths converge on "the rule decides" — and the bench should reflect that, not paper over it with a `--model` flag.
3. **Operational separation of concerns.** "Which models do we compare on this task" is a deployment-config decision (the routing rule), not a per-run client knob. Changing the fleet is one Conduct call, not 20 client invocations.

## Fleet (as of conduct#36)

`code_generation` now routes to a local-only fleet: primary `qwen3.5:9b`, shadows `gemma4:e4b` + `llama3.2:3b`. All free, all run on the host Ollama. To change the fleet, edit the rule in [`conduct/config/seed.routing.yaml`](https://github.com/gotoplanb/conduct/blob/main/config/seed.routing.yaml#L128) — never via a client flag.
