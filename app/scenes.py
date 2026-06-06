"""Episode + scene + transition dataclasses.

Pure data shapes — no hardcoded content. Episodes load from SQLite via
`app.episodes.load_episode`.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Transition:
    """One branch out of a scene.

    The AI picks which condition fires by index (`transition_index` in its
    response). The engine applies `state_delta` deterministically when this
    transition is the one chosen — the AI never has to remember to set both
    fields consistently.
    """

    condition: str  # human-readable, shown to the AI
    next_scene_id: str
    state_delta: dict[str, Any] = field(default_factory=dict)


@dataclass
class Scene:
    id: str
    title: str
    narrative: str
    visual_description: str
    evaluation_context: str
    transitions: list[Transition] = field(default_factory=list)
    intro_video: str | None = None
    ambient_video: str | None = None
    is_terminal: bool = False
    outcome: str | None = None  # "success" | "failure" | "partial" | None


@dataclass
class Episode:
    id: str
    title: str
    description: str
    version: str
    author: str
    world_constraints: str
    opening_scene_id: str
    initial_world_state: dict[str, Any]
    scenes: dict[str, Scene]
