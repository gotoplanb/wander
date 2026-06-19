"""Code-generation eval flywheel — bench harness.

The bench fans `code_generation` jobs across the Conduct model fleet, submits
`code_eval` per result (chaining by target_job_id, the same way the media
pipeline chains), collects structured verdicts, and produces reproducible
bench reports + lift measurements.

Conduct owns the primitives (task types, sandboxed evaluator, artifact
storage, scoring dimensions, dataset export). This package is the
orchestration on top.

Planned layout (per gotoplanb/wander#1):
    specs/         — algorithm spec corpus (gotoplanb/wander#3)
    goldens/       — harness-authored test suites (gotoplanb/wander#4)
    properties/    — proptest properties (gotoplanb/wander#5)
    reports/       — committed bench artifacts (gotoplanb/wander#6, #8)
    orchestrator.py  — the loop (gotoplanb/wander#2)

Shared scaffolding lives in `harness/`.
"""
