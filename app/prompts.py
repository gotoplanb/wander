"""Prompt templates for Wanderer.

Shared between the FastAPI Ollama backend (`app.ai`, playtest mode) and the
MCP server (`app.mcp_server`, authoring mode via Claude orchestrator).
"""

import json
from typing import Any

from app.scenes import Scene

CHOICES_SYSTEM_PROMPT = """\
You generate three choices for a text adventure player at a decision point.

The choices must reflect what a real person in this situation might genuinely \
consider, given the WORLD STATE shown. A well-crafted distractor teaches as much \
as the correct answer — no obvious red herrings.

Generate exactly three choices:
- one that demonstrates clearly correct judgment (quality: "correct")
- one that is reasonable on its face but flawed in a non-obvious way (quality: "flawed")
- one that reflects a common mistake an undertrained person would make (quality: "mistake")

Each choice is a single action stated in first person, present tense, one sentence. \
Do NOT include the quality label in the visible text — the text is what the player \
reads as a button label.

Write each choice IN-WORLD. Do NOT reference the prompt, the evaluation context, \
the world state object, this scene, or your own role as "the script", "the rules", \
"the instructions", "the system", or similar. The player sees these strings verbatim; \
anything that breaks immersion ruins the scene.

Stay strictly within the scene as described. Do not invent objects, characters, or \
geography not mentioned in the scene, world state, or evaluation context.

OUTPUT FORMAT: Respond with a single JSON object and nothing else — no commentary, \
no markdown code fences, no preamble. Exact shape:
{"choices":[{"text":"...","quality":"correct"},{"text":"...","quality":"flawed"},{"text":"...","quality":"mistake"}]}
"""

EVAL_SYSTEM_PROMPT = """\
You evaluate a player's action against the scene's standard of good judgment and \
pick which transition condition fires next.

Return a single JSON object with these fields:
- verdict: "good" if the action reflects sound judgment; "partial" if it has merit \
  but misses something important; "poor" if it reflects a meaningful error.
- explanation: 1-2 sentences explaining the verdict. Address the player directly in \
  second person ("You..."). Be specific about what was right or wrong. Avoid generic \
  praise or criticism.
- coaching: 1-2 sentences of forward-looking advice tied to the specific error or \
  strength. Not a restatement of the explanation.
- transition_index: integer. The 0-based index of the transition condition (from the \
  TRANSITIONS list in the prompt) that best matches what the player just did. If the \
  scene is terminal or has no listed transitions, set this to 0. The engine handles \
  state changes; you do not need to report any.

Write explanation and coaching IN-WORLD. Do NOT reference the prompt, the evaluation \
context, the transitions list, this scene, or your own role as "the script", "the \
rules", "the instructions", "the system", or similar. The player sees these strings \
verbatim; anything that breaks immersion ruins the scene.

Do not invent consequences not implied by the scene. Do not advance the narrative — \
that is the engine's job.

OUTPUT FORMAT: Respond with a single JSON object and nothing else — no commentary, \
no markdown code fences, no preamble. Exact shape:
{"verdict":"good|partial|poor","explanation":"...","coaching":"...","transition_index":N}
"""


def _state_block(world_state: dict[str, Any]) -> str:
    if not world_state:
        return "WORLD STATE: (empty)"
    return f"WORLD STATE:\n{json.dumps(world_state, indent=2)}"


def _transitions_block(scene: Scene) -> str:
    if scene.is_terminal or not scene.transitions:
        return "TRANSITIONS: (this scene is terminal; set transition_index to 0)"
    lines = [f"{i}. {t.condition}" for i, t in enumerate(scene.transitions)]
    return "TRANSITIONS (pick the index of the one that fires):\n" + "\n".join(lines)


def scene_brief(scene: Scene, world_state: dict[str, Any]) -> str:
    return (
        f"SCENE:\n{scene.narrative}\n\n"
        f"WHAT GOOD JUDGMENT LOOKS LIKE HERE:\n{scene.evaluation_context}\n\n"
        f"{_state_block(world_state)}"
    )


def choices_user_prompt(scene: Scene, world_state: dict[str, Any]) -> str:
    return f"{scene_brief(scene, world_state)}\n\nGenerate three choices."


def eval_user_prompt(
    scene: Scene, action_text: str, world_state: dict[str, Any]
) -> str:
    return (
        f"{scene_brief(scene, world_state)}\n\n"
        f"{_transitions_block(scene)}\n\n"
        f"PLAYER ACTION:\n{action_text}\n\n"
        f"Evaluate the action and pick a transition."
    )
