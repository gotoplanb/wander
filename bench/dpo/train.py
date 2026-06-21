"""Run a DPO LoRA fine-tune via mlx-lm.

Shells out to ``python -m mlx_lm.lora --train-type dpo``. We don't import
``mlx_lm`` here — the CLI is the supported entry point for DPO training and
keeps the heavy mlx deps out of import time on machines that only want to
run ``export``/``prepare``.

Inputs: a prepared version directory (containing ``train.jsonl`` and
``valid.jsonl`` from ``bench.dpo.prepare``). Output: a versioned checkpoint
directory under ``bench/dpo/checkpoints/`` containing the LoRA adapter,
mlx-lm's adapter config, and a ``train.log`` capturing the run.

Defaults are tuned for a 4B-class base model on an M3 Max with a few hundred
to a few thousand preference pairs. Override anything with flags.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_DATASET_ROOT = Path("bench/dpo/datasets")
DEFAULT_CHECKPOINT_ROOT = Path("bench/dpo/checkpoints")

# Defaults: small-but-effective LoRA on a 4B Gemma. Beta is the DPO
# temperature — 0.1 is the TRL paper's default and a good starting point.
DEFAULTS = {
    "lora_rank": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05,
    "learning_rate": 1e-5,
    "iters": 1000,
    "batch_size": 2,
    "grad_checkpoint": True,
    "dpo_beta": 0.1,
    "seed": 0,
}


class TrainError(RuntimeError):
    pass


def _resolve_base_model(explicit: str | None) -> str:
    if explicit:
        return explicit
    env = os.environ.get("WANDER_DPO_BASE_MODEL")
    if env:
        return env
    raise TrainError(
        "no base model specified — pass --base-model or set WANDER_DPO_BASE_MODEL "
        "(e.g. mlx-community/gemma-3-4b-it-bf16; match Conduct's fleet pin for "
        "gemma4:e4b)."
    )


def _build_command(
    *,
    base_model: str,
    dataset_dir: Path,
    output_dir: Path,
    config: dict[str, object],
) -> list[str]:
    """Compose the mlx_lm.lora invocation.

    Pinned to the documented DPO flag set as of mlx-lm 0.20+. If mlx-lm
    bumps the CLI surface, update both this list and the version pin in
    pyproject.toml's [project.optional-dependencies.dpo].
    """
    cmd = [
        sys.executable, "-m", "mlx_lm.lora",
        "--model", base_model,
        "--train",
        "--train-type", "dpo",
        "--data", str(dataset_dir),
        "--adapter-path", str(output_dir),
        "--lora-rank", str(config["lora_rank"]),
        "--lora-alpha", str(config["lora_alpha"]),
        "--lora-dropout", str(config["lora_dropout"]),
        "--learning-rate", str(config["learning_rate"]),
        "--iters", str(config["iters"]),
        "--batch-size", str(config["batch_size"]),
        "--dpo-beta", str(config["dpo_beta"]),
        "--seed", str(config["seed"]),
    ]
    if config.get("grad_checkpoint"):
        cmd.append("--grad-checkpoint")
    return cmd


def _write_run_manifest(
    output_dir: Path,
    *,
    base_model: str,
    dataset_dir: Path,
    config: dict[str, object],
    command: list[str],
    started_at: str,
    finished_at: str,
    return_code: int,
) -> None:
    dataset_manifest = dataset_dir / "manifest.json"
    dataset_provenance = None
    if dataset_manifest.is_file():
        try:
            dataset_provenance = json.loads(dataset_manifest.read_text())
        except (OSError, json.JSONDecodeError):
            dataset_provenance = None
    manifest = {
        "base_model": base_model,
        "dataset_dir": str(dataset_dir),
        "dataset_provenance": dataset_provenance,
        "config": config,
        "command": command,
        "started_at": started_at,
        "finished_at": finished_at,
        "return_code": return_code,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )


def train(
    *,
    version: str,
    dataset_root: Path = DEFAULT_DATASET_ROOT,
    checkpoint_root: Path = DEFAULT_CHECKPOINT_ROOT,
    base_model: str | None = None,
    overrides: dict[str, object] | None = None,
) -> Path:
    """Run the training subprocess; return the checkpoint dir."""
    if shutil.which(sys.executable) is None:  # paranoia
        raise TrainError("no Python interpreter on PATH for subprocess")
    dataset_dir = dataset_root / version
    train_file = dataset_dir / "train.jsonl"
    valid_file = dataset_dir / "valid.jsonl"
    if not train_file.is_file() or not valid_file.is_file():
        raise TrainError(
            f"{dataset_dir} missing train.jsonl / valid.jsonl — "
            "run `bench.dpo.prepare` first"
        )
    resolved_base = _resolve_base_model(base_model)
    config = {**DEFAULTS, **(overrides or {})}
    output_dir = checkpoint_root / version
    output_dir.mkdir(parents=True, exist_ok=True)
    command = _build_command(
        base_model=resolved_base,
        dataset_dir=dataset_dir,
        output_dir=output_dir,
        config=config,
    )
    log_path = output_dir / "train.log"
    started = datetime.now(UTC).isoformat()
    with log_path.open("w", encoding="utf-8") as log_f:
        log_f.write(f"# command: {' '.join(command)}\n")
        log_f.write(f"# started_at: {started}\n\n")
        log_f.flush()
        rc = subprocess.call(command, stdout=log_f, stderr=subprocess.STDOUT)
    finished = datetime.now(UTC).isoformat()
    _write_run_manifest(
        output_dir,
        base_model=resolved_base,
        dataset_dir=dataset_dir,
        config=config,
        command=command,
        started_at=started,
        finished_at=finished,
        return_code=rc,
    )
    if rc != 0:
        raise TrainError(
            f"mlx_lm.lora exited {rc} — see {log_path} for details"
        )
    return output_dir


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="bench.dpo.train")
    p.add_argument("--version", required=True,
                   help="Version slug (directory name shared by dataset + checkpoint).")
    p.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    p.add_argument("--checkpoint-root", type=Path, default=DEFAULT_CHECKPOINT_ROOT)
    p.add_argument("--base-model", default=None,
                   help="HuggingFace/MLX repo id of the base model (overrides WANDER_DPO_BASE_MODEL).")
    p.add_argument("--lora-rank", type=int, default=DEFAULTS["lora_rank"])
    p.add_argument("--lora-alpha", type=int, default=DEFAULTS["lora_alpha"])
    p.add_argument("--lora-dropout", type=float, default=DEFAULTS["lora_dropout"])
    p.add_argument("--learning-rate", type=float, default=DEFAULTS["learning_rate"])
    p.add_argument("--iters", type=int, default=DEFAULTS["iters"])
    p.add_argument("--batch-size", type=int, default=DEFAULTS["batch_size"])
    p.add_argument("--dpo-beta", type=float, default=DEFAULTS["dpo_beta"])
    p.add_argument("--seed", type=int, default=DEFAULTS["seed"])
    p.add_argument("--no-grad-checkpoint", dest="grad_checkpoint",
                   action="store_false", default=True)
    args = p.parse_args(argv)
    overrides = {
        "lora_rank": args.lora_rank,
        "lora_alpha": args.lora_alpha,
        "lora_dropout": args.lora_dropout,
        "learning_rate": args.learning_rate,
        "iters": args.iters,
        "batch_size": args.batch_size,
        "dpo_beta": args.dpo_beta,
        "seed": args.seed,
        "grad_checkpoint": args.grad_checkpoint,
    }
    try:
        out = train(
            version=args.version,
            dataset_root=args.dataset_root,
            checkpoint_root=args.checkpoint_root,
            base_model=args.base_model,
            overrides=overrides,
        )
    except TrainError as e:
        print(f"train failed: {e}", file=sys.stderr)
        return 2
    print(f"checkpoint: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
