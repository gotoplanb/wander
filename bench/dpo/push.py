"""Publish the fused checkpoint to HuggingFace Hub.

Per [conduct#42](https://github.com/gotoplanb/conduct/issues/42) Conduct treats
``huggingface://<repo>@<rev>`` as an identity-agnostic model source — same
path it would use for any community model. The handoff is one-directional and
involves no cross-host state:

    Wander (here):    fuse → GGUF + Modelfile + manifest → upload to HF Hub
    Conduct (later):  routing rule references huggingface://<repo>@<rev>
                      → pulls + serves through its own dispatch path

Publishing is **always** the client's responsibility — Conduct never reaches
back into Wander, never SSHes anywhere, never trusts SCPed artifacts. This
script's only job is to put the artifacts on HF Hub and emit the
``huggingface://<repo>@<commit>`` reference to hand to Conduct's routing
config when conduct#42 lands.

Auth: ``HF_TOKEN`` (write-scoped) for the Hub upload. Target repo is
``--repo`` or ``$WANDER_DPO_HF_REPO`` (e.g. ``gotoplanb/gemma-e4b-wander-dpo``).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

DEFAULT_CHECKPOINT_ROOT = Path("bench/dpo/checkpoints")


class PushError(RuntimeError):
    pass


def _resolve_repo(explicit: str | None) -> str:
    if explicit:
        return explicit
    env = os.environ.get("WANDER_DPO_HF_REPO")
    if env:
        return env
    raise PushError(
        "no target repo — pass --repo or set WANDER_DPO_HF_REPO "
        "(e.g. gotoplanb/gemma-e4b-wander-dpo)."
    )


def _resolve_token() -> str:
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise PushError(
            "HF_TOKEN not set — generate a write-scoped token at "
            "https://huggingface.co/settings/tokens"
        )
    return token


def _require_artifacts(checkpoint_dir: Path) -> tuple[Path, Path]:
    gguf = checkpoint_dir / "model.gguf"
    modelfile = checkpoint_dir / "Modelfile"
    if not gguf.is_file():
        raise PushError(f"{gguf} missing — run `bench.dpo.fuse` first")
    if not modelfile.is_file():
        raise PushError(f"{modelfile} missing — run `bench.dpo.fuse` first")
    return gguf, modelfile


def _build_model_card(checkpoint_dir: Path, version: str, base_model: str | None) -> str:
    """Generate a minimal model card with provenance back to the training run."""
    manifest_path = checkpoint_dir / "manifest.json"
    manifest = None
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text())
        except (OSError, json.JSONDecodeError):
            manifest = None
    base = base_model or (manifest.get("base_model") if manifest else "unknown")
    dataset_prov = (manifest or {}).get("dataset_provenance") or {}
    dataset_version = dataset_prov.get("version", "unknown")
    dataset_hash = dataset_prov.get("content_hash", "unknown")
    rows = dataset_prov.get("row_count", "unknown")
    chosen_models = dataset_prov.get("chosen_models", {})
    rejected_models = dataset_prov.get("rejected_models", {})
    return f"""---
tags:
- wander
- dpo
- gemma
license: apache-2.0
---

# Wander DPO checkpoint `{version}`

Fine-tuned via mlx-lm DPO from a preference dataset produced by the Wander
code-generation eval flywheel. See
[gotoplanb/wander](https://github.com/gotoplanb/wander) for the harness
and [gotoplanb/conduct](https://github.com/gotoplanb/conduct) for the
data source.

## Provenance

- **Base model:** `{base}`
- **Dataset version:** `{dataset_version}`
- **Dataset content hash:** `{dataset_hash}`
- **Preference pairs:** {rows}
- **Chosen-side models:** {json.dumps(chosen_models)}
- **Rejected-side models:** {json.dumps(rejected_models)}

## Serving via Conduct

Per conduct#42, reference this checkpoint in a routing rule as:

```yaml
huggingface://<repo>@<commit-sha>
```

Pin a specific commit SHA (not `main`) for reproducible bench runs.
"""


def push(
    *,
    version: str,
    checkpoint_root: Path = DEFAULT_CHECKPOINT_ROOT,
    repo: str | None = None,
    base_model: str | None = None,
    private: bool = True,
) -> str:
    """Upload the checkpoint dir to HF Hub. Return the commit SHA."""
    try:
        from huggingface_hub import HfApi  # noqa: PLC0415
    except ImportError as e:
        raise PushError(
            "huggingface_hub not installed — `pip install -e '.[dpo]'`"
        ) from e

    checkpoint_dir = checkpoint_root / version
    if not checkpoint_dir.is_dir():
        raise PushError(f"{checkpoint_dir} not found — run `bench.dpo.fuse` first")
    _require_artifacts(checkpoint_dir)
    resolved_repo = _resolve_repo(repo)
    token = _resolve_token()

    # Build a per-version subdir on the repo so multiple checkpoints can
    # coexist. README at the root + the GGUF + Modelfile under <version>/.
    card_path = checkpoint_dir / "MODEL_CARD.md"
    card_path.write_text(_build_model_card(checkpoint_dir, version, base_model))

    api = HfApi(token=token)
    api.create_repo(
        repo_id=resolved_repo,
        repo_type="model",
        private=private,
        exist_ok=True,
    )
    commit_info = api.upload_folder(
        folder_path=str(checkpoint_dir),
        path_in_repo=version,
        repo_id=resolved_repo,
        repo_type="model",
        # Only ship what Conduct actually needs to serve. Skip the LoRA
        # adapter + fused HF dir (those are reproducible from the manifest).
        allow_patterns=["model.gguf", "Modelfile", "manifest.json", "MODEL_CARD.md"],
        commit_message=f"wander DPO checkpoint {version}",
    )
    return commit_info.oid


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="bench.dpo.push")
    p.add_argument("--version", required=True,
                   help="Version slug (directory name under bench/dpo/checkpoints/).")
    p.add_argument("--checkpoint-root", type=Path, default=DEFAULT_CHECKPOINT_ROOT)
    p.add_argument("--repo", default=None,
                   help="HF model repo (defaults to $WANDER_DPO_HF_REPO).")
    p.add_argument("--base-model", default=None,
                   help="Base model id for the model card (defaults to train manifest).")
    p.add_argument("--public", dest="private", action="store_false", default=True,
                   help="Create the HF repo as public (default: private).")
    args = p.parse_args(argv)
    try:
        commit = push(
            version=args.version,
            checkpoint_root=args.checkpoint_root,
            repo=args.repo,
            base_model=args.base_model,
            private=args.private,
        )
    except PushError as e:
        print(f"push failed: {e}", file=sys.stderr)
        return 2
    repo = args.repo or os.environ.get("WANDER_DPO_HF_REPO", "<repo>")
    reference = f"huggingface://{repo}@{commit}"
    print(f"uploaded to {repo} @ {commit}")
    print(f"reference:  {reference}")
    print(
        "\nNext: when conduct#42 lands, open a Conduct routing-config "
        f"issue asking for `{reference}` to be added to the "
        "code_generation rule's eval_shadow_models (or preferred_model)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
