"""Mechanical scoring of model response format compliance.

Computes the `format` dimension of the eval score deterministically from a raw
response string. Used when submitting `submit_eval` to Conduct so the format
dimension is reproducible across runs and never confused with content judgment.

The `format` dimension answers one question: did the response obey the output
schema declared in the system prompt? It is intentionally separate from
`correctness` (did the model pick the right transition?) and `craft` (was the
prose in-world, second person, specific?). See gotoplanb/conduct#15 for the
score-dimension agreement.
"""

import json
from typing import Any

REQUIRED_EVAL_FIELDS = frozenset(
    {"verdict", "explanation", "coaching", "transition_index"}
)
VALID_VERDICTS = frozenset({"good", "partial", "poor"})

REQUIRED_GEN_FIELDS = frozenset({"choices"})
REQUIRED_CHOICE_FIELDS = frozenset({"text", "quality"})
VALID_QUALITIES = frozenset({"correct", "flawed", "mistake"})


def _has_markdown_fence(raw: str) -> bool:
    return "```" in raw


def _is_pure_json_object(raw: str) -> bool:
    s = raw.strip()
    return s.startswith("{") and s.endswith("}")


def score_format(
    raw: str,
    *,
    required_fields: frozenset[str],
    optional_fields: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    """Mechanically score JSON output format compliance.

    Returns a dict with:
      - score: int 1-5
      - issues: list of short tags suitable for the eval note
      - parsed: the parsed JSON dict if parse succeeded, else None
    """
    issues: list[str] = []
    parsed: dict[str, Any] | None = None

    if _has_markdown_fence(raw):
        issues.append("markdown_fence")
    if not _is_pure_json_object(raw):
        issues.append("not_pure_json_object")

    # Try to parse — strip whitespace and fences if present
    candidate = raw.strip()
    if candidate.startswith("```"):
        candidate = candidate.lstrip("`")
        if candidate.lower().startswith("json"):
            candidate = candidate[4:]
        candidate = candidate.strip().rstrip("`").strip()
    if "{" in candidate and "}" in candidate:
        candidate = candidate[candidate.index("{") : candidate.rindex("}") + 1]

    try:
        parsed_any = json.loads(candidate)
        if not isinstance(parsed_any, dict):
            issues.append("not_object")
        else:
            parsed = parsed_any
    except json.JSONDecodeError:
        issues.append("parse_error")

    if parsed is not None:
        present = set(parsed.keys())
        missing = required_fields - present
        for field in sorted(missing):
            issues.append(f"missing:{field}")
        allowed = required_fields | optional_fields
        extra = present - allowed
        for field in sorted(extra):
            issues.append(f"extra:{field}")

    # Score: start at 5, subtract per issue category
    score = 5
    weights = {
        "markdown_fence": 2,
        "not_pure_json_object": 1,
        "not_object": 3,
        "parse_error": 3,
    }
    for issue in issues:
        if issue in weights:
            score -= weights[issue]
        elif issue.startswith("missing:"):
            score -= 2
        elif issue.startswith("extra:"):
            score -= 1
    score = max(1, min(5, score))

    return {"score": score, "issues": issues, "parsed": parsed}


def score_eval_format(raw: str) -> dict[str, Any]:
    """Format-score a wander_eval response. Also validates verdict enum."""
    result = score_format(raw, required_fields=REQUIRED_EVAL_FIELDS)
    parsed = result["parsed"]
    if parsed is not None and "verdict" in parsed:
        if parsed["verdict"] not in VALID_VERDICTS:
            result["issues"].append(f"invalid_verdict:{parsed['verdict']}")
            result["score"] = max(1, result["score"] - 1)
    if parsed is not None and "transition_index" in parsed:
        if not isinstance(parsed["transition_index"], int):
            result["issues"].append("transition_index_not_int")
            result["score"] = max(1, result["score"] - 1)
    return result


def score_gen_format(raw: str) -> dict[str, Any]:
    """Format-score a wander_gen response. Also validates the 3-choice shape."""
    result = score_format(raw, required_fields=REQUIRED_GEN_FIELDS)
    parsed = result["parsed"]
    if parsed is not None and "choices" in parsed:
        choices = parsed["choices"]
        if not isinstance(choices, list):
            result["issues"].append("choices_not_list")
            result["score"] = max(1, result["score"] - 2)
        else:
            if len(choices) != 3:
                result["issues"].append(f"choice_count:{len(choices)}")
                result["score"] = max(1, result["score"] - 2)
            seen_qualities: set[str] = set()
            for i, choice in enumerate(choices):
                if not isinstance(choice, dict):
                    result["issues"].append(f"choice_{i}_not_object")
                    result["score"] = max(1, result["score"] - 1)
                    continue
                missing = REQUIRED_CHOICE_FIELDS - set(choice.keys())
                for field in sorted(missing):
                    result["issues"].append(f"choice_{i}_missing:{field}")
                    result["score"] = max(1, result["score"] - 1)
                q = choice.get("quality")
                if q is not None and q not in VALID_QUALITIES:
                    result["issues"].append(f"choice_{i}_invalid_quality:{q}")
                    result["score"] = max(1, result["score"] - 1)
                if q in VALID_QUALITIES:
                    seen_qualities.add(q)
            if seen_qualities and seen_qualities != VALID_QUALITIES:
                missing_q = VALID_QUALITIES - seen_qualities
                for mq in sorted(missing_q):
                    result["issues"].append(f"missing_quality:{mq}")
                    result["score"] = max(1, result["score"] - 1)
    result["score"] = max(1, min(5, result["score"]))
    return result


def format_note(format_result: dict[str, Any]) -> str:
    """Render the format-score result as a short tag suitable for inclusion
    in an eval note alongside craft/correctness scores."""
    if not format_result["issues"]:
        return f"format=5/5"
    return f"format={format_result['score']}/5({','.join(format_result['issues'])})"
