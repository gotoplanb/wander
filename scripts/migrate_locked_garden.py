"""Seed `episodes/locked-garden/episode.sqlite`.

A Victorian-era locked-room mystery. The lady of an English country house
has vanished from her walled garden; the only entrance was locked from
the inside. The player is a friend of the family with a knack for puzzles,
summoned to look into it before the county police arrive.

Stresses the engine differently from kq1:
- Linear scene sequence (no death terminals on the puzzles)
- Six evidence flags gathered (or missed) across the middle scenes
- Final accusation scene with five transitions whose firing depends on
  BOTH the suspect named in the player's action AND how much evidence
  the player has gathered

Tests the new transition-declared state_delta system end to end.
Idempotent — drops and recreates the DB.
"""

import json
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
EPISODE_DIR = REPO_ROOT / "episodes" / "locked-garden"
DB_PATH = EPISODE_DIR / "episode.sqlite"

V = {
    "blazes": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
    "bunny": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
    "escapes": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
    "elephants": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
    "fun": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
    "joyrides": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4",
    "meltdowns": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerMeltdowns.mp4",
    "sintel": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4",
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
    "id": "locked-garden",
    "title": "The Locked Garden",
    "description": (
        "A Victorian-era country house mystery. The lady of the estate has "
        "vanished from her walled garden; the only entrance was locked from "
        "inside. Investigate, gather evidence, name the culprit."
    ),
    "version": "0.1.0",
    "author": "Dave Stanton",
    "world_constraints": (
        "An English country estate in the late 19th century. The player is an "
        "amateur investigator — observant, polite, has roughly an hour before "
        "the county constabulary arrives. Stay within Victorian propriety and "
        "the small world of the estate (drawing room, walled garden, study, "
        "servants' hall, family bedrooms). Three principal suspects: the "
        "husband (anxious, devoted), the brother (irritable, in debt to the "
        "lady), the gardener (silent, dutiful, no apparent motive). One of "
        "them did it. State flags track evidence the player gathers, and the "
        "final accusation scene branches on both the suspect named and the "
        "evidence in hand."
    ),
    "opening_scene_id": "arrival",
    "initial_world_state": {
        "saw_broken_trellis": False,
        "read_torn_letter": False,
        "noticed_timing_gap": False,
        "found_husbands_letter": False,
        "pressed_brother": False,
        "understood_mechanism": False,
    },
}


SCENES = [
    # ---------- 1. Arrival ----------
    {
        "id": "arrival",
        "title": "The drawing room",
        "narrative": (
            "You arrive at the estate by trap, summoned by a hurried note. The "
            "drawing room receives you stiffly. The husband — a man in his "
            "fifties, ash-pale — paces by the cold fireplace, working a "
            "handkerchief between his fingers. The brother stands by the tall "
            "window with a brandy glass already half emptied at eleven in the "
            "morning. A young maid stands rigid in the doorway behind you. On "
            "a low table: a woman's straw sun hat with a violet ribbon, the "
            "brim faintly muddied. The county constable, they tell you, is "
            "still an hour out from the village."
        ),
        "visual_description": (
            "A late-Victorian drawing room at mid-morning. Tall sash windows "
            "let in pale spring sun. Faded green silk wallpaper, framed "
            "engravings, a cold marble fireplace. Husband — fifties, "
            "moustached, grey at the temples — paces in front of it. Brother "
            "— thirty-ish, tweed, brandy in hand — stands at the window, "
            "facing out. A pale maid in black-and-white hovers in the open "
            "doorway. A straw sun hat with a violet ribbon lies on a marble-"
            "topped side table, brim slightly soiled."
        ),
        "evaluation_context": (
            "Setup scene. The player has just arrived and is taking the room "
            "in. Good judgment is to gather impressions before speaking — read "
            "the three figures' postures, look at the hat, listen for what "
            "the room itself tells you. Reasonable but flawed: open with "
            "questions to the husband or the brother. Common mistake: take "
            "charge as if you were already the police, demand statements, or "
            "ignore the family and rush straight to the garden. No state "
            "change at this scene — the only thing being gathered is footing."
        ),
        "intro_video": V["joyrides"],
        "ambient_video": V["meltdowns"],
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the player has taken the room in and is ready to investigate",
                "next_scene_id": "the_garden",
            },
        ],
    },
    # ---------- 2. The garden ----------
    {
        "id": "the_garden",
        "title": "The walled garden",
        "narrative": (
            "The maid leads you through the conservatory to a heavy iron gate. "
            "Beyond it: a small walled garden, perhaps thirty feet across. "
            "Pink roses on neat trellises along the walls. An apple tree in "
            "late flower at the far corner. A stone bench in the middle. The "
            "narrow gate by which you entered is the only opening. They tell "
            "you it was locked from the inside this morning — the housekeeper "
            "had to fetch the spare. Behind the apple tree, one of the trellis "
            "panels has come loose at the top and hangs at an angle. The soil "
            "in the bed below is dark from recent rain."
        ),
        "visual_description": (
            "A stone-walled garden in late morning. Walls twelve feet high, "
            "weathered brick, capped with stone. Pink and white roses on "
            "wood-lath trellises against three sides. A flowering apple tree "
            "at the back corner, blossoms pale. A small stone bench in the "
            "center of a gravel path. One trellis panel behind the apple tree "
            "has pulled away from the wall at the top and leans inward. Damp "
            "dark soil beneath. One narrow iron gate set into the side wall, "
            "currently standing open."
        ),
        "evaluation_context": (
            "The player must examine the apparent locked-room. The crucial "
            "physical evidence is the LEANING TRELLIS PANEL — it tells the "
            "player something or someone climbed it, but the direction of the "
            "stress (pulled from the inside vs from outside) tells different "
            "stories. Good judgment: examine the trellis CLOSELY (which way "
            "did it bend? — the answer is that it was pulled from inside, "
            "meaning whoever locked the gate then went out OVER the wall), "
            "look at the soil for prints, mark the position of the hat. "
            "Reasonable but flawed: walk the perimeter looking for an obvious "
            "exit (you'll find none — the wall is twelve feet). Common "
            "mistake: trample the soil getting to the bench, or wave the maid "
            "off and assume the obvious gate was used. The flag "
            "saw_broken_trellis becomes true ONLY on the correct close-"
            "examination transition (index 0)."
        ),
        "intro_video": V["escapes"],
        "ambient_video": V["sintel"],
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the player examines the trellis and soil closely and notes the direction of the pull",
                "next_scene_id": "the_study",
                "state_delta": {"saw_broken_trellis": True},
            },
            {
                "condition": "the player looks around but does not closely examine the trellis",
                "next_scene_id": "the_study",
            },
            {
                "condition": "the player tramples the scene or dismisses it as straightforward",
                "next_scene_id": "the_study",
            },
        ],
    },
    # ---------- 3. The study ----------
    {
        "id": "the_study",
        "title": "Her study",
        "narrative": (
            "The lady kept a small study on the ground floor — the husband "
            "shows you in apologetically. A writing desk, a fine green-shaded "
            "lamp, a glass-fronted bookcase. The desk is mostly tidy. The "
            "wastepaper basket beside it is not. In the basket: torn corners "
            "of a letter, the rest of the page missing. An appointment book "
            "lies open on the desk; today's date has a single line through "
            "it. A faint scent of violet water."
        ),
        "visual_description": (
            "A small study lit by a north-facing window. Walnut writing desk "
            "with a green-shaded oil lamp, blotter, inkwell. Glass-fronted "
            "bookcase of bound volumes in brown leather. A worn wicker "
            "wastepaper basket beside the desk. In it: scraps of cream "
            "writing paper torn in irregular pieces. An open appointment book "
            "on the desk, this morning's date crossed out with a single black "
            "line. Cut roses in a small glass jar on the windowsill, drooping."
        ),
        "evaluation_context": (
            "The study should yield ONE piece of evidence: the torn letter. "
            "Good judgment is to assemble the torn pieces — they reveal a "
            "drafted note to the brother demanding repayment of a substantial "
            "debt by the end of the week. Reasonable but flawed: look at the "
            "appointment book (interesting but already known — she had an "
            "appointment today). Common mistake: respect the lady's privacy "
            "and leave the wastepaper basket alone, or take the appointment "
            "book as the smoking gun. The flag read_torn_letter becomes true "
            "ONLY on the correct examine-the-torn-letter transition (index 0)."
        ),
        "intro_video": V["meltdowns"],
        "ambient_video": V["fun"],
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the player reconstructs the torn letter from the wastepaper basket",
                "next_scene_id": "the_servants",
                "state_delta": {"read_torn_letter": True},
            },
            {
                "condition": "the player reads the appointment book but leaves the basket",
                "next_scene_id": "the_servants",
            },
            {
                "condition": "the player respects the privacy of the room and looks only superficially",
                "next_scene_id": "the_servants",
            },
        ],
    },
    # ---------- 4. The servants' hall ----------
    {
        "id": "the_servants",
        "title": "The servants' hall",
        "narrative": (
            "The servants' hall, below stairs, is warm and smells of soap and "
            "stewed mutton. The cook keeps her hands in a pan of dishwater "
            "and refuses to look at you. The kitchen maid, the one who let "
            "you in, sits on a wooden chair with her hands in her lap. The "
            "housekeeper stands at the dresser, very still, watching. The "
            "gardener is not present — he is in the kitchen garden, they say. "
            "The county constable has not yet arrived."
        ),
        "visual_description": (
            "A low-ceilinged servants' hall lit by a small window high on the "
            "wall. A long scrubbed pine table, a few wooden chairs, a black "
            "iron range giving off a warm bake. Drying linen overhead. Cook — "
            "broad, fifties, apron — at the basin with her back half turned. "
            "Kitchen maid — seventeen, eyes red — sitting on a chair, hands "
            "folded. Housekeeper — black bombazine, sixty, immovable — by the "
            "dresser. The room smells of soap, mutton, and the iron."
        ),
        "evaluation_context": (
            "The player needs to find the TIMING GAP. The lady was last seen "
            "going into the garden after breakfast, about half past nine. The "
            "trellis was discovered at about ten. The brother claims he was "
            "in the library reading the whole morning. The kitchen maid will "
            "say, if asked carefully and not in front of the housekeeper, "
            "that she took tea up to the library at half past nine and the "
            "brother was not there. Good judgment: ask the maid alone, "
            "without the housekeeper looming, when she last saw or served "
            "each person. Reasonable but flawed: ask the housekeeper, who is "
            "loyal and will give a clean composite account that hides the "
            "gap. Common mistake: confront them all together and demand "
            "alibis, or fail to ask about the brother at all. The flag "
            "noticed_timing_gap becomes true ONLY on the correct ask-the-"
            "maid-alone transition (index 0)."
        ),
        "intro_video": V["meltdowns"],
        "ambient_video": V["bunny"],
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the player gets the maid alone and asks specifically about the brother's morning",
                "next_scene_id": "the_husbands_room",
                "state_delta": {"noticed_timing_gap": True},
            },
            {
                "condition": "the player questions the housekeeper or asks the group generally",
                "next_scene_id": "the_husbands_room",
            },
            {
                "condition": "the player is brusque and they all close ranks",
                "next_scene_id": "the_husbands_room",
            },
        ],
    },
    # ---------- 5. The husband's room ----------
    {
        "id": "the_husbands_room",
        "title": "The husband's dressing room",
        "narrative": (
            "The husband, distracted, lets you into his dressing room when "
            "asked, then waits awkwardly in the hall. A washstand. A wardrobe "
            "with the doors a little open. A small writing slope on the chest "
            "of drawers — his, by the look of it, not hers. A leather card "
            "case, a few opened envelopes, a half-written letter abandoned. "
            "His suit of the morning hangs over a chair, the cuffs faintly "
            "damp."
        ),
        "visual_description": (
            "A man's dressing room in muted greens and brown. A washstand "
            "with a porcelain jug. A heavy wardrobe of dark wood. A leather "
            "card case and a few unfolded letters on top of a writing slope. "
            "A grey morning suit hangs over the back of a wooden chair — the "
            "cuffs and hems slightly darkened by damp. A faint smell of his "
            "shaving soap."
        ),
        "evaluation_context": (
            "The husband's room offers TWO data points. The damp cuffs and "
            "hems show he was in the garden some time after the rain (not "
            "suspicious — the rose beds are his — but worth noting). The "
            "writing slope holds a letter HE was drafting to his solicitor: "
            "an attempt to renegotiate the terms of the lady's life insurance "
            "policy, which were unfavorable to him on her death. THAT is the "
            "exonerating evidence — he had reason to want her alive, not "
            "dead. Good judgment: read the unfinished letter on the writing "
            "slope, note the insurance detail. Reasonable but flawed: examine "
            "the morning suit and conclude the husband is the obvious "
            "suspect. Common mistake: feel embarrassed and leave without "
            "really looking. The flag found_husbands_letter becomes true ONLY on "
            "the correct read-the-letter transition (index 0) — it both "
            "exonerates the husband AND establishes the brother's motive "
            "(the brother's debt was to the lady, not to him)."
        ),
        "intro_video": V["fun"],
        "ambient_video": V["meltdowns"],
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the player reads the husband's unfinished letter on the writing slope",
                "next_scene_id": "the_brother",
                "state_delta": {"found_husbands_letter": True},
            },
            {
                "condition": "the player examines the damp morning suit and forms suspicions of the husband",
                "next_scene_id": "the_brother",
            },
            {
                "condition": "the player feels intrusive and leaves the room quickly",
                "next_scene_id": "the_brother",
            },
        ],
    },
    # ---------- 6. The brother ----------
    {
        "id": "the_brother",
        "title": "The brother",
        "narrative": (
            "You find the brother in the library, no longer affecting calm. "
            "The brandy glass is empty. He is at the long bookcase with his "
            "back to the door, and turns when you enter. He says, before you "
            "can speak, that he was here all morning. He does not ask after "
            "his sister. He does not ask what you have found. He waits."
        ),
        "visual_description": (
            "A modest library — three walls of books in brown and dark green "
            "bindings, a heavy mahogany table, a single brass lamp lit "
            "despite the daylight. The brother — thirty, sharp-featured, "
            "tweed jacket — stands at the bookcase, one hand resting on the "
            "shelf. His empty brandy glass sits on the table behind him. He "
            "looks at the player evenly. The room smells of cigar smoke and "
            "old paper."
        ),
        "evaluation_context": (
            "The brother is the one who did it. He is brittle and waiting to "
            "see what the player has. Good judgment is to push him on the "
            "specifics — what was he reading? where was he at half past "
            "nine? did he speak with his sister this morning about the debt? "
            "— and watch for him going pale, particularly on the timing "
            "question. Reasonable but flawed: tell him sympathetically you "
            "have a few questions and let him talk (he will fill the silence "
            "with a smooth, prepared account). Common mistake: accuse him "
            "outright with no evidence — he will close down, deny "
            "everything, and the encounter is wasted. The flag "
            "pressed_brother becomes true ONLY on the correct specific-"
            "pressure transition (index 0)."
        ),
        "intro_video": V["sintel"],
        "ambient_video": V["bunny"],
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the player asks specific, hard questions and watches the brother go pale on the timing",
                "next_scene_id": "the_mechanism",
                "state_delta": {"pressed_brother": True},
            },
            {
                "condition": "the player is sympathetic and lets the brother give a smooth, prepared account",
                "next_scene_id": "the_mechanism",
            },
            {
                "condition": "the player accuses outright and the brother shuts down",
                "next_scene_id": "the_mechanism",
            },
        ],
    },
    # ---------- 7. The mechanism ----------
    {
        "id": "the_mechanism",
        "title": "The mechanism",
        "narrative": (
            "You go back to the gate. The lock itself is a heavy iron drop-"
            "bar on the inside — no key, no keyhole through to the outside. "
            "The wall around the gate is twelve feet of brick. You stand and "
            "look at it. The trellis behind the apple tree is in your line "
            "of sight. The housekeeper hovers a respectful distance away, "
            "watching."
        ),
        "visual_description": (
            "Close on the iron drop-bar mechanism on the inside of the gate — "
            "a simple hinge, no outside access. Pull back to the garden: the "
            "player standing in the gravel, looking from the gate toward the "
            "apple tree across the garden. The leaning trellis is visible "
            "behind the tree. Twelve-foot wall capped in stone. The "
            "housekeeper in the conservatory doorway, hands folded."
        ),
        "evaluation_context": (
            "This is the SOLVE moment. The gate locks only from inside. The "
            "wall is twelve feet. The trellis is leaned against the wall — "
            "it would NOT support a person climbing OUT, but it would "
            "support someone CLIMBING FROM A LADDER STANDING IN THE GARDEN, "
            "using the trellis only as the last reach. Good judgment is to "
            "reason through this: someone in the garden locked the gate, "
            "used the trellis as the final handhold to get over the wall, "
            "and pulled it slightly outward in doing so. That someone "
            "removed the lady (or the lady's body) over the wall on a ladder "
            "kept on the outside. The brother grew up here and would know "
            "every wall and trellis. Reasonable but flawed: conclude the "
            "lock was tampered with from outside (it cannot be). Common "
            "mistake: give up and say it must have been someone with a key "
            "(there is no key). The flag understood_mechanism becomes true "
            "ONLY on the correct figure-out-the-climb transition (index 0)."
        ),
        "intro_video": V["escapes"],
        "ambient_video": V["sintel"],
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the player works out the trellis-as-final-handhold escape from inside",
                "next_scene_id": "the_accusation",
                "state_delta": {"understood_mechanism": True},
            },
            {
                "condition": "the player concludes the lock must have been tampered with from outside",
                "next_scene_id": "the_accusation",
            },
            {
                "condition": "the player gives up and goes to the drawing room without an answer",
                "next_scene_id": "the_accusation",
            },
        ],
    },
    # ---------- 8. The accusation ----------
    {
        "id": "the_accusation",
        "title": "The accusation",
        "narrative": (
            "The constable's trap rolls up the drive — you can hear the "
            "wheels on the gravel from the drawing room. The husband and the "
            "brother are both there. The housekeeper waits at the door, "
            "watching you. There is, perhaps, two minutes before the door "
            "opens and the case becomes someone else's. You stand before the "
            "fireplace. They look at you. They wait to hear what you have."
        ),
        "visual_description": (
            "The drawing room again, now late morning, the light slightly "
            "harder. Husband on the settee, hands together between his "
            "knees, watching the player. Brother in an armchair, leg crossed "
            "over the other, brandy glass refilled and untouched. "
            "Housekeeper in the doorway, hands folded. Through the tall "
            "window: a horse and trap turning into the gravel drive, the "
            "blue-coated figure of the county constable visible on the "
            "bench. The fireplace cold, the mantelpiece clock at five past "
            "the hour."
        ),
        "evaluation_context": (
            "Final scene. The player names a suspect (or declines to). The "
            "transition to fire depends on BOTH the suspect named in the "
            "player's action AND the world state — count the true evidence "
            "flags in WORLD STATE (saw_broken_trellis, read_torn_letter, "
            "noticed_timing_gap, found_husbands_letter, pressed_brother, "
            "understood_mechanism). The brother is the actual culprit. "
            "Decision rules:\n"
            "- If the player names the BROTHER and 4 or more flags are "
            "true: pick transition 0 (the solid case).\n"
            "- If the player names the BROTHER and 1-3 flags are true: pick "
            "transition 1 (the weak case — the player is right but the "
            "constable will not be convinced).\n"
            "- If the player names the HUSBAND (any evidence): pick "
            "transition 2 (the wrong suspect; the husband had reason to "
            "want her alive).\n"
            "- If the player names the GARDENER (any evidence): pick "
            "transition 3 (the easy outsider — wrong).\n"
            "- If the player declines to accuse, says they need more time, "
            "or names nobody: pick transition 4 (the case will be left to "
            "the constable; ambiguous).\n"
            "The verdict can reflect the dignity of how the player presents "
            "(good = clear and respectful, partial = hedged, poor = "
            "blustering), but the transition is state-and-suspect-driven. "
            "No state_delta is needed at this scene — the engine handles "
            "transition state deltas, and the endings need no flags set."
        ),
        "intro_video": V["joyrides"],
        "ambient_video": V["meltdowns"],
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the player names the brother with substantial evidence (4+ flags true)",
                "next_scene_id": "ending_correct_solid",
            },
            {
                "condition": "the player names the brother with thin evidence (1-3 flags true)",
                "next_scene_id": "ending_correct_weak",
            },
            {
                "condition": "the player names the husband",
                "next_scene_id": "ending_wrong_husband",
            },
            {
                "condition": "the player names the gardener",
                "next_scene_id": "ending_wrong_gardener",
            },
            {
                "condition": "the player declines to name anyone or asks for more time",
                "next_scene_id": "ending_unsolved",
            },
        ],
    },
    # ---------- Terminal endings ----------
    {
        "id": "ending_correct_solid",
        "title": "The constable's notebook",
        "narrative": (
            "You lay it out for the constable as he arrives — torn letter, "
            "timing, debt, trellis, the climb. He listens without writing at "
            "first, then begins to write quickly. The brother says nothing. "
            "By afternoon he is in the constable's trap on the way to the "
            "village lock-up. The husband shakes your hand at the door, "
            "thinly, but holds it longer than he means to. The county papers "
            "name you within the week."
        ),
        "visual_description": (
            "The drawing room slightly later. The constable in his blue coat "
            "writing into a small black notebook at the table, the player "
            "speaking quietly across from him. The brother behind them on the "
            "settee, looking at the carpet. The husband by the window, "
            "shoulders down, watching the garden. Pale afternoon light. The "
            "case closed cleanly."
        ),
        "evaluation_context": "Terminal ending — correct accusation, solid evidence.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "success",
        "transitions": [],
    },
    {
        "id": "ending_correct_weak",
        "title": "Without proof",
        "narrative": (
            "You name the brother. The constable hears you, but he hears "
            "what you have and what you don't have. He nods politely. The "
            "brother is questioned and released within the day. There will "
            "be no charge. Within a month he is gone abroad — Italy, they "
            "say, the lakes — and the case stays open and quiet. You were "
            "right, you know. So does he. So does the housekeeper. It is "
            "not the same as proving it."
        ),
        "visual_description": (
            "The drawing room at full noon, the constable already gone. The "
            "brother adjusting his cuffs at the window, almost amused. The "
            "husband sitting very still on the settee. The player at the "
            "fireplace. The light too bright, the silence too long. The "
            "housekeeper in the doorway, eyes on the player only."
        ),
        "evaluation_context": "Terminal ending — correct suspect, insufficient evidence.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "partial",
        "transitions": [],
    },
    {
        "id": "ending_wrong_husband",
        "title": "The wrong man",
        "narrative": (
            "You name the husband. The constable takes the accusation "
            "seriously. The husband is questioned, weeps, is held overnight, "
            "and released the next morning when the brother — looking "
            "carefully sympathetic — produces the husband's draft letter to "
            "the solicitor about the life insurance. The case is closed by "
            "the constable as a tragic disappearance, foul play uncertain. "
            "The brother inherits within the year. You are not invited back."
        ),
        "visual_description": (
            "The drawing room late afternoon, after. The husband seated on "
            "the settee, hollow, head in his hand. The brother by the "
            "fireplace, quietly satisfied. The housekeeper not looking at "
            "anyone. The player standing at the doorway with their hat in "
            "their hand, no longer welcome. Cold light through the window."
        ),
        "evaluation_context": "Terminal ending — wrong suspect (husband). Failure.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "failure",
        "transitions": [],
    },
    {
        "id": "ending_wrong_gardener",
        "title": "The convenient man",
        "narrative": (
            "You name the gardener. The constable is grateful — it is a "
            "tidy answer. The gardener, a man who has worked the grounds "
            "for thirty years and never raised his voice, is taken away "
            "without protest. The brother sees the constable to the door "
            "and shakes his hand. The case is closed by the next afternoon. "
            "You go home. Some nights the housekeeper's silence comes back "
            "to you, and you wonder what she would have said if you had "
            "asked her the right question."
        ),
        "visual_description": (
            "The walled garden empty now, the gate hanging open. The "
            "gardener's leather gloves left on the stone bench. The "
            "constable in the conservatory door, hat in hand, speaking to "
            "the brother. The housekeeper in the kitchen window, watching, "
            "saying nothing."
        ),
        "evaluation_context": "Terminal ending — wrong suspect (gardener, the easy outsider). Failure.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "failure",
        "transitions": [],
    },
    {
        "id": "ending_unsolved",
        "title": "The constable's case",
        "narrative": (
            "You tell the constable you are not yet ready to name anyone. "
            "He looks at you for a moment, nods, and goes to do his own "
            "work. The case slides slowly out of your hands. He concludes "
            "in his official report that the lady left of her own accord. "
            "The household keeps its silences. The brother stays in the "
            "library with his brandy. The husband ages five years in two "
            "months. There is, in the end, no answer that anyone speaks aloud."
        ),
        "visual_description": (
            "The drawing room in deepening afternoon. The constable's hat "
            "and notebook on the table — he has gone home. The husband at "
            "the window with his back to the room. The brother nowhere. "
            "The player still at the fireplace, alone. The sun hat still on "
            "the marble side table where it was that morning."
        ),
        "evaluation_context": "Terminal ending — case unsolved. Partial.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "partial",
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
        stateful_transition_count = conn.execute(
            "SELECT COUNT(*) FROM transitions WHERE state_delta != '{}'"
        ).fetchone()[0]
        print(f"Wrote {DB_PATH}")
        print(f"  scenes:                {scene_count}  ({terminal_count} terminal)")
        print(f"  transitions:           {transition_count}")
        print(f"  stateful transitions:  {stateful_transition_count}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
