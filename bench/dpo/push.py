"""Ship the fused GGUF + Modelfile to the Ollama host and register the tag.

The Ollama daemon runs on a separate Mac on the local network — never on this
machine. This stage scp's the artifacts over, runs ``ollama create`` remotely
via ssh, and verifies the new tag appears in ``ollama list``.

Once the tag is live on the inference host, hand it to Conduct (conduct#32)
so its routing rule for ``code_generation`` can dispatch to it. That step is
out of scope here — it's a config change on the Conduct side.
"""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_CHECKPOINT_ROOT = Path("bench/dpo/checkpoints")
DEFAULT_REMOTE_DIR = "~/wander-checkpoints"


class PushError(RuntimeError):
    pass


def _resolve_host(explicit: str | None) -> str:
    if explicit:
        return explicit
    env = os.environ.get("OLLAMA_SSH_HOST")
    if env:
        return env
    raise PushError(
        "no SSH host — pass --host or set OLLAMA_SSH_HOST (e.g. dave@ollama-mbp.local)."
    )


def _resolve_remote_dir(explicit: str | None) -> str:
    if explicit:
        return explicit
    return os.environ.get("OLLAMA_REMOTE_DIR", DEFAULT_REMOTE_DIR)


def _require_local_artifacts(checkpoint_dir: Path) -> tuple[Path, Path]:
    gguf = checkpoint_dir / "model.gguf"
    modelfile = checkpoint_dir / "Modelfile"
    if not gguf.is_file():
        raise PushError(f"{gguf} missing — run `bench.dpo.fuse` first")
    if not modelfile.is_file():
        raise PushError(f"{modelfile} missing — run `bench.dpo.fuse` first")
    return gguf, modelfile


def _require_tools() -> None:
    for tool in ("ssh", "scp"):
        if shutil.which(tool) is None:
            raise PushError(f"{tool} not on PATH — required to reach the Ollama host")


def _run(cmd: list[str], label: str) -> str:
    """Run a subprocess, capture combined output, raise on non-zero exit."""
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if proc.returncode != 0:
        raise PushError(
            f"{label} failed (exit {proc.returncode}):\n{proc.stdout}"
        )
    return proc.stdout


def push(
    *,
    version: str,
    tag: str,
    checkpoint_root: Path = DEFAULT_CHECKPOINT_ROOT,
    host: str | None = None,
    remote_dir: str | None = None,
) -> str:
    """Copy artifacts, run ``ollama create`` remotely, verify the tag."""
    _require_tools()
    checkpoint_dir = checkpoint_root / version
    gguf, modelfile = _require_local_artifacts(checkpoint_dir)
    resolved_host = _resolve_host(host)
    resolved_dir = _resolve_remote_dir(remote_dir)
    remote_subdir = f"{resolved_dir}/{version}"

    _run(
        ["ssh", resolved_host, f"mkdir -p {shlex.quote(remote_subdir)}"],
        "ssh mkdir",
    )
    _run(
        ["scp", str(gguf), str(modelfile), f"{resolved_host}:{remote_subdir}/"],
        "scp artifacts",
    )

    # `ollama create` reads Modelfile relative to its working directory, so cd
    # into the remote dir before invoking it. Quote the tag because it may
    # contain ':' which is harmless but worth being explicit about.
    create_cmd = (
        f"cd {shlex.quote(remote_subdir)} && "
        f"ollama create {shlex.quote(tag)} -f Modelfile"
    )
    _run(["ssh", resolved_host, create_cmd], "ollama create")

    listing = _run(["ssh", resolved_host, "ollama list"], "ollama list")
    if tag not in listing:
        raise PushError(
            f"tag '{tag}' not visible in remote `ollama list` output:\n{listing}"
        )
    return listing


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="bench.dpo.push")
    p.add_argument("--version", required=True)
    p.add_argument("--tag", required=True,
                   help="Ollama tag to register (e.g. gemma4:e4b-wander-dpo-<version>).")
    p.add_argument("--checkpoint-root", type=Path, default=DEFAULT_CHECKPOINT_ROOT)
    p.add_argument("--host", default=None,
                   help="SSH target for the Ollama host (defaults to $OLLAMA_SSH_HOST).")
    p.add_argument("--remote-dir", default=None,
                   help="Remote directory for the GGUF + Modelfile "
                        f"(defaults to $OLLAMA_REMOTE_DIR or {DEFAULT_REMOTE_DIR}).")
    args = p.parse_args(argv)
    try:
        listing = push(
            version=args.version,
            tag=args.tag,
            checkpoint_root=args.checkpoint_root,
            host=args.host,
            remote_dir=args.remote_dir,
        )
    except PushError as e:
        print(f"push failed: {e}", file=sys.stderr)
        return 2
    print(f"tag '{args.tag}' registered on host. ollama list:\n{listing}")
    print(
        "\nNext: open a Conduct routing-config issue (conduct#32 path) asking "
        f"for '{args.tag}' to be added to the code_generation rule."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
