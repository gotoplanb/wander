"""Wanderer MCP server.

State machine + content + prompt templates. Does NOT make AI calls.

Tool flow per turn:

  start_episode(id) -> {scene, choice_gen_request}
       └─> submit choice_gen_request to mcp__claude_ai_conduct-dave-ios__create_job
       └─> parse JSON response into three choices, present to the player

  evaluate_action(action_text) -> {eval_request, transitions}
       └─> submit eval_request to Conduct
       └─> parse {verdict, explanation, coaching, transition_index}

  advance(action_text, evaluation) -> {evaluation, scene, choice_gen_request}
       └─> server validates evaluation, applies the CHOSEN TRANSITION's
           declared state_delta, advances to the next scene

State changes are declared on each Transition in the episode SQLite and
applied deterministically by the engine — the AI only picks the index.
"""

from typing import Any

from fastmcp import FastMCP
from pydantic import ValidationError

from app.episodes import load_episode
from app.models import Evaluation
from app.prompts import (
    CHOICES_SYSTEM_PROMPT,
    EVAL_SYSTEM_PROMPT,
    choices_user_prompt,
    eval_user_prompt,
)
from app.scenes import Scene
from app.session import ActionRecord, SessionState, reset_session

mcp = FastMCP("wander")

DEFAULT_EPISODE_ID = "forest-demo"
GEN_TASK_TYPE = "wander_gen"
EVAL_TASK_TYPE = "wander_eval"
SENSITIVITY = "public"


def _scene_payload(scene: Scene) -> dict[str, Any]:
    return {
        "scene_id": scene.id,
        "title": scene.title,
        "narrative": scene.narrative,
        "visual_description": scene.visual_description,
        "is_terminal": scene.is_terminal,
        "outcome": scene.outcome,
    }


def _choice_gen_request(scene: Scene, world_state: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_type": GEN_TASK_TYPE,
        "system_prompt": CHOICES_SYSTEM_PROMPT,
        "prompt": choices_user_prompt(scene, world_state),
        "sensitivity": SENSITIVITY,
        "force_shadows": True,
    }


def _eval_request(
    scene: Scene, action_text: str, world_state: dict[str, Any]
) -> dict[str, Any]:
    return {
        "task_type": EVAL_TASK_TYPE,
        "system_prompt": EVAL_SYSTEM_PROMPT,
        "prompt": eval_user_prompt(scene, action_text, world_state),
        "sensitivity": SENSITIVITY,
        "force_shadows": True,
    }


@mcp.tool
def start_episode(episode_id: str = DEFAULT_EPISODE_ID) -> dict[str, Any]:
    """Begin a new Wanderer playthrough."""
    try:
        episode = load_episode(episode_id)
    except FileNotFoundError as exc:
        return {"error": str(exc)}

    scene = episode.scenes[episode.opening_scene_id]
    state = SessionState(
        episode_id=episode_id,
        current_scene_id=scene.id,
        world_state=dict(episode.initial_world_state),
        action_history=[],
    )
    state.save()
    return {
        "episode": {
            "id": episode.id,
            "title": episode.title,
            "description": episode.description,
        },
        "world_state": state.world_state,
        "scene": _scene_payload(scene),
        "choice_gen_request": _choice_gen_request(scene, state.world_state),
    }


@mcp.tool
def evaluate_action(action_text: str) -> dict[str, Any]:
    """Prepare an evaluation request for the player's action.

    Returns the eval_request payload to submit to Conduct. The AI's response
    must include verdict, explanation, coaching, and transition_index. The
    AI does NOT need to return state changes — those are declared on each
    transition in the episode and applied by the engine.
    """
    state = SessionState.load()
    if state.episode_id is None or state.current_scene_id is None:
        return {"error": "No active episode. Call start_episode first."}
    episode = load_episode(state.episode_id)
    scene = episode.scenes[state.current_scene_id]
    return {
        "current_scene_id": scene.id,
        "action_text": action_text,
        "world_state": state.world_state,
        "transitions": [
            {"index": i, "condition": t.condition}
            for i, t in enumerate(scene.transitions)
        ],
        "eval_request": _eval_request(scene, action_text, state.world_state),
    }


@mcp.tool
def advance(action_text: str, evaluation: dict[str, Any]) -> dict[str, Any]:
    """Record the turn, follow the chosen transition, apply its declared state delta.

    Any `state_delta` returned by the AI in `evaluation` is ignored — the
    engine applies the transition's declared state_delta deterministically.
    """
    state = SessionState.load()
    if state.episode_id is None or state.current_scene_id is None:
        return {"error": "No active episode. Call start_episode first."}

    try:
        eval_obj = Evaluation.model_validate(evaluation)
    except ValidationError as exc:
        return {
            "error": "evaluation did not match the expected schema",
            "expected_schema": Evaluation.model_json_schema(),
            "validation_errors": exc.errors(),
        }

    episode = load_episode(state.episode_id)
    current = episode.scenes[state.current_scene_id]

    if not current.is_terminal and current.transitions:
        if not (0 <= eval_obj.transition_index < len(current.transitions)):
            return {
                "error": "transition_index out of range",
                "transition_count": len(current.transitions),
                "got": eval_obj.transition_index,
                "valid_range": f"0 to {len(current.transitions) - 1}",
            }

    state.action_history.append(
        ActionRecord(
            scene_id=current.id,
            action=action_text,
            evaluation=eval_obj.model_dump(),
        )
    )

    if current.is_terminal or not current.transitions:
        state.save()
        return {
            "evaluation": eval_obj.model_dump(),
            "world_state": state.world_state,
            "terminal": True,
            "previous_scene_id": current.id,
            "outcome": current.outcome,
        }

    transition = current.transitions[eval_obj.transition_index]

    # Apply the transition's declared state delta (engine-deterministic, not AI).
    state.world_state.update(transition.state_delta)

    next_scene = episode.scenes[transition.next_scene_id]
    state.current_scene_id = next_scene.id
    state.save()

    return {
        "evaluation": eval_obj.model_dump(),
        "world_state": state.world_state,
        "transition": {
            "index": eval_obj.transition_index,
            "condition": transition.condition,
            "applied_state_delta": transition.state_delta,
        },
        "scene": _scene_payload(next_scene),
        "choice_gen_request": _choice_gen_request(next_scene, state.world_state),
    }


@mcp.tool
def current_state() -> dict[str, Any]:
    """Return the current session state — useful for debug or resume."""
    state = SessionState.load()
    return {
        "episode_id": state.episode_id,
        "current_scene_id": state.current_scene_id,
        "world_state": state.world_state,
        "action_count": len(state.action_history),
        "actions": [a.model_dump() for a in state.action_history],
    }


@mcp.tool
def reset() -> dict[str, str]:
    """Clear the current session."""
    reset_session()
    return {"status": "reset"}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
