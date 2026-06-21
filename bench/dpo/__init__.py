"""DPO fine-tune pipeline for gotoplanb/wander#7.

Closes the cognitive loop: Conduct accumulates scored `code_generation`
submissions (primary + shadows) under one prompt, derives `(chosen, rejected)`
preference pairs from the composite code-eval score
([gotoplanb/conduct#31](https://github.com/gotoplanb/conduct/issues/31)),
and this package consumes that export to fine-tune the local `gemma4:e4b`
primary toward higher-scoring outputs. The result is handed back to
Conduct as a selectable model
([gotoplanb/conduct#32](https://github.com/gotoplanb/conduct/issues/32))
so the lift report (gotoplanb/wander#8) can re-bench against it.

Pipeline (one module per stage, each runnable as `python -m bench.dpo.<stage>`)::

    export   → bench/dpo/datasets/<version>/pairs.jsonl   + manifest.json
    prepare  → bench/dpo/datasets/<version>/{train,valid}.jsonl
    train    → bench/dpo/checkpoints/<version>/adapters.safetensors
    fuse     → bench/dpo/checkpoints/<version>/model.gguf + Modelfile
    push     → ollama create <tag> on $OLLAMA_SSH_HOST

Training runs on the M-series box via mlx-lm; inference stays on the
separate Ollama host (per the project's "no Ollama on the dev machine"
rule). The `push` stage is the only one that touches the Ollama box.
See `README.md` for end-to-end run instructions and version conventions.
"""
