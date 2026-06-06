"""Episode loader."""

import json
import sqlite3
from pathlib import Path

from app.scenes import Episode, Scene, Transition

EPISODES_DIR = Path(__file__).parent.parent / "episodes"

_cache: dict[str, Episode] = {}


def _episode_path(episode_id: str) -> Path:
    return EPISODES_DIR / episode_id / "episode.sqlite"


def load_episode(episode_id: str) -> Episode:
    """Load an episode by id. Cached after first call."""
    if episode_id in _cache:
        return _cache[episode_id]

    db_path = _episode_path(episode_id)
    if not db_path.exists():
        raise FileNotFoundError(
            f"Episode {episode_id!r} not found at {db_path}. "
            f"Run the matching migration script in scripts/."
        )

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        meta_row = conn.execute("SELECT * FROM episode_metadata").fetchone()
        if meta_row is None:
            raise ValueError(f"Episode {episode_id!r} has no metadata row.")

        scenes: dict[str, Scene] = {}
        for scene_row in conn.execute("SELECT * FROM scenes").fetchall():
            sid = scene_row["id"]
            transitions = [
                Transition(
                    condition=t["condition"],
                    next_scene_id=t["next_scene_id"],
                    state_delta=json.loads(t["state_delta"] or "{}"),
                )
                for t in conn.execute(
                    "SELECT * FROM transitions WHERE scene_id = ? ORDER BY position",
                    (sid,),
                ).fetchall()
            ]
            scenes[sid] = Scene(
                id=sid,
                title=scene_row["title"],
                narrative=scene_row["narrative"],
                visual_description=scene_row["visual_description"],
                evaluation_context=scene_row["evaluation_context"],
                transitions=transitions,
                intro_video=scene_row["intro_video"],
                ambient_video=scene_row["ambient_video"],
                is_terminal=bool(scene_row["is_terminal"]),
                outcome=scene_row["outcome"],
            )

        episode = Episode(
            id=meta_row["id"],
            title=meta_row["title"],
            description=meta_row["description"] or "",
            version=meta_row["version"],
            author=meta_row["author"] or "",
            world_constraints=meta_row["world_constraints"] or "",
            opening_scene_id=meta_row["opening_scene_id"],
            initial_world_state=json.loads(meta_row["initial_world_state"]),
            scenes=scenes,
        )
        _cache[episode_id] = episode
        return episode
    finally:
        conn.close()


def clear_cache() -> None:
    _cache.clear()
