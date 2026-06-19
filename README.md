# wander

**Client-side harness for [Conduct](https://github.com/gotoplanb/conduct).** The same orchestration pattern (fan out → judge → export → fine-tune → measure lift) applied across two domains.

Conduct's stance is *"primitives, clients orchestrate, no lifecycle hooks."* Wander is the client that orchestrates — proving the harness pattern transcends use case by instantiating it for two unrelated workloads.

## Two domains

| Domain | Path | Owns |
|---|---|---|
| **Text-adventure engine** | `app/` + `episodes/` | Episode authoring, MCP playtest server, FastAPI runtime, `wander_eval` + `wander_gen` orchestration |
| **Code-generation flywheel** | `bench/` ([#1](https://github.com/gotoplanb/wander/issues/1)) | Algorithm spec corpus, golden tests, proptest properties, bench report, DPO fine-tune run, lift measurement |

Both submit jobs to Conduct, poll, collect, score, and consume the dataset export. Both have a mechanical scorer for syntactically-decidable dimensions and an LLM-judge rubric override for dimensions that need judgment. The shared scaffolding for both lives in `harness/`.

## Layout

```
wander/
├── app/             — text-adventure runtime (FastAPI + MCP + Ollama)
├── bench/           — code-generation eval flywheel (issue #1)
├── harness/         — shared client patterns (scorers, rubrics, Conduct wrappers)
├── episodes/        — text-adventure SQLite packs (forest-demo, kq1, locked-garden,
│                       quartermaster, salvage-run, road-of-yellow-brick, lost-tail)
└── scripts/         — episode migrations
```

## Status

- **`app/`** — seven published episodes, MCP playtest validated, prompt-engineering findings captured (format-budget thresholds, judge rubric override pattern, panel-vs-pairwise selection). See [issue #20 on conduct](https://github.com/gotoplanb/conduct/issues/20) for the latest observability win.
- **`harness/`** — wander_eval mechanical format scorer + judge rubric override. Pattern is in place; code_eval scorers and rubrics will live here too as `bench/` lands.
- **`bench/`** — stub. Epic [#1](https://github.com/gotoplanb/wander/issues/1), partner [Conduct epic](https://github.com/gotoplanb/conduct/issues/22). Critical-path issues: [#2](https://github.com/gotoplanb/wander/issues/2) → [#3](https://github.com/gotoplanb/wander/issues/3)–[#6](https://github.com/gotoplanb/wander/issues/6) → [#7](https://github.com/gotoplanb/wander/issues/7)–[#8](https://github.com/gotoplanb/wander/issues/8).

## Running the text-adventure side

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8765
# or, for the MCP playtest path:
.venv/bin/wanderer-mcp
```

## Why both in one repo

The architectural claim is that the harness pattern is domain-agnostic. One repo where you can grep `harness/scoring.py` and see it instantiated for both `wander_eval` and (eventually) `code_eval` is a stronger demonstration than two repos with a shared library between them. Phase 5 of [#1](https://github.com/gotoplanb/wander/issues/1) is the explicit bridge — terminal games with scripted-play eval ties the two domains together where deterministic correctness runs out and judgment comes back in.
