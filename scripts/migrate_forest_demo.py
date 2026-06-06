"""Seed `episodes/forest-demo/episode.sqlite` from the same content the old
hardcoded SCENES dict served. Idempotent — drops and recreates the DB.
"""

import json
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
EPISODE_DIR = REPO_ROOT / "episodes" / "forest-demo"
DB_PATH = EPISODE_DIR / "episode.sqlite"

SAMPLE_INTRO_1 = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"
SAMPLE_AMBIENT_1 = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
SAMPLE_INTRO_2 = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4"
SAMPLE_AMBIENT_2 = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4"

SCHEMA = """
CREATE TABLE episode_metadata (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    version TEXT NOT NULL,
    author TEXT,
    world_constraints TEXT,
    opening_scene_id TEXT NOT NULL,
    initial_world_state TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE scenes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    narrative TEXT NOT NULL,
    visual_description TEXT NOT NULL,
    evaluation_context TEXT NOT NULL,
    intro_video TEXT,
    ambient_video TEXT,
    is_terminal INTEGER NOT NULL DEFAULT 0,
    outcome TEXT
);

CREATE TABLE transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scene_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    condition TEXT NOT NULL,
    next_scene_id TEXT NOT NULL,
    state_delta TEXT NOT NULL DEFAULT '{}',
    UNIQUE (scene_id, position),
    FOREIGN KEY (scene_id) REFERENCES scenes(id),
    FOREIGN KEY (next_scene_id) REFERENCES scenes(id)
);

CREATE INDEX idx_transitions_scene ON transitions(scene_id);
"""

EPISODE_META = {
    "id": "forest-demo",
    "title": "The Forest Edge",
    "description": "A two-scene proof of the Wanderer engine. Real branching comes with KQ1.",
    "version": "0.1.0",
    "author": "Dave Stanton",
    "world_constraints": (
        "A solitary traveler on a path through a darkening forest. Stay within the bounds "
        "of a low-fantasy traveler's journey: no magic, no monsters, no characters beyond "
        "what the scene mentions. Inventory items are limited to plausible traveler gear."
    ),
    "opening_scene_id": "opening",
    "initial_world_state": {},
}

SCENES = [
    {
        "id": "opening",
        "title": "The forest edge",
        "narrative": (
            "You stand at the edge of a darkening forest. A narrow path winds "
            "east beneath the trees. A stream burbles south toward open meadow. "
            "Behind you, the lights of the village have already faded."
        ),
        "visual_description": (
            "A wide shot at twilight. A dirt path's edge where a darkening forest "
            "gives way to open meadow. Gnarled oaks form a shadowed tunnel to the "
            "east; their canopies catch the last orange light. To the south, a "
            "small stream cuts through tall grass. Mist rises from the wet ground. "
            "Far behind, the pinprick lights of a small village fade into deepening "
            "blue. The air is cold; the protagonist's breath fogs faintly."
        ),
        "evaluation_context": (
            "The player is alone, unequipped beyond what a traveler would carry, "
            "and dusk is settling. Good judgment here means recognizing that the "
            "forest is risky in fading light but the path is the intended route — "
            "moving forward with awareness of time and footing. Following the "
            "stream is reasonable for navigation but takes the player away from "
            "the destination. Turning back to the village is a clear failure of "
            "the journey's purpose: it abandons the goal at the first sign of "
            "discomfort. Sound actions: take the path with care, light a torch "
            "or check supplies before entering. Flawed but reasonable: follow "
            "the stream as a navigation aid. Common mistake: turn back."
        ),
        "intro_video": SAMPLE_INTRO_1,
        "ambient_video": SAMPLE_AMBIENT_1,
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "any action — the player commits to a direction and the journey continues",
                "next_scene_id": "forest",
            },
        ],
    },
    {
        "id": "forest",
        "title": "Deeper in",
        "narrative": (
            "The trees close overhead. You find yourself in a small clearing "
            "where moss covers a flat stone slab. Something glints beneath it. "
            "From somewhere ahead, you hear water — but not the stream you left."
        ),
        "visual_description": (
            "Close in among ancient trees, canopies woven so tightly little "
            "daylight reaches the forest floor. A small clearing opens around a "
            "flat moss-covered stone slab, roughly the size of a tabletop. "
            "Something metallic glints in a narrow gap beneath one edge — gold or "
            "polished steel, hard to tell. Ferns and tree roots curl around the "
            "slab. Ahead, water trickles over rock — too narrow and too clear-"
            "sounding to be the stream the player left. Insects drone, then go "
            "silent all at once."
        ),
        "evaluation_context": (
            "Two signals compete: an object of interest under the slab, and an "
            "unfamiliar water source nearby. Good judgment is curious but cautious — "
            "investigate the slab without committing fully (look around it first, "
            "test its weight, watch for traps or unstable footing). Reasonable but "
            "flawed: follow the new water sound, since fresh water is genuinely "
            "useful but pulls the player off-task into the unknown. Common mistake: "
            "press on through the trees without engaging either signal, missing "
            "information that could matter later. Sound actions: examine the slab "
            "deliberately. Flawed but reasonable: investigate the water. Mistake: "
            "ignore both and keep walking."
        ),
        "intro_video": SAMPLE_INTRO_2,
        "ambient_video": SAMPLE_AMBIENT_2,
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "any action — the player makes a choice in the clearing and the journey loops",
                "next_scene_id": "opening",
            },
        ],
    },
]


def main() -> None:
    EPISODE_DIR.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA)
        conn.execute(
            "INSERT INTO episode_metadata "
            "(id, title, description, version, author, world_constraints, "
            "opening_scene_id, initial_world_state) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                EPISODE_META["id"],
                EPISODE_META["title"],
                EPISODE_META["description"],
                EPISODE_META["version"],
                EPISODE_META["author"],
                EPISODE_META["world_constraints"],
                EPISODE_META["opening_scene_id"],
                json.dumps(EPISODE_META["initial_world_state"]),
            ),
        )
        for scene in SCENES:
            conn.execute(
                "INSERT INTO scenes "
                "(id, title, narrative, visual_description, evaluation_context, "
                "intro_video, ambient_video, is_terminal, outcome) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    scene["id"],
                    scene["title"],
                    scene["narrative"],
                    scene["visual_description"],
                    scene["evaluation_context"],
                    scene["intro_video"],
                    scene["ambient_video"],
                    int(scene["is_terminal"]),
                    scene["outcome"],
                ),
            )
            for pos, t in enumerate(scene["transitions"]):
                conn.execute(
                    "INSERT INTO transitions "
                    "(scene_id, position, condition, next_scene_id, state_delta) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        scene["id"],
                        pos,
                        t["condition"],
                        t["next_scene_id"],
                        json.dumps(t.get("state_delta", {})),
                    ),
                )
        conn.commit()
        print(f"Wrote {DB_PATH}")
        print(
            f"  scenes:      {conn.execute('SELECT COUNT(*) FROM scenes').fetchone()[0]}"
        )
        print(
            f"  transitions: {conn.execute('SELECT COUNT(*) FROM transitions').fetchone()[0]}"
        )
    finally:
        conn.close()


if __name__ == "__main__":
    main()
