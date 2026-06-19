"""Mechanical scoring of model response format compliance + wander_eval-
specific judge rubric for the Conduct `judge` task type.

This module is part of the shared `harness/` layer — the same pattern
(mechanical scorer for syntactically-decidable dimensions + LLM judge rubric
override for dimensions that need judgment) is what the `bench/` code-gen
flywheel will reuse, with `code_eval` rubrics living alongside these
`wander_eval` ones as that work lands.

The `format` dimension answers one question: did the response obey the output
schema declared in the system prompt? It is mechanically derivable from the
raw response, so it is computed deterministically here rather than asked of
the LLM panel — jurors invent their own definitions of "format" otherwise.
See gotoplanb/conduct#20 for the panel observability issue surfaced by this.

`correctness` (did the model pick the right transition?) and `craft` (was the
prose in-world, second person, period-appropriate?) ARE asked of the panel —
those need judgment. The rubric below anchors jurors so both reach for the
same definition of each dimension; pass it as `system_prompt` on each judge
call.

See gotoplanb/conduct#15 / #18 for the score-dimension agreement and #17 for
the judge task type.
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


# Dimensions to ask the LLM panel for. `format` is intentionally absent —
# compute it mechanically with `score_eval_format` / `score_gen_format` and
# submit it separately. See gotoplanb/conduct#20 for why we drop it from the
# panel ask.
WANDER_EVAL_JUDGE_DIMENSIONS = ["correctness", "craft"]


WANDER_EVAL_JUDGE_RUBRIC = """\
You are evaluating the output of a `wander_eval` task. The task type belongs to \
Wanderer, an AI-driven text adventure engine.

CONTEXT
The ORIGINAL PROMPT describes a scene in an interactive story (narrative + \
"what good judgment looks like" + the world's state + the available transitions \
+ the player's action). The model's job is to return a single JSON object: \
verdict ("good" / "partial" / "poor"), explanation (1-2 sentences to the player \
in second person), coaching (1-2 sentences of forward-looking advice), and \
transition_index (which transition fires).

DIMENSIONS

`correctness` — did the model pick the right transition_index given the world \
state and the player's action? The "WHAT GOOD JUDGMENT LOOKS LIKE HERE" section \
of the prompt typically states the routing rule (e.g. "if 5+ conditions met and \
player names X, pick transition 0"). A correct response picks the index those \
rules dictate.
- 5: transition_index matches the rule exactly, AND the verdict aligns (good \
for the success path, partial for hedged, poor for self-dealing).
- 4: transition_index correct, verdict slightly off (e.g. "good" when "partial" \
was warranted, or vice versa).
- 3: transition_index correct but verdict clearly wrong; or transition_index \
off by one when the state-action mapping is genuinely ambiguous.
- 2: transition_index wrong but the model's reasoning shows it understood the \
scene.
- 1: transition_index wrong and the reasoning shows the model misread the scene \
or invented facts.

`craft` — is the prose well-made for a player to read? The explanation and \
coaching are shown verbatim to a human playing the game.
- 5: in-world voice (no engine terminology like "flags", "world state", \
"transition", "score"); second person addressing the player ("You did X..."); \
specific to what the player actually did (cites concrete actions/objects from \
the scene); period- and tone-appropriate to the episode register (Victorian \
mystery sounds Victorian; pirate sounds 17th-century; sci-fi sounds sci-fi); no \
narrative invention beyond what the scene set up; no anachronisms.
- 4: minor craft issue — one borderline meta-phrase ("the right answer here", \
"good judgment"), or one mild anachronism, or one sentence too many.
- 3: a clear craft drift — third-person narration, modern phrasing in a period \
setting, generic coaching ("keep doing this"), or a borderline-meta reference \
to the scene as a frame.
- 2: hard fourth-wall slip ("the world state shows", "transition 0", "the \
script"); or pronoun bug on a named character; or invents a continuation the \
scene didn't establish.
- 1: explicit engine terminology in the player-facing text, or coaching that \
breaks the fiction outright.

`format` is NOT asked of you. It is computed mechanically client-side. Do not \
score or comment on JSON validity, field presence, or markdown fences.

RULES
- Reason briefly per dimension before scoring.
- Be specific in rationale: quote the phrase that earned the score.
- Judge the response only against the prompt. Do not penalize a correct call \
because the explanation is short, or reward a wrong call because the prose is \
pretty.
- Do not invent dimensions. Score only `correctness` and `craft`.
"""


def wander_eval_judge_inputs(target_job_id: str, apply: bool = True) -> dict:
    """Build the `inputs` bag for a panel judge call on a wander_eval target.

    Pass the result to create_job(task_type="judge", system_prompt=
    WANDER_EVAL_JUDGE_RUBRIC, inputs=...).
    """
    return {
        "mode": "panel",
        "target_job_id": target_job_id,
        "apply_to_target": apply,
        "dimensions": WANDER_EVAL_JUDGE_DIMENSIONS,
    }


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
