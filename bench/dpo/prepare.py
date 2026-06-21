"""Convert a Conduct preference export into mlx-lm's DPO training format.

Reads ``bench/dpo/datasets/<version>/pairs.jsonl`` (Conduct's NDJSON shape:
``{prompt, system, chosen, rejected, meta}``) and writes the two files
``mlx_lm.lora --train-type dpo`` expects under the same version dir::

    train.jsonl   # 90% of pairs (default)
    valid.jsonl   # 10% of pairs (default)

Each output row is ``{"prompt": <fully-templated user turn>, "chosen": <reply>,
"rejected": <reply>}``. The prompt has the Gemma chat template applied through
the model's start-of-turn marker so mlx-lm appends ``chosen``/``rejected`` to
exactly the right boundary.

Split is deterministic (hash-based) so re-running on the same input produces
the same split — important for being able to compare two runs that differ only
in training hyperparameters.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

DEFAULT_DATASET_ROOT = Path("bench/dpo/datasets")
DEFAULT_VALID_FRACTION = 0.10


class PrepareError(RuntimeError):
    pass


# Gemma 3/4 chat template. Matches the format both google/gemma-*-it tokenizers
# and Ollama's default template use. We hand-render here rather than calling
# tokenizer.apply_chat_template() so this stage has no torch/transformers dep.
#
# Gemma's template:
#   <start_of_turn>user\n{system}\n\n{user}<end_of_turn>\n<start_of_turn>model\n
# (Gemma has no dedicated system role — system content prepends the first user turn.)
_GEMMA_PROMPT_TMPL = (
    "<start_of_turn>user\n"
    "{header}"
    "{user}<end_of_turn>\n"
    "<start_of_turn>model\n"
)


def _render_prompt(system: str, user: str) -> str:
    system = (system or "").strip()
    header = f"{system}\n\n" if system else ""
    return _GEMMA_PROMPT_TMPL.format(header=header, user=user)


def _split_bucket(seed: str, valid_fraction: float) -> str:
    """Deterministic train/valid bucket from a row-identity seed.

    Hash → uniform [0,1) → bucket. Same seed always lands in the same bucket
    regardless of row order or run count.
    """
    h = hashlib.sha256(seed.encode("utf-8")).digest()
    # Take first 8 bytes as a uint64, normalize to [0, 1).
    uniform = int.from_bytes(h[:8], "big") / (1 << 64)
    return "valid" if uniform < valid_fraction else "train"


def _row_seed(row: dict[str, Any]) -> str:
    """Stable per-row identifier for the split decision.

    Prefer Conduct's provenance ids (chosen_id + rejected_id from meta) so
    even if the prompt text gets edited, the same comparison stays in the same
    bucket. Fall back to the prompt+chosen+rejected text content for older
    exports that predate those meta keys.
    """
    meta = row.get("meta") or {}
    chosen_id = meta.get("chosen_id")
    rejected_id = meta.get("rejected_id")
    if chosen_id and rejected_id:
        return f"{chosen_id}|{rejected_id}"
    return hashlib.sha256(
        (row.get("prompt", "") + "|" + row.get("chosen", "") + "|" + row.get("rejected", ""))
        .encode("utf-8")
    ).hexdigest()


def _convert_row(row: dict[str, Any]) -> dict[str, str]:
    user = row.get("prompt")
    chosen = row.get("chosen")
    rejected = row.get("rejected")
    if not isinstance(user, str) or not isinstance(chosen, str) or not isinstance(rejected, str):
        raise PrepareError(
            f"row missing required prompt/chosen/rejected: keys={list(row.keys())}"
        )
    return {
        "prompt": _render_prompt(row.get("system") or "", user),
        "chosen": chosen,
        "rejected": rejected,
    }


def prepare(
    version_dir: Path,
    *,
    valid_fraction: float = DEFAULT_VALID_FRACTION,
) -> dict[str, int]:
    """Read pairs.jsonl, write train.jsonl + valid.jsonl, return counts."""
    if not version_dir.is_dir():
        raise PrepareError(f"{version_dir} is not a directory")
    src = version_dir / "pairs.jsonl"
    if not src.is_file():
        raise PrepareError(f"{src} not found — run `bench.dpo.export` first")
    if not 0.0 < valid_fraction < 1.0:
        raise PrepareError(f"valid_fraction must be in (0, 1), got {valid_fraction}")

    counts = {"train": 0, "valid": 0, "skipped": 0}
    train_path = version_dir / "train.jsonl"
    valid_path = version_dir / "valid.jsonl"
    with (
        src.open("r", encoding="utf-8") as in_f,
        train_path.open("w", encoding="utf-8") as train_f,
        valid_path.open("w", encoding="utf-8") as valid_f,
    ):
        for line in in_f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            try:
                converted = _convert_row(row)
            except PrepareError:
                counts["skipped"] += 1
                continue
            bucket = _split_bucket(_row_seed(row), valid_fraction)
            target = valid_f if bucket == "valid" else train_f
            target.write(json.dumps(converted, separators=(",", ":")))
            target.write("\n")
            counts[bucket] += 1

    if counts["train"] == 0:
        raise PrepareError(
            "no training rows after split — dataset too small for valid_fraction "
            f"{valid_fraction}, or every row was skipped as malformed"
        )
    return counts


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="bench.dpo.prepare")
    p.add_argument("--version", required=True,
                   help="Version slug (directory name under bench/dpo/datasets/).")
    p.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT,
                   help=f"Dataset root (default: {DEFAULT_DATASET_ROOT}).")
    p.add_argument("--valid-fraction", type=float, default=DEFAULT_VALID_FRACTION,
                   help=f"Fraction held out for validation (default: {DEFAULT_VALID_FRACTION}).")
    args = p.parse_args(argv)
    try:
        counts = prepare(
            args.dataset_root / args.version,
            valid_fraction=args.valid_fraction,
        )
    except PrepareError as e:
        print(f"prepare failed: {e}", file=sys.stderr)
        return 2
    print(f"prepared {args.dataset_root / args.version}:")
    print(f"  train: {counts['train']}")
    print(f"  valid: {counts['valid']}")
    if counts["skipped"]:
        print(f"  skipped (malformed): {counts['skipped']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
