"""Session state persistence for Wanderer playthroughs.

Single JSON file at the repo root for the current slice — single-player,
single-session, survives MCP server restarts. Both surfaces (MCP and
FastAPI) read/write the same file; the user only uses one at a time.

Multi-session support lands when storage moves to per-session SQLite.
"""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

SESSION_FILE = Path(__file__).parent.parent / "wanderer-session.json"


class ActionRecord(BaseModel):
    scene_id: str
    action: str
    evaluation: dict[str, Any]


class SessionState(BaseModel):
    episode_id: str | None = None
    current_scene_id: str | None = None
    world_state: dict[str, Any] = Field(default_factory=dict)
    action_history: list[ActionRecord] = Field(default_factory=list)

    @classmethod
    def load(cls) -> "SessionState":
        if not SESSION_FILE.exists():
            return cls()
        return cls.model_validate_json(SESSION_FILE.read_text())

    def save(self) -> None:
        SESSION_FILE.write_text(self.model_dump_json(indent=2))


def reset_session() -> None:
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()
