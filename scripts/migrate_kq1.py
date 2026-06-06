"""Seed `episodes/kq1/episode.sqlite`.

A King's Quest 1-inspired arc: a wanderer is given a quest by an aging king
to retrieve three lost treasures from monstrous keepers. Original prose;
fairy-tale tropes (sleeping dragon, witch's oven, sky-giant) are drawn from
public-domain folklore, not from the Sierra game.

Exercises the engine's new surface: state tracking (has_mirror / has_chest /
has_shield), multi-condition transitions (3 outcomes per puzzle scene),
state-driven ending selection (throne_return picks one of three endings
based on what the player carries home).

Idempotent — drops and recreates the DB.
"""

import json
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
EPISODE_DIR = REPO_ROOT / "episodes" / "kq1"
DB_PATH = EPISODE_DIR / "episode.sqlite"

# Reused Google sample MP4s as placeholders. The visual_description on each
# scene is what we'll feed to a video model later.
V = {
    "blazes": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
    "bunny": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
    "escapes": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
    "elephants": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
    "fun": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
    "joyrides": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4",
    "meltdowns": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerMeltdowns.mp4",
}

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
    "id": "kq1",
    "title": "Three Treasures",
    "description": (
        "A wanderer is sent by an aging king to retrieve three lost magical "
        "treasures from a dragon, a witch, and a sky-giant. KQ1-inspired."
    ),
    "version": "0.1.0",
    "author": "Dave Stanton",
    "world_constraints": (
        "A solitary wanderer on a quest given by an aging king. The world is "
        "low-fantasy: a small kingdom edged by wild country with fairy-tale "
        "dangers — a dragon coiled in a deep well, a witch in a wooded cottage, "
        "a giant asleep above the clouds. Three magic treasures (a mirror, a "
        "chest, a shield) are the objects of the quest. Player actions should "
        "fit a knight's-tale traveler — examining surroundings, sneaking, "
        "speaking, fighting if necessary. Reject actions that invoke modern "
        "technology, characters from other stories, or magic the wanderer has "
        "not been told they possess. State flags track which treasures the "
        "wanderer has obtained."
    ),
    "opening_scene_id": "opening",
    "initial_world_state": {
        "has_mirror": False,
        "has_chest": False,
        "has_shield": False,
    },
}


SCENES = [
    # ---------- 1. Opening ----------
    {
        "id": "opening",
        "title": "The aging king's errand",
        "narrative": (
            "An aging king leans forward on his throne, the crown sitting heavy on "
            "thin grey hair. The kingdom is failing, he tells you. Three sacred "
            "treasures — a mirror that shows tomorrow, a chest that gives gold "
            "without end, a shield that turns blades — were carried off long ago by "
            "the monsters of the wild country. Bring them back, the king says, and "
            "the throne will be yours when he passes. The court stands at the walls, "
            "watching. The great doors behind you stand open onto green countryside."
        ),
        "visual_description": (
            "An ancient stone throne room lit through tall windows of cracked stained "
            "glass. Dust drifts in slanted afternoon light. The old king in faded "
            "purple robes sits forward on a worn wooden throne — the crown almost "
            "slipping from his head. Courtiers in muted finery stand at a respectful "
            "distance against the walls. Through the open doors at the far end you "
            "can see green hills under a hazy sun."
        ),
        "evaluation_context": (
            "The opening. The player has just been given a quest by an aging king "
            "in front of his court. Good judgment is to accept the charge with "
            "appropriate respect and set out. The scene is mostly setup — almost any "
            "committed forward action advances the story. Sound actions: kneel and "
            "accept, ask a clarifying question about the treasures or where to find "
            "them, take formal leave. Flawed but reasonable: ask for an escort or "
            "supplies before leaving. Common mistake: refuse the quest, mock the "
            "king, demand the throne now, or simply walk out without acknowledgment."
        ),
        "intro_video": V["joyrides"],
        "ambient_video": V["meltdowns"],
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the wanderer accepts the quest and sets out",
                "next_scene_id": "dragon_well",
            },
        ],
    },
    # ---------- 2. Dragon's well ----------
    {
        "id": "dragon_well",
        "title": "The dragon's well",
        "narrative": (
            "Days of walking bring you to a deep well in a clearing. Stone steps "
            "spiral down its inner wall. Torchlight from below catches the scales "
            "of an enormous dragon curled at the bottom, sides rising and falling "
            "in slow sleep. Behind it, propped against the curved wall, a mirror in "
            "a frame of bone-white silver catches the torchlight and throws it back. "
            "The dragon's breath stirs the dust between you."
        ),
        "visual_description": (
            "Slick stone steps spiraling down into a wide stone well lit by guttering "
            "torches. At the bottom, an enormous dragon coiled three times on itself, "
            "scales the color of wet iron, breathing slow. A great silvered mirror is "
            "propped against the far wall behind it, catching the torchlight in long "
            "white reflections. Dust drifts in the warm air. Single shaft of daylight "
            "comes down from above."
        ),
        "evaluation_context": (
            "The wanderer must retrieve the magic mirror while the dragon sleeps. "
            "Good judgment is silent caution: tiptoe down, hug the wall, test each "
            "step for loose stones, breathe carefully, lift the mirror without "
            "scraping it. The dragon's hearing is the threat — a single loud sound "
            "wakes it. Sound actions: tiptoe with care, hold breath, take the mirror "
            "by the frame and retreat. Reasonable but flawed: descend partway, judge "
            "the risk too great, retreat empty-handed (no mirror but alive). Common "
            "mistake that ends the quest: draw a weapon, shout, throw something at "
            "the dragon, run for the mirror, attempt to fight or speak. The AI "
            "should set state_delta has_mirror to true ONLY if the action results "
            "in successfully retrieving the mirror (transition 0)."
        ),
        "intro_video": V["blazes"],
        "ambient_video": V["bunny"],
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the wanderer retrieves the mirror without waking the dragon",
                "next_scene_id": "cliff_path",
                "state_delta": {"has_mirror": True},
            },
            {
                "condition": "the wanderer judges the risk too great and retreats empty-handed but alive",
                "next_scene_id": "cliff_path",
            },
            {
                "condition": "the wanderer wakes the dragon",
                "next_scene_id": "death_dragon",
            },
        ],
    },
    # ---------- 3. Cliff path ----------
    {
        "id": "cliff_path",
        "title": "The narrow ledge",
        "narrative": (
            "The road climbs into broken country and narrows to a ledge along a "
            "sheer rock face. There is no path back the way you came. The valley "
            "drops away to your left in a long fall of slate and scrub. Wind pulls "
            "steadily at your coat. The ledge curls around the cliff and is lost "
            "from sight where it bends."
        ),
        "visual_description": (
            "A narrow ledge — barely wider than a footstep — cut into a sheer slate "
            "cliff. To one side: bare wet rock rising out of frame. To the other: a "
            "long drop to a misted valley of grey stone and stunted pine. The sky is "
            "overcast and uneasy. Wind pulls strands of dust and grit along the "
            "ledge. The ledge bends out of sight ahead."
        ),
        "evaluation_context": (
            "The wanderer must cross a narrow cliff ledge. Good judgment is steady "
            "and patient: face the wall, move sideways, test footing before "
            "committing weight, keep one hand on rock at all times. Reasonable but "
            "flawed: cross at normal walking pace facing forward — quicker, riskier, "
            "but survivable. Common mistake that ends the quest: look down for too "
            "long, run, jump, turn back partway and panic, drop to all fours and "
            "freeze. No state change at this scene — the only treasure here is "
            "survival."
        ),
        "intro_video": V["escapes"],
        "ambient_video": V["elephants"],
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the wanderer crosses safely",
                "next_scene_id": "witches_cottage",
            },
            {
                "condition": "the wanderer falls from the ledge",
                "next_scene_id": "death_cliff",
            },
        ],
    },
    # ---------- 4. Witch's cottage ----------
    {
        "id": "witches_cottage",
        "title": "The witch's hearth",
        "narrative": (
            "A cottage stands alone among old beech trees, smoke curling from a "
            "crooked chimney. The air smells of fresh bread. An old woman in a "
            "homespun dress opens the door before you can knock, smiles wide enough "
            "to show too many teeth, and invites you to warm yourself by the fire. "
            "Inside, a great oven roars in the corner. On the mantel sits a small "
            "carved chest, dark wood bound in brass."
        ),
        "visual_description": (
            "A small cottage in a clearing of old beech trees, late-afternoon "
            "light slanting golden through the leaves. Smoke from a crooked stone "
            "chimney. Through the open door: a single firelit room with hanging "
            "herbs, a long scrubbed table, a great brick oven with its iron door "
            "open showing flames inside. A dark carved chest with brass bands sits "
            "on the mantel. The old woman in the doorway smiles a sharp smile, eyes "
            "small and bright."
        ),
        "evaluation_context": (
            "The wanderer is at the cottage of a witch who will try to put them in "
            "the oven and take their bones. The carved chest on the mantel is the "
            "magic chest the king sent the wanderer for. Good judgment is to play "
            "along just enough to get close to the oven, then turn the trap on the "
            "witch herself — ask her to demonstrate how the oven works, shove her "
            "in, take the chest and leave. Reasonable but flawed: refuse her "
            "hospitality and flee the cottage empty-handed (alive but no chest). "
            "Common mistake that ends the quest: accept her food, sit at the table, "
            "fall asleep by the fire, fight her openly (she has the home advantage "
            "and is stronger than she looks). The AI should set state_delta "
            "has_chest to true ONLY if the wanderer obtains the chest (transition "
            "0)."
        ),
        "intro_video": V["blazes"],
        "ambient_video": V["fun"],
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the wanderer tricks the witch and escapes with the chest",
                "next_scene_id": "cloud_realm",
                "state_delta": {"has_chest": True},
            },
            {
                "condition": "the wanderer flees the cottage empty-handed but alive",
                "next_scene_id": "cloud_realm",
            },
            {
                "condition": "the wanderer is caught by the witch",
                "next_scene_id": "death_witch",
            },
        ],
    },
    # ---------- 5. Cloud realm ----------
    {
        "id": "cloud_realm",
        "title": "Above the clouds",
        "narrative": (
            "A vine ladder rises from a hilltop into the clouds. You climb. The "
            "clouds part around a meadow of cloud-grass, soft and dry underfoot. In "
            "the meadow, an enormous oak. Beneath the oak, a giant lies on his side, "
            "snoring slow thunder. Propped against the trunk where it meets the "
            "ground: a round shield, bronze, faintly humming. The giant's breath "
            "moves a circle of grass in and out with each rise and fall."
        ),
        "visual_description": (
            "A floor of pale cloud under a deep blue sky. A single enormous oak "
            "grows out of the cloud-meadow, leaves silver-green. A giant — easily "
            "twenty feet tall — lies on his side beneath the oak, mouth slightly "
            "open, snoring. A round bronze shield rests against the trunk where it "
            "meets the cloud. The grass around the giant rises and falls slightly "
            "with his breathing. Distant horizon of more cloud, going on forever."
        ),
        "evaluation_context": (
            "The wanderer must take the magic shield from beside the sleeping giant. "
            "Good judgment is to move in time with the giant's breathing — step "
            "while he exhales, freeze while he inhales — keep low, hug the line "
            "of the oak's shadow, lift the shield slowly, retreat the same way. "
            "Reasonable but flawed: judge the risk too great and climb back down "
            "the vine empty-handed (no shield but alive). Common mistake that ends "
            "the quest: rush, drop something, run for the shield, attempt to use "
            "magic, attempt to threaten or wake the giant on purpose, or step on a "
            "vine root that snaps. The AI should set state_delta has_shield to true "
            "ONLY if the wanderer successfully takes the shield (transition 0)."
        ),
        "intro_video": V["fun"],
        "ambient_video": V["bunny"],
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the wanderer takes the shield without waking the giant",
                "next_scene_id": "throne_return",
                "state_delta": {"has_shield": True},
            },
            {
                "condition": "the wanderer judges the risk too great and retreats empty-handed but alive",
                "next_scene_id": "throne_return",
            },
            {
                "condition": "the wanderer wakes the giant",
                "next_scene_id": "death_giant",
            },
        ],
    },
    # ---------- 6. Throne return ----------
    {
        "id": "throne_return",
        "title": "The return",
        "narrative": (
            "The road brings you back to the kingdom by dusk. The great doors of "
            "the throne room are closed but open at your approach. The aging king "
            "is still on his throne, thinner now. The court has thinned too — only "
            "a few stand at the walls. The king straightens as you enter and asks, "
            "without ceremony, what you have brought."
        ),
        "visual_description": (
            "The throne room again — same tall stained-glass windows, but the light "
            "now is the last orange of evening. Long shadows. Fewer courtiers, "
            "spaced further apart. The aging king on the worn throne, more bowed "
            "than before, watching the wanderer at the doors with quiet, tired "
            "attention. Dust hangs in the air. The wanderer's footsteps echo."
        ),
        "evaluation_context": (
            "Final scene before the ending. The wanderer is reporting back to the "
            "king. The TRANSITION to pick depends ENTIRELY on the WORLD STATE: if "
            "has_mirror AND has_chest AND has_shield are all true, pick transition "
            "0 (triumphant). If at least one is true but not all, pick transition 1 "
            "(partial). If all three are false, pick transition 2 (empty-handed). "
            "The verdict can reflect the dignity of how the wanderer presents (good "
            "if they speak honestly and respectfully, partial if they exaggerate or "
            "deflect, poor if they lie or insult the king), but the verdict does "
            "not change which transition fires — the world state alone decides "
            "that. No state_delta needed at this scene."
        ),
        "intro_video": V["joyrides"],
        "ambient_video": V["elephants"],
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the wanderer has the mirror, the chest, AND the shield",
                "next_scene_id": "ending_triumphant",
            },
            {
                "condition": "the wanderer has at least one treasure but not all three",
                "next_scene_id": "ending_partial",
            },
            {
                "condition": "the wanderer has no treasures",
                "next_scene_id": "ending_empty_handed",
            },
        ],
    },
    # ---------- Terminal endings ----------
    {
        "id": "ending_triumphant",
        "title": "The new king",
        "narrative": (
            "You set the mirror, the chest, and the shield at the foot of the "
            "throne. The aging king closes his eyes, breath catching, and smiles. "
            "He names you his successor before the court. By the next morning he "
            "is gone, peacefully, and the crown is placed on your head. The kingdom "
            "begins to mend."
        ),
        "visual_description": (
            "The throne room at dawn the next day. The aging king's chair is empty "
            "and draped in white cloth. The three treasures sit on a low table "
            "before the throne, catching the morning light. The wanderer stands "
            "before the throne now, the crown on their head, the courtiers fuller "
            "in number and dressed in clean colors. Sun streams through repaired "
            "stained glass."
        ),
        "evaluation_context": "Terminal success ending.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "success",
        "transitions": [],
    },
    {
        "id": "ending_partial",
        "title": "A lesser inheritance",
        "narrative": (
            "You set down what you brought. The king nods slowly, neither pleased "
            "nor angry. The kingdom is still fragile, he says, but it will hold a "
            "while longer with what you've returned. He names you his successor "
            "all the same. When he passes you take the crown — but the kingdom "
            "remains uneasy, and you will spend years securing what was almost won."
        ),
        "visual_description": (
            "The throne room at evening. The wanderer kneels before the throne with "
            "some — but not all — of the treasures on the floor between them. The "
            "aging king's hand rests briefly on the wanderer's shoulder. Courtiers "
            "watch with mixed expressions. The light is overcast and the room feels "
            "cooler than the triumphant version."
        ),
        "evaluation_context": "Terminal partial ending.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "partial",
        "transitions": [],
    },
    {
        "id": "ending_empty_handed",
        "title": "The empty return",
        "narrative": (
            "You stand before the throne with nothing to lay at the king's feet. "
            "The king looks at you a long moment, then looks away. The court is "
            "silent. He waves you off without a word. You leave the throne room and "
            "the kingdom, and what happens to either is no longer your story to "
            "tell."
        ),
        "visual_description": (
            "The throne room at last light, almost dark. The wanderer stands before "
            "the throne empty-handed. The aging king has turned his face away. The "
            "courtiers look at the floor. The great doors are open behind the "
            "wanderer onto a darkening countryside."
        ),
        "evaluation_context": "Terminal failure ending — wanderer returned empty-handed.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "failure",
        "transitions": [],
    },
    {
        "id": "death_dragon",
        "title": "Smoke",
        "narrative": (
            "The dragon's eye opens slowly. It is the size of a shield, the color "
            "of an old gold coin. The well fills with heat. There is a small "
            "moment in which you understand, completely, what is about to happen. "
            "Then the moment ends."
        ),
        "visual_description": (
            "Tight on the dragon's opening eye, gold iris filling the frame. Cut "
            "to a wide shot of the well from above, smoke and red light pouring "
            "up out of the opening into the sky. Birds scatter from the trees "
            "around the clearing. The torches in the well are gone."
        ),
        "evaluation_context": "Terminal failure ending — wanderer was killed at the dragon's well.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "failure",
        "transitions": [],
    },
    {
        "id": "death_cliff",
        "title": "The long drop",
        "narrative": (
            "Your footing goes. There is no railing, no second chance, no slow "
            "rope to catch. The valley comes up to meet you with all the patience "
            "of stone."
        ),
        "visual_description": (
            "A figure falling silently against grey cliff and mist, getting smaller "
            "frame by frame. No music. The ledge above empty, wind pulling at "
            "nothing. The valley floor of slate and stunted pine waiting at the "
            "bottom of the shot."
        ),
        "evaluation_context": "Terminal failure ending — wanderer fell from the cliff path.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "failure",
        "transitions": [],
    },
    {
        "id": "death_witch",
        "title": "The cottage door",
        "narrative": (
            "The cottage door closes behind you and the bolt slides home. The "
            "witch's smile changes. The oven is very warm. The story you might "
            "have told ends here, in this small firelit room, on a quiet "
            "afternoon."
        ),
        "visual_description": (
            "Inside the cottage. The door has closed; an iron bolt is sliding "
            "into its catch. The witch in the foreground no longer smiling like a "
            "grandmother — eyes hard, mouth a thin line. The oven's open iron door "
            "fills the background, flames bright inside. Hanging herbs sway "
            "slightly. No exit visible."
        ),
        "evaluation_context": "Terminal failure ending — wanderer was caught by the witch.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "failure",
        "transitions": [],
    },
    {
        "id": "death_giant",
        "title": "Thunder",
        "narrative": (
            "The giant's eye opens. He sits up slowly, almost gently, like a man "
            "stretching after a nap. Then he looks down at you. His hand comes up. "
            "There is no run, no climb, no clever word that gets you back to the "
            "ladder in time."
        ),
        "visual_description": (
            "Tight on the giant's eye opening, then a slow pull back as he sits up "
            "against the oak. The shield falls flat into the cloud-grass. The "
            "wanderer is a small figure on the ground beneath the giant's "
            "shadow, looking up. Distant horizon of more cloud. The giant's hand "
            "begins to come down toward camera."
        ),
        "evaluation_context": "Terminal failure ending — wanderer woke the giant.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "failure",
        "transitions": [],
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
            " opening_scene_id, initial_world_state) "
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
                " intro_video, ambient_video, is_terminal, outcome) "
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

        scene_count = conn.execute("SELECT COUNT(*) FROM scenes").fetchone()[0]
        terminal_count = conn.execute(
            "SELECT COUNT(*) FROM scenes WHERE is_terminal = 1"
        ).fetchone()[0]
        transition_count = conn.execute(
            "SELECT COUNT(*) FROM transitions"
        ).fetchone()[0]
        print(f"Wrote {DB_PATH}")
        print(f"  scenes:           {scene_count}  ({terminal_count} terminal)")
        print(f"  transitions:      {transition_count}")
        print(f"  opening_scene_id: {EPISODE_META['opening_scene_id']}")
        print(f"  initial_world_state: {EPISODE_META['initial_world_state']}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
