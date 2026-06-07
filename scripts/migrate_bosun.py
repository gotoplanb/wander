"""Seed `episodes/bosun/episode.sqlite`.

A pirate episode. The captain of a small armed ship has died of fever off
the Windward Islands in 1684. The player is the ship's bosun and next in
line. Authority, the Account, a sealed chart, a Spanish sail on the
horizon, a buried cache, a long return voyage with gold under every
bunk, and a free-port harbor that will or will not give them a captain's
chair.

Public-domain Golden Age of Piracy tropes only — no characters or plot
beats borrowed from existing works. Generic role names (the bosun, the
boatswain, the cook, the gunner, the captain) and a fictional ship
(the Margaret-Ann).

Stresses the engine:
- 8 active scenes, 5 terminal endings (1 mid-voyage death, 1 mid-voyage
  marooning, 3 state-driven endings at the harbor).
- 6 boolean state flags applied via transition-declared state_delta.
- Final scene branches on state AND player action.

Idempotent — drops and recreates the DB.
"""

import json
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
EPISODE_DIR = REPO_ROOT / "episodes" / "bosun"
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
    "id": "bosun",
    "title": "The Bosun's Account",
    "description": (
        "The captain of a small armed sloop has died of fever off the Windward "
        "Islands. You are the bosun, next in line. There is a chart, a Spanish "
        "sail on the horizon, a cache to dig up, gold to divide, and a long "
        "voyage home. Lead them well and the harbor gives you a captain's "
        "chair."
    ),
    "version": "0.1.0",
    "author": "Dave Stanton",
    "world_constraints": (
        "Setting: the Caribbean in 1684, aboard the small armed sloop "
        "Margaret-Ann, somewhere off the Windward Islands. Public-domain Golden "
        "Age of Piracy tropes only — the Account (ship's articles), shares of "
        "prizes, marooning, the dead captain, a sealed chart, a Spanish sail on "
        "the horizon, a free port that asks no questions if the manifest is "
        "tidy. The PLAYER is the ship's bosun — second-in-command after the "
        "captain, NOT the captain's relative, NOT a passenger, NOT a "
        "guest. The bosun has been with the ship for years and knows every "
        "man aboard by name. The captain has just died of fever; the first "
        "mate was landed sick at the last port. The bosun is therefore next in "
        "line. Other crew positions named in the episode: boatswain, cook, "
        "gunner, lookout — these are generic roles, not characters with "
        "biographies. Do NOT invent additional plot characters (a daughter, a "
        "lover, a brother-officer) — keep the story to the crew and what the "
        "world places in front of them. Player actions should fit a 17th-"
        "century mariner with authority — reading the Account, plotting a "
        "course, dividing a prize, judging the wind. Reject actions that "
        "invoke modern technology or magic."
    ),
    "opening_scene_id": "the_captain_dies",
    "initial_world_state": {
        "crew_respect": False,
        "has_chart": False,
        "avoided_spanish": False,
        "recovered_treasure": False,
        "shared_take": False,
        "no_mutiny": False,
    },
}


SCENES = [
    # ---------- 1. The captain dies ----------
    {
        "id": "the_captain_dies",
        "title": "The captain's cabin",
        "narrative": (
            "Captain Greaves died this morning, between four bells and six, of "
            "the fever that took half of Saint-Pierre last month. You stood at "
            "the bunk with him to the end. Now the cabin door is closed and you "
            "are alone with what he left — a sea-chest, a brass-bound writing "
            "slope, a chart wrapped in oilskin half tucked under the cot, and a "
            "small key on a leather cord around his neck. Above you on the main "
            "deck, you can hear the crew not speaking. The first mate was put "
            "ashore sick at the last port. You are the bosun, and you are next."
        ),
        "visual_description": (
            "A small captain's cabin lit by a swinging brass lamp, late morning, "
            "the air still and stale. The dead captain lies on the cot under a "
            "thin grey blanket, hand fallen to the deck. A sea-chest with iron "
            "bands at the foot of the cot. A walnut writing slope on the table. "
            "An oilskin-wrapped roll just visible under the cot. A small brass "
            "key on a leather thong around the dead man's neck. Through the "
            "stern window: open blue Caribbean, a single low cloud line. The "
            "cabin door closed, the muffled sound of a quiet, watching crew "
            "above."
        ),
        "evaluation_context": (
            "The opening. The player must establish authority and order before "
            "touching anything in the cabin. Good judgment: step out to the "
            "deck FIRST, name the captain's death to the crew plainly, call a "
            "muster for the Account to be read, then come back to deal with the "
            "cabin. Reasonable but flawed: secure the cabin door and inventory "
            "it now — sensible but reads to the crew like greed when the news "
            "of the death is still spreading. Common mistake: take the key from "
            "around the captain's neck before announcing anything (a watching "
            "hand will see and it becomes a story). No state change at this "
            "scene; only the player's tone matters."
        ),
        "intro_video": V["meltdowns"],
        "ambient_video": V["sintel"],
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the bosun goes to the deck to face the crew and call the Account",
                "next_scene_id": "the_account",
            },
        ],
    },
    # ---------- 2. The Account ----------
    {
        "id": "the_account",
        "title": "The Account read",
        "narrative": (
            "The crew gathers around the forecastle in the heat of midday. "
            "Eighteen men, the cook and boatswain among them. The Account — the "
            "ship's articles — sits in your hand, the captain's seal still on "
            "the wax. By the Account, the captain's share goes to the next in "
            "line if the first mate is absent. That is you. The men know this. "
            "The men are watching to see if YOU know it. The boatswain — a hard "
            "man named Doyle — stands with his arms crossed and his weight on "
            "the back of his heel."
        ),
        "visual_description": (
            "The forecastle at noon. Sunlight harsh, the deck planks bleached. "
            "The bosun (the player) standing on the half-deck above the men, "
            "the sealed Account in their hand. Eighteen sailors below, in worn "
            "linen shirts, sashes, headcloths — a few smoking clay pipes. "
            "Doyle, the boatswain, broad-shouldered and shaven-skulled, stands "
            "front and center, arms folded across his chest, weight back. The "
            "cook — wiry, sun-blackened — leans against the foremast. The blue "
            "Caribbean horizon all around."
        ),
        "evaluation_context": (
            "Critical scene for crew_respect. The bosun must read the Account "
            "straight, including the unflattering part where the captain's "
            "share becomes the bosun's by right. Good judgment: break the seal "
            "openly, read every line without skipping the bosun's-share "
            "clause, then ASK the crew if any man disputes it. Refusing to "
            "duck the awkward bit earns Doyle's grudging respect and the "
            "crew's. Reasonable but flawed: read the Account but quietly skip "
            "or soften the bosun's-share clause, hoping no one notices (Doyle "
            "notices). Common mistake: defer to Doyle to read it (he will and "
            "the crew will follow him after this), or claim the captain's share "
            "without reading at all (mutiny by sundown). The flag crew_respect "
            "becomes true ONLY on the read-it-straight transition (index 0)."
        ),
        "intro_video": V["joyrides"],
        "ambient_video": V["fun"],
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the bosun reads the Account straight, names their own share, and asks for any dispute",
                "next_scene_id": "the_chart",
                "state_delta": {"crew_respect": True},
            },
            {
                "condition": "the bosun reads the Account but softens the inconvenient parts",
                "next_scene_id": "the_chart",
            },
            {
                "condition": "the bosun hands the Account to Doyle or claims the share without ceremony",
                "next_scene_id": "the_chart",
            },
        ],
    },
    # ---------- 3. The chart ----------
    {
        "id": "the_chart",
        "title": "The chart",
        "narrative": (
            "Back in the cabin with two witnesses — the cook and Doyle, by your "
            "choice — you take the key from the captain's neck and open the "
            "sea-chest. Two pistols, a bag of shot, a small purse of Spanish "
            "silver, papers in a leather wallet, and the oilskin-wrapped roll "
            "from under the cot. Inside the oilskin: a chart, hand-drawn but "
            "skilled, of a cove the captain never spoke of. A single mark in "
            "old Castilian: 'Aquí.' Here. The wind and your current position "
            "place it perhaps three days' sail south by south-east."
        ),
        "visual_description": (
            "The captain's cabin, now open and aired, late afternoon light "
            "through the stern window. The sea-chest open at the foot of the "
            "cot, its contents laid out on the cot's blanket: two flintlock "
            "pistols, a small leather purse, a stack of folded papers, a bone-"
            "handled clasp knife. Spread on the table under the brass lamp: a "
            "hand-drawn chart on heavy paper, edges browned, showing a small "
            "crescent cove and a notation in faded ink. The cook and the "
            "boatswain Doyle stand to either side, watching the bosun (the "
            "player) plot a course over the chart with a brass divider."
        ),
        "evaluation_context": (
            "Good judgment: open the chest WITH WITNESSES present (the cook "
            "and Doyle by the player's choice or by the player calling them "
            "in), mark the chart's existence in the ship's log, plot the "
            "course to the cove openly. The witness rule is the bosun "
            "establishing that nothing was palmed in private; the log entry "
            "protects the bosun later. Reasonable but flawed: open the chest "
            "alone, find the chart, then announce only that there is a course "
            "to set without explaining why (the crew will fill the silence "
            "with rumors of treasure that may grow in the telling). Common "
            "mistake: open the chest alone and palm the chart to read later, "
            "telling no one (Doyle will know — he counts the chest's contents "
            "before the captain dies, every captain knows this is done). The "
            "flag has_chart becomes true ONLY on the with-witnesses-and-log "
            "transition (index 0)."
        ),
        "intro_video": V["bunny"],
        "ambient_video": V["elephants"],
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the bosun opens the chest with witnesses, logs the chart, plots the course openly",
                "next_scene_id": "the_spanish_sail",
                "state_delta": {"has_chart": True},
            },
            {
                "condition": "the bosun opens the chest alone but announces a heading without the chart's source",
                "next_scene_id": "the_spanish_sail",
            },
            {
                "condition": "the bosun palms the chart in private and tells no one",
                "next_scene_id": "the_spanish_sail",
            },
        ],
    },
    # ---------- 4. The Spanish sail ----------
    {
        "id": "the_spanish_sail",
        "title": "Sail on the horizon",
        "narrative": (
            "Third day out. The lookout calls down: a sail. Two sails. A heavy "
            "Spanish merchantman riding low — fat with cargo — and at three "
            "cables' distance behind her, a frigate of the line under Spanish "
            "colors. They have not seen the Margaret-Ann yet; you are in the "
            "merchantman's blind quarter and the wind is yours. Doyle waits at "
            "your shoulder. The cook, behind him, says nothing. The whole crew "
            "is on the deck looking at you."
        ),
        "visual_description": (
            "Bright Caribbean noon, deep blue water under a small breeze. The "
            "Margaret-Ann from her own deck — a small armed sloop, twelve guns. "
            "On the horizon over the bowsprit: a heavy three-masted Spanish "
            "merchantman in cream and red, and behind her a sleek warship — a "
            "fifth-rate frigate — with Spanish colors snapping at the mizzen. "
            "Sails and water and very little else. The bosun (the player) at "
            "the rail with a glass, Doyle at their shoulder, the cook a step "
            "back. The crew lined along the rail, watching."
        ),
        "evaluation_context": (
            "Player chooses the response. Good judgment is sober avoidance: "
            "change course south, lose them in the current that runs along "
            "the leeward side of Saint-Vincent, stay focused on the cove. The "
            "frigate's guns would punch through the Margaret-Ann at half a "
            "league. Reasonable but flawed: shadow the merchantman at extreme "
            "range hoping the frigate breaks off (it won't — Spanish "
            "merchantmen are escorted to port for a reason). Common mistake "
            "that ends the quest: order the attack on the merchantman with "
            "the frigate within range. The Margaret-Ann is fast but not that "
            "fast. The flag avoided_spanish becomes true ONLY on the change-"
            "course transition (index 0)."
        ),
        "intro_video": V["blazes"],
        "ambient_video": V["escapes"],
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the bosun changes course south to lose them in the current",
                "next_scene_id": "the_cove",
                "state_delta": {"avoided_spanish": True},
            },
            {
                "condition": "the bosun shadows the merchantman at distance hoping the frigate breaks off",
                "next_scene_id": "the_cove",
            },
            {
                "condition": "the bosun orders the attack with the frigate in range",
                "next_scene_id": "ending_sunk",
            },
        ],
    },
    # ---------- 5. The cove ----------
    {
        "id": "the_cove",
        "title": "The cove",
        "narrative": (
            "The cove on the chart is real. You land at first light — yourself, "
            "Doyle, the cook, four men, and the longboat. The marking on the "
            "chart, translated by the cook from the old Castilian, reads: "
            "'From the mouth of the dead palm, fifteen paces along the line of "
            "the sun at noon, then dig ten paces deep beneath the white "
            "stones.' But there is no standing dead palm. There is a young palm "
            "in flower at the inland edge of the beach — and behind it, half "
            "in the sand, the hollow stump of one long since fallen. White "
            "stones could mean the shells scattered on the high-tide line. Or "
            "they could mean a small outcrop of limestone visible inland past "
            "the young palm. The cook waits to be told which to dig."
        ),
        "visual_description": (
            "Tropical morning on a small crescent beach of pale sand. Aquamarine "
            "water inside the cove, deeper blue beyond. A young palm in flower "
            "at the back of the beach. Behind it, in the sand, the broken "
            "hollow stump of an older palm long fallen. Further inland past the "
            "young palm, a small outcrop of white limestone rising out of the "
            "scrub. Scattered white shells along the high-tide line. The "
            "longboat pulled up on the sand. The cook (wiry, sun-blackened) "
            "with a spade. Doyle (broad, shaven-skulled) with another. The "
            "bosun (the player) holding the chart in the morning light."
        ),
        "evaluation_context": (
            "A puzzle scene. The DEAD palm is what matters — its stump is "
            "still visible behind the young one. 'Line of the sun at noon' "
            "means north (the sun's track at this latitude in summer). White "
            "stones cannot mean shells in old Castilian — the Spaniard would "
            "have called shells conchas, not piedras. The limestone is the "
            "white stones. Good judgment: stand at the stump, walk fifteen "
            "paces inland (north), dig at the limestone outcrop. Reasonable "
            "but flawed: try the beach shells first (you'll find nothing but "
            "wet sand and the day will pass). Common mistake: dig at the "
            "BASE OF THE YOUNG PALM (treating it as the palm in the chart — "
            "you'll bring it down with no cache to show for it). The flag "
            "recovered_treasure becomes true ONLY on the stump-and-limestone "
            "transition (index 0)."
        ),
        "intro_video": V["fun"],
        "ambient_video": V["bunny"],
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the bosun reasons the dead palm is the stump and digs at the limestone",
                "next_scene_id": "the_division",
                "state_delta": {"recovered_treasure": True},
            },
            {
                "condition": "the bosun tries the beach shells first and the day runs out",
                "next_scene_id": "the_division",
            },
            {
                "condition": "the bosun digs at the base of the young palm",
                "next_scene_id": "the_division",
            },
        ],
    },
    # ---------- 6. The division ----------
    {
        "id": "the_division",
        "title": "The take",
        "narrative": (
            "Whatever you found — much, little, or nothing but sand — must now "
            "be answered for. The crew waits on the beach, in a loose half-"
            "circle around the cook and Doyle. If you found the cache, the "
            "chest is open between you. If you did not, your hands are empty "
            "and the silence is louder. Either way the men want to know what "
            "comes next, and they want to hear it from you."
        ),
        "visual_description": (
            "Afternoon, the same beach. The crew in a loose semicircle on the "
            "sand. In the middle: an open iron-bound chest with what was found "
            "in it (or an empty hole and a spade resting in the sand). The "
            "bosun standing at the chest, the chart loose in their hand. Doyle "
            "with his arms crossed at the bosun's right shoulder. The cook to "
            "the left, quieter than usual. The sun slanting low over the "
            "leeward water."
        ),
        "evaluation_context": (
            "Player decides how to divide the take (or how to handle empty-"
            "handedness). Good judgment: divide by the Account on the beach, "
            "openly, every man counted, the dead captain's share marked aside "
            "for his widow at port, the bosun's-and-officer's shares marked "
            "openly. If the cache is empty, announce it plainly and the share "
            "of nothing is nothing — no man can complain of a fair zero. "
            "Reasonable but flawed: order the take returned to the ship to be "
            "divided 'properly' at sea (looks like skimming, even if you "
            "wouldn't). Common mistake: claim a captain's share for yourself "
            "before the crew has voted you in (mutiny at sea will follow). The "
            "flag shared_take becomes true ONLY on the divide-on-the-beach-by-"
            "the-Account transition (index 0)."
        ),
        "intro_video": V["meltdowns"],
        "ambient_video": V["sintel"],
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the bosun divides openly on the beach by the Account, with the dead captain's share marked",
                "next_scene_id": "the_return",
                "state_delta": {"shared_take": True},
            },
            {
                "condition": "the bosun orders the take returned to the ship to be divided at sea",
                "next_scene_id": "the_return",
            },
            {
                "condition": "the bosun claims a captain's share without the crew's vote",
                "next_scene_id": "the_return",
            },
        ],
    },
    # ---------- 7. The return ----------
    {
        "id": "the_return",
        "title": "The long return",
        "narrative": (
            "Twelve days back to the free port. Every man knows what is in his "
            "sea-chest below. Some sleep on theirs. The cook has gone quiet — "
            "you have not heard him sing his evening song in three nights. On "
            "the fourth night out from the cove, on your watch, you come round "
            "the galley and find one of the gun crew — a young Cornish hand "
            "named Treve — standing at the magazine door with his hand on the "
            "bolt and his eye on the dark passage behind him. He sees you and "
            "freezes."
        ),
        "visual_description": (
            "Below decks, late night, a single oil lamp swinging at the end "
            "of the galley passage. The magazine door at the end, iron-banded. "
            "Treve — slight, twenty-two, dirty-blond, in only his shirt and "
            "breeches — frozen with one hand on the door bolt and the other "
            "near a folded piece of canvas held against his chest. He looks at "
            "the bosun over his shoulder, white-eyed. The ship creaks slowly "
            "around them. From higher up, the slow swing of a hammock."
        ),
        "evaluation_context": (
            "Player handles the magazine incident. Treve is not attempting "
            "mutiny — he is afraid his own sea-chest will be robbed by another "
            "hand in the night, and the magazine has a lock he thought he "
            "could share. Good judgment: take him aside, get the truth from "
            "him without raising his voice or yours, set up a sleeping rota "
            "for the gold sea-chests that the whole crew will trust (one "
            "watchman from each watch, rotated). Reasonable but flawed: ignore "
            "the incident as one nervous man's foolishness — Treve will be "
            "found by Doyle the next night and the story will spread badly. "
            "Common mistake that ends the quest in marooning: clap Treve in "
            "irons and announce it to the crew at dawn as an example. The "
            "other gun crew will not stand for it; they will rise that night. "
            "The flag no_mutiny becomes true ONLY on the handle-with-steady-"
            "authority transition (index 0)."
        ),
        "intro_video": V["sintel"],
        "ambient_video": V["elephants"],
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the bosun handles Treve steadily, gets the truth, sets a watch rota the crew trusts",
                "next_scene_id": "the_free_port",
                "state_delta": {"no_mutiny": True},
            },
            {
                "condition": "the bosun lets it pass and hopes for the best",
                "next_scene_id": "the_free_port",
            },
            {
                "condition": "the bosun clamps Treve in irons and announces him as an example",
                "next_scene_id": "ending_marooned",
            },
        ],
    },
    # ---------- 8. The free port ----------
    {
        "id": "the_free_port",
        "title": "The free port",
        "narrative": (
            "On the twelfth morning, the harbor opens to leeward — a small "
            "free port that asks no questions if the manifest is tidy. The "
            "harbor master will row out at noon to log the ship, name the "
            "captain in his book, take his fee. The crew is on deck, looking "
            "at you. They will follow you ashore as their captain. Or they "
            "will not. There is, at most, a quarter of an hour before the "
            "harbor master's boat is in pistol-shot."
        ),
        "visual_description": (
            "Late morning. The Margaret-Ann at anchor in the outer roads of a "
            "small Caribbean free port — a half-circle of wooden buildings, "
            "tile-roofed warehouses, a small fort with no flag flying. Other "
            "ships at anchor: a Dutch trader, a small French sloop. A red "
            "longboat coming out from the dock with five men in it — the "
            "harbor master and four hands. On the deck of the Margaret-Ann, "
            "the bosun stands at the rail. Doyle behind them. The cook a few "
            "paces back. The crew lined along the deck, every face turned "
            "toward the bosun. The blue water, the wooden harbor, the open "
            "morning."
        ),
        "evaluation_context": (
            "FINAL SCENE. The transition fired depends on BOTH the action the "
            "player names AND the world state. Count the true flags in WORLD "
            "STATE: crew_respect, has_chart, avoided_spanish, recovered_"
            "treasure, shared_take, no_mutiny. The decision rules are:\n"
            "- If the player names self as captain to the harbor master AND "
            "5 or more flags are true: pick transition 0 (the captain's "
            "chair).\n"
            "- If the player names self as captain AND 3 or 4 flags are "
            "true: pick transition 1 (accepted but conditional — partial).\n"
            "- If crew_respect is FALSE (the bosun lost the crew at the "
            "Account read at the very start): pick transition 2 (the crew "
            "trades you to the harbor master for amnesty — hung).\n"
            "- If the player asks the crew to elect a captain or declines "
            "to take the chair: pick transition 3 (the quiet share — "
            "partial).\n"
            "- If the player tries to abscond with the take in the longboat: "
            "pick transition 4 (the crew shoots you from the deck — the "
            "captain's chair was within reach and you chose this).\n"
            "Verdict reflects the dignity of the player's choice (good = "
            "clear and respectful of the crew, partial = hedged, poor = "
            "self-dealing), but the transition is state-and-action-driven. "
            "No state_delta is needed at this scene."
        ),
        "intro_video": V["joyrides"],
        "ambient_video": V["fun"],
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the player names self as captain with 5+ flags true (the crew is solidly with them)",
                "next_scene_id": "ending_captains_chair",
            },
            {
                "condition": "the player names self as captain with 3 or 4 flags true (accepted but on conditions)",
                "next_scene_id": "ending_quiet_share",
            },
            {
                "condition": "crew_respect is false — the crew gives the bosun up to the harbor master",
                "next_scene_id": "ending_hung",
            },
            {
                "condition": "the player declines to take the chair and asks the crew to elect",
                "next_scene_id": "ending_quiet_share",
            },
            {
                "condition": "the player tries to abscond with the take in the longboat",
                "next_scene_id": "ending_shot_from_the_deck",
            },
        ],
    },
    # ---------- Terminal endings ----------
    {
        "id": "ending_captains_chair",
        "title": "The captain's chair",
        "narrative": (
            "The harbor master comes aboard, looks at you, looks at the crew "
            "lined behind you, opens his book. 'Captain?' he says. You say "
            "your name. Doyle, behind you, says nothing — which is the loudest "
            "thing he could say. The harbor master writes it down and takes "
            "his fee from the purse you offer him. Within the week the ship "
            "is yours by right, the dead captain's widow is found and paid in "
            "Saint-Pierre by the cook, and the crew that came back with you "
            "will sail under you on the next voyage. The Margaret-Ann has a "
            "captain again. He is you."
        ),
        "visual_description": (
            "The deck of the Margaret-Ann at midday. The harbor master in a "
            "rumpled blue coat at a small table with his open book, writing. "
            "The bosun — now the captain — stands at his elbow. Doyle on the "
            "captain's right hand, the cook on the left. The crew behind "
            "them, in good order, in their best linen. The pier in the "
            "background, sun bright on white-painted warehouses. A small "
            "Spanish flag in the harbor — peaceful, distant."
        ),
        "evaluation_context": "Terminal ending — captain's chair earned cleanly.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "success",
        "transitions": [],
    },
    {
        "id": "ending_quiet_share",
        "title": "The quiet share",
        "narrative": (
            "The crew gives you the chair, but not as a unanimous voice — "
            "some hands first, then the rest. The harbor master writes your "
            "name without ceremony. The ship is yours for this voyage and "
            "perhaps the next, but the bosun's table you keep below shows "
            "the rota you watched yourself sleep against, and the boatswain "
            "Doyle, when he looks at you, looks at you as a man who will "
            "have to keep proving it. The take is divided, the dead captain's "
            "widow is paid, the crew scatters into the port. You hold the "
            "ship. You do not yet hold the chair."
        ),
        "visual_description": (
            "The deck at evening. The harbor master gone, his name in the "
            "book. The crew breaking up into small groups, men shouldering "
            "their kits and going ashore. The bosun-now-captain at the rail "
            "looking at the lit harbor, alone. Doyle a few paces away, "
            "looking at the same harbor, not at the bosun. The Margaret-Ann's "
            "deck nearly empty."
        ),
        "evaluation_context": "Terminal ending — partial. Survived with the ship, no glory.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "partial",
        "transitions": [],
    },
    {
        "id": "ending_hung",
        "title": "The harbor master's book",
        "narrative": (
            "Doyle speaks first. He says you took the captain's share against "
            "the Account and that the crew never agreed. The harbor master "
            "looks at Doyle and looks at the crew and writes Doyle's name in "
            "his book. He looks at you only when he calls for the irons. There "
            "is no fight to make. By sundown you are in the port's small jail "
            "above the harbor. The county takes a fortnight to hang a man for "
            "piracy in this town. They are unhurried. The Margaret-Ann sails "
            "without you under her new captain."
        ),
        "visual_description": (
            "The deck in the moment of arrest. Two of the harbor master's men "
            "stepping toward the bosun. Doyle a step back, expression flat. "
            "The crew not looking at the bosun. The harbor master closing his "
            "book. Cut to: the small white-walled jail above the harbor, a "
            "single barred window, the harbor visible in the distance. The "
            "Margaret-Ann at anchor, made small by the angle, with another "
            "man's flag at her mizzen."
        ),
        "evaluation_context": "Terminal failure — crew turned at port because the bosun lost their respect early.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "failure",
        "transitions": [],
    },
    {
        "id": "ending_shot_from_the_deck",
        "title": "The longboat",
        "narrative": (
            "You make it as far as the longboat with the cook's purse and "
            "your own and the captain's share. You make it as far as ten "
            "yards of water between your boat and the Margaret-Ann's hull. "
            "Doyle does not raise his voice. He raises a musket. The captain's "
            "chair was within a quarter-hour's reach and you chose this. The "
            "harbor master, watching from his own boat, makes no move to row "
            "in either direction. He waits to see who he will be writing into "
            "his book."
        ),
        "visual_description": (
            "The longboat in the water between the Margaret-Ann and the "
            "shore, the bosun at the oars with three purses at their feet. "
            "On the deck of the Margaret-Ann, Doyle at the rail with a long "
            "musket levelled, expression utterly steady. The cook behind him "
            "looking away. The harbor master's boat a hundred yards off, "
            "stopped, the harbor master with his book held closed against "
            "his chest. Open blue water all around."
        ),
        "evaluation_context": "Terminal failure — self-dealing within sight of the chair.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "failure",
        "transitions": [],
    },
    {
        "id": "ending_marooned",
        "title": "The sandbar",
        "narrative": (
            "The gun crew rises in the dawn watch with the men of the larboard "
            "watch behind them. There is a brief fight on the main deck. Doyle "
            "fights for you and against you both, in the way Doyle does, until "
            "he sees which way the deck will go. By midmorning the longboat is "
            "in the water and you and what they consider your party — the cook, "
            "two men who would not turn — are in it, with three days of water "
            "and no firearms. They have left you in sight of a small sandbar "
            "off the Grenadines. The Margaret-Ann sails on without you. The "
            "cook does not look at you. The two men row."
        ),
        "visual_description": (
            "Bright morning sea, a small longboat low in the water with four "
            "men in it — the bosun in the stern, the cook in the middle, two "
            "young hands at the oars. In the middle distance, a small low "
            "sandbar with two stunted palms. In the further distance, the "
            "stern of the Margaret-Ann sailing away under full canvas, a "
            "small black figure (Doyle) visible at her stern rail, watching."
        ),
        "evaluation_context": "Terminal failure — mid-voyage marooning after botched discipline.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "failure",
        "transitions": [],
    },
    {
        "id": "ending_sunk",
        "title": "Two broadsides",
        "narrative": (
            "The frigate does what a frigate does. Her first broadside "
            "passes high; her second does not. The Margaret-Ann goes down "
            "in fifteen minutes by the boatswain's pocket watch, which is "
            "found in the wreckage a month later by Spanish fishermen. The "
            "merchantman reaches port the next afternoon. Her captain is "
            "commended in dispatches. The chart, the Account, the cook, "
            "Doyle, every man of the eighteen, and the bosun are all at "
            "the bottom of the leeward channel before nightfall."
        ),
        "visual_description": (
            "Two ships at close action — the small sloop Margaret-Ann under "
            "fire from the larger Spanish frigate, masts cracking. Smoke, "
            "splintering wood, fire taking the foresail. Cut to: the same "
            "stretch of sea an hour later, only the masthead of the "
            "Margaret-Ann showing above water, the merchantman sailing on "
            "untouched in the middle distance under the frigate's protection."
        ),
        "evaluation_context": "Terminal failure — fought the frigate's escort, the ship was sunk.",
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
