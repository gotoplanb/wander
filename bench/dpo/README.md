# DPO fine-tune pipeline (wander#7)

Closes the cognitive loop for the `code_generation` flywheel: Conduct
accumulates scored primary + shadow submissions per prompt, this package
exports the resulting preference pairs, fine-tunes the local primary
(`gemma4:e4b`) toward higher-scoring outputs, and hands the checkpoint
back to Conduct as a selectable model so the lift report (wander#8)
can re-bench against it.

## Pipeline

```
Conduct                                            Wander                       Ollama host
───────                                            ──────                       ───────────
/datasets/preferences?method=composite  ──► export.py     ──► pairs.jsonl
                                                │
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
                                            push.py       ─────────────────────────────► ollama create
                                                                                          gemma4:e4b-wander-dpo-<version>
                                                                                                    │
                                                                                                    ▼
                                                                              register in Conduct routing (conduct#32)
```

Each stage is one module; each runs `python -m bench.dpo.<stage>`. Stages share a
`<version>` slug — the date-stamped directory under `bench/dpo/datasets/` produced
by `export.py`. Downstream stages take `--version <slug>` to find their inputs.

## Why this shape

- **Conduct's job ends at the export.** Per the README split: Conduct owns
  primitives + data; clients own orchestration + cognition. Training and the
  resulting checkpoint registration are Wander-side.
- **Same-family preference pairs.** Per [conduct#40](https://github.com/gotoplanb/conduct/issues/40),
  the fleet is Gemma-only — `gemma4:e4b` (chosen-side baseline) vs `gemma4:12b`
  (chosen-side ceiling). DPO learns to push e4b toward 12b-shaped outputs without
  picking up cross-family quirks.
- **mlx-lm, not TRL.** Native Apple Silicon, mature DPO support for Gemma since
  Q3 2025, single-tool path from base weights → LoRA adapter → fused safetensors
  → GGUF for Ollama.
- **Inference stays on the Ollama host.** Training is heavy and happens here;
  the resulting GGUF is shipped to the separate Mac that runs the fleet. This
  machine never starts Ollama.

## Environment

In addition to the variables `harness/conduct.py` already reads
(`CONDUCT_BASE_URL`, `CONDUCT_TOKEN`):

| variable | used by | meaning |
|---|---|---|
| `CONDUCT_ADMIN_TOKEN` | `export.py` | `/datasets/preferences` is admin-only (it's a bulk data pull). The client key won't work — mint or read an admin key per `conduct/docs/auth.md`. |
| `WANDER_DPO_BASE_MODEL` | `train.py`, `fuse.py` | HuggingFace repo id of the base model in MLX format (e.g. `mlx-community/gemma-3-4b-it-bf16`). The Ollama tag `gemma4:e4b` maps to whichever upstream Gemma the fleet is currently pinned to — check Conduct's routing config and pick the matching mlx-community conversion. |
| `OLLAMA_SSH_HOST` | `push.py` | SSH target for the Ollama box, e.g. `dave@ollama-mbp.local`. `push.py` uses scp + `ssh … ollama create`. |
| `OLLAMA_REMOTE_DIR` | `push.py` | Directory on the Ollama host where the GGUF + Modelfile land (default `~/wander-checkpoints`). |

## Versioning

`export.py` writes a date-stamped directory under `bench/dpo/datasets/` plus a
`manifest.json` that records the exact Conduct query, the returned row count,
the distinct chosen/rejected models, and a SHA-256 of `pairs.jsonl`. The same
version slug is reused by every downstream stage so checkpoints stay
traceable back to the input data.

If you re-run `export.py` against the same Conduct state, the manifest hash
matches and the export is skipped (idempotent). To force a new version, pass
`--force` or `--version <slug>`.

## End-to-end run

```bash
# 1. Pull preference pairs (admin token; rows include all task_types unless filtered).
python -m bench.dpo.export --task-type code_generation

# 2. Apply Gemma chat template + 90/10 split.
python -m bench.dpo.prepare --version <slug>

# 3. Train. ~20–60 min on an M3 Max depending on pair count.
python -m bench.dpo.train --version <slug>

# 4. Fuse adapter into base + convert to GGUF + emit Modelfile.
python -m bench.dpo.fuse --version <slug>

# 5. Ship to the Ollama host and register the tag locally there.
python -m bench.dpo.push --version <slug> --tag gemma4:e4b-wander-dpo-<slug>

# 6. (Outside this repo) ask Conduct to add the new tag to the
#    code_generation routing rule per conduct#32 — open a routing-config issue
#    with the tag name, host, and provenance pointer (manifest.json path).

# 7. (Wander#8) re-run the bench against the new tag for the lift report.
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
- [conduct#32](https://github.com/gotoplanb/conduct/issues/32) — register checkpoint as a selectable model (closed)
- [conduct#40](https://github.com/gotoplanb/conduct/issues/40) — Gemma-only shadow fleet (in flight)
- [conduct/docs/datasets.md](https://github.com/gotoplanb/conduct/blob/main/docs/datasets.md) — export contract
