"""bench/runner — the orchestration loop for #2.

Public surface:

    run_spec(spec_id, models=None) -> RunSummary

Submits one `code_generation` job per model for the given spec, polls each
to completion, then submits one `code_eval` per completed gen carrying the
spec's golden suite + `commands=[check, build, test]` + `apply_to_target=True`.
Per-model dimensions land on the originating gen job (via Conduct's
write-back) and are mirrored into a local SQLite at `bench/runs/runs.db`
for re-aggregation across runs (the basis for #6's report).

Models default to whatever local Ollama models Conduct reports as
`resident` (no swap cost). Pass an explicit list to target cloud models
or specific Ollama tags.
"""

from .orchestrator import RunSummary, run_spec

__all__ = ["RunSummary", "run_spec"]
