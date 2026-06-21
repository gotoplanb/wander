# DPO fine-tune pipeline (wander#7)

Closes the cognitive loop for the `code_generation` flywheel: Conduct
accumulates scored primary + shadow submissions per prompt, this package
exports the resulting preference pairs (via the regular client key —
[conduct#41](https://github.com/gotoplanb/conduct/issues/41)), fine-tunes the
local primary (`gemma4:e4b`) toward higher-scoring outputs, and publishes
the checkpoint to HuggingFace Hub so Conduct's routing rule can reference
it ([conduct#42](https://github.com/gotoplanb/conduct/issues/42)) for the
lift report (wander#8).

## Pipeline

```
Conduct                                Wander                            HuggingFace Hub
───────                                ──────                            ───────────────
/datasets/preferences          ──►   export.py    ──► pairs.jsonl
(client key, own data only)             │
                                        ▼
                                    prepare.py    ──► train.jsonl, valid.jsonl
                                        │
                                        ▼
                                    train.py      ──► adapters.safetensors  (mlx-lm DPO)
                                        │
                                        ▼
                                    fuse.py       ──► model.gguf + Modelfile
                                        │
                                        ▼
                                    push.py       ───────────────────►  gotoplanb/<repo>@<sha>
                                                                                │
       (when conduct#42 lands)                                                  ▼
       Conduct config: huggingface://<repo>@<sha>  ◄──────────  pulls + serves
```

Each stage is one module; each runs `python -m bench.dpo.<stage>`. Stages share
a `<version>` slug — the date-stamped directory under `bench/dpo/datasets/`
produced by `export.py`. Downstream stages take `--version <slug>` to find
their inputs.

## Why this shape

- **Identity-agnostic handoff via HF Hub.** Per [conduct#42](https://github.com/gotoplanb/conduct/issues/42),
  Conduct treats `huggingface://<repo>@<rev>` as just another model source —
  no special "register our checkpoint" handshake, same path it would use for
  a community model. Publishing is the client's job; pulling + serving is
  Conduct's. No SSH, no shared filesystem, no admin tokens.
- **Client-key data export.** Per [conduct#41](https://github.com/gotoplanb/conduct/issues/41),
  Wander pulls its preference pairs with its regular `CONDUCT_TOKEN` —
  scoped to its own jobs, no admin token crosses the service boundary.
- **Same-family preference pairs.** Per [conduct#40](https://github.com/gotoplanb/conduct/issues/40),
  the fleet is Gemma-only — `gemma4:e4b` (chosen-side baseline) vs `gemma4:12b`
  (chosen-side ceiling). DPO learns to push e4b toward 12b-shaped outputs
  without picking up cross-family quirks.
- **mlx-lm, not TRL.** Native Apple Silicon, mature DPO support for Gemma
  since Q3 2025, single-tool path from base weights → LoRA adapter → fused
  safetensors → GGUF for Ollama serving.

## Environment

In addition to the variables `harness/conduct.py` already reads
(`CONDUCT_BASE_URL`, `CONDUCT_TOKEN`):

| variable | used by | meaning |
|---|---|---|
| `WANDER_DPO_BASE_MODEL` | `train.py`, `fuse.py` | HuggingFace repo id of the base model in MLX format (e.g. `mlx-community/gemma-3-4b-it-bf16`). Should match the upstream Gemma `gemma4:e4b` is pinned to in Conduct's routing. |
| `HF_TOKEN` | `push.py` | Write-scoped HuggingFace token. Generate at <https://huggingface.co/settings/tokens>. |
| `WANDER_DPO_HF_REPO` | `push.py` | Target HF model repo (e.g. `gotoplanb/gemma-e4b-wander-dpo`). |
| `LLAMA_CPP_DIR` | `fuse.py` | Path to a local clone of [llama.cpp](https://github.com/ggerganov/llama.cpp), used for the GGUF conversion script. |

## Versioning

`export.py` writes a date-stamped directory under `bench/dpo/datasets/` plus a
`manifest.json` that records the exact Conduct query, the returned row count,
the distinct chosen/rejected models, and a SHA-256 of `pairs.jsonl`. The same
version slug is reused by every downstream stage so checkpoints stay
traceable back to the input data.

If you re-run `export.py` against the same Conduct state, the manifest hash
matches and the export is skipped (idempotent). To force a new version, pass
`--force` or `--version <slug>`.

The `push.py` stage uploads to a per-version subdirectory of the HF repo and
prints the resulting `huggingface://<repo>@<commit-sha>` reference — pin that
exact SHA (not `main`) in Conduct's routing config for reproducible benches.

## End-to-end run

```bash
# 1. Pull preference pairs (client key — own data only).
python -m bench.dpo.export --task-type code_generation

# 2. Apply Gemma chat template + 90/10 split.
python -m bench.dpo.prepare --version <slug>

# 3. Train. ~20–60 min on an M3 Max depending on pair count.
python -m bench.dpo.train --version <slug>

# 4. Fuse adapter into base + convert to GGUF + emit Modelfile.
python -m bench.dpo.fuse --version <slug>

# 5. Publish the checkpoint to HF Hub.
python -m bench.dpo.push --version <slug>

# 6. (Outside this repo, after conduct#42 lands) open a Conduct
#    routing-config issue asking for the printed
#    `huggingface://<repo>@<sha>` reference to be added to the
#    code_generation rule's eval_shadow_models (or preferred_model).

# 7. (wander#8) re-run the bench against the new model for the lift report.
```

## Install

The pipeline deps (`mlx-lm`, `huggingface_hub`) are heavy and only needed on
the training machine. They're under the `dpo` optional-deps group:

```bash
uv pip install -e ".[dpo]"
```

The export stage alone has no extra deps (it only uses `httpx`, already a
core dep).

## Related

- [wander#7](https://github.com/gotoplanb/wander/issues/7) — this issue
- [conduct#31](https://github.com/gotoplanb/conduct/issues/31) — preference-pair extraction (closed)
- [conduct#40](https://github.com/gotoplanb/conduct/issues/40) — Gemma-only shadow fleet (closed)
- [conduct#41](https://github.com/gotoplanb/conduct/issues/41) — client-key data export (closed; shipped)
- [conduct#42](https://github.com/gotoplanb/conduct/issues/42) — HF model reference as routing target (open, deferred until wander#7 produces a checkpoint)
- [conduct/docs/datasets.md](https://github.com/gotoplanb/conduct/blob/main/docs/datasets.md) — export contract
