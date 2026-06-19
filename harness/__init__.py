"""Shared client-side patterns for orchestrating Conduct.

This package holds scaffolding that's the same across domains: mechanical
scorers, judge rubric overrides, MCP wrappers, dataset consumption. Domain-
specific runtimes live elsewhere (`app/` for the text-adventure engine,
`bench/` for the code-generation flywheel) and import from here.

See the repo README for the harness framing.
"""
