"""Seed `episodes/salvage-run/episode.sqlite`.

A sci-fi comedy episode in the Sierra register. The player is a third-shift
waste reclamation tech on the freighter Brackish, far out in the Outer Lanes.
The shift lead — the player's only friend on this ship — has gone missing on
a "contract recovery" for Lardner-Voss Synergistics, and a small black data
crystal has turned up in the morning's muck-screen catch that should not be
there.

Original characters, original locations, original prose. The Sierra register
borrowed only in tone and pacing: a snarky-but-matter-of-fact narrator, a
low-status protagonist in a grubby practical near-future, absurd corporate
villainy treated as the weather. No characters or plot beats lifted from any
existing work.

Stresses the engine:
- 8 active scenes, 6 terminal endings (3 mid-flow failures, 3 state-driven
  endings at the docking strut).
- 7 boolean state flags applied via transition-declared state_delta.
- Final scene branches on state AND player action.

Idempotent — drops and recreates the DB.
"""

import json
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
EPISODE_DIR = REPO_ROOT / "episodes" / "salvage-run"
DB_PATH = EPISODE_DIR / "episode.sqlite"


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
    "id": "salvage-run",
    "title": "Salvage Run",
    "description": (
        "Your shift lead is missing and there is a data crystal in the morning's "
        "muck-screen catch that should not be there. The corporate compliance "
        "office has her. Get to her before her file is closed."
    ),
    "version": "0.1.0",
    "author": "Dave Stanton",
    "world_constraints": (
        "Setting: the Outer Lanes, a grubby practical near-future of "
        "decommissioned mining haulers, refueling moons, and 24-hour fuel-and-"
        "food franchises. No magic, no faster-than-light wizardry, no godlike "
        "AI, no time travel. Tools are practical — multitools, vacsuit patch "
        "kits, magstrip locks, datapads, encryption keys, escape pods on half-"
        "charge.\n\n"
        "The PLAYER is a third-shift waste reclamation tech on the freighter "
        "Brackish — the rec-tech. Their job is sorting and cleaning what comes "
        "up in the muck-screen catch. They are NOT an officer, NOT a "
        "passenger, NOT a relative of anyone in the story, NOT a corporate "
        "plant. They are low-status crew with a steady wage and a small "
        "shared bunk. They are good at their job, quiet, and have no leverage "
        "over anyone except the friend they are about to look for.\n\n"
        "Named characters and what they are:\n"
        "- Shift Lead Manda Korth: the player's direct supervisor on the "
        "Brackish's reclamation deck for the last two cycles. SHE/HER pronouns "
        "throughout. She is the player's ONLY personal connection on this "
        "ship. She is not the player's relative, not their romantic interest "
        "— she is the boss who taught them the job and trusted them with her "
        "console password. She is currently missing on a Lardner-Voss "
        "compliance summons.\n"
        "- Foreman Olm: deck foreman of the Brackish. A company man — corporate "
        "compliance's eyes on this deck. He/him. Treat him as an antagonist.\n"
        "- Tem: night clerk at Lubricasso's, a 24-hour fuel-and-food franchise "
        "on a refueling moon. They/them. Owes Korth a favor. Just a clerk — "
        "not a relative, not a romantic interest.\n"
        "- Vex Brindle: regional compliance officer for Lardner-Voss "
        "Synergistics. He/him. The antagonist. A corporate manager with a "
        "quota for 'recovered assets,' not a personal enemy.\n\n"
        "Locations: the Brackish's reclamation bay, an escape pod, the "
        "Threnody Drift (an asteroid graveyard of dead mining haulers), "
        "Lubricasso's (a fuel-and-food diner on a refueling moon), the LVS "
        "Compliance Tower (a brutalist regional office on the same moon), "
        "the Tower's docking strut.\n\n"
        "Tone: matter-of-fact narrator, dry workplace humor, no fourth-wall "
        "breaks. The world treats corporate weaponization of compliance law "
        "as the normal weather, not as a punchline. Humor lives in small "
        "specific details — diner menu items, bureaucratic phrasing, the "
        "wrong things being more reliable than the right things — not in the "
        "narrator winking at the player.\n\n"
        "Do NOT invent additional plot characters: no sibling on the ship, no "
        "old flame at the diner, no child waiting at port, no secret partner. "
        "The cast above is the cast.\n\n"
        "Reject actions that invoke magic, telepathy, instant teleport, or "
        "any technology the world has not established. The player's leverage "
        "is observation, patience, and the trust of one person."
    ),
    "opening_scene_id": "the_bilge",
    "initial_world_state": {
        "has_crystal": False,
        "read_log": False,
        "carries_multitool": False,
        "knows_lvs": False,
        "has_clearance": False,
        "read_archive": False,
        "trust_korth": False,
    },
}


SCENES = [
    # ---------- 1. The bilge ----------
    {
        "id": "the_bilge",
        "title": "Muck-screen catch",
        "narrative": (
            "Shift turnover bell rang twenty-two minutes ago and Shift Lead "
            "Korth still hasn't come down to sign off. The reclamation bay "
            "smells the way it always does — coolant, rust, the burnt-rubber "
            "tang of yesterday's seal jobs. Her console is unlocked the way "
            "she always leaves it for you. Her duffel hook by the door is "
            "empty. On the muck-screen above tank three, the morning's catch "
            "is laid out for you to sort: the usual broken handcuffs, a snapped "
            "tool handle, two dead datapads — and one small black data crystal, "
            "thumbnail-sized, with the wrong color of casing for company stock. "
            "Foreman Olm is one deck up doing the maintenance walk. He'll be "
            "down here in maybe ten minutes."
        ),
        "visual_description": (
            "Low industrial bay, fluorescent panels harsh and yellowed. "
            "Concrete-grey floor with iron gratings. Tank three is a wide "
            "stainless basin holding a wet pile of compressed sludge studded "
            "with metal junk. On the muck-screen — a polished steel sorting "
            "bed beside the tank — a layer of recovered detritus: tangled "
            "wiring, broken handcuffs, a snapped tool handle, two dead "
            "datapads, and a small black data crystal the size of a thumbnail "
            "with a non-standard violet casing. Korth's console at the back "
            "of the bay, screen glowing, swivel chair empty. The work-duffel "
            "hook on the wall by the door, empty. The whole bay otherwise "
            "still — no shift partner, no foreman, no second sound. A faint "
            "rhythmic clang from somewhere above: Olm on the walk."
        ),
        "evaluation_context": (
            "The opening. Korth is missing — that's the hook — but the more "
            "immediate problem is the crystal. The wrong-color casing means "
            "it isn't company stock; if Olm sees it on the screen the rec-"
            "tech is implicated in something they don't yet understand. Good "
            "judgment: pocket the crystal quickly, sort the rest of the catch "
            "normally so the muck-screen looks worked, sit down at Korth's "
            "console and check her last-clocked-out timestamp. Reasonable "
            "but flawed: pocket the crystal but don't bother to fake the "
            "sort — Olm will notice an unworked muck-screen on his walk and "
            "ask questions, no flag set. Common mistake: report the crystal "
            "and the missing shift lead up the chain to Foreman Olm. The "
            "Brackish foreman is corporate compliance's eyes on this deck; "
            "by next shift the rec-tech will be on a recovery list. Same next "
            "scene; the player just no longer has the crystal. Transition 0 "
            "(pocket and cover, then check console) sets has_crystal=True. "
            "Transitions 1 and 2 do not set the flag."
        ),
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the rec-tech pockets the crystal, works the rest of the catch as cover, then goes to Korth's console",
                "next_scene_id": "the_console",
                "state_delta": {"has_crystal": True},
            },
            {
                "condition": "the rec-tech pockets the crystal but leaves the muck-screen unsorted and walks to the console",
                "next_scene_id": "the_console",
            },
            {
                "condition": "the rec-tech reports the crystal and the missing shift lead to Foreman Olm",
                "next_scene_id": "the_console",
            },
        ],
    },
    # ---------- 2. The console ----------
    {
        "id": "the_console",
        "title": "Korth's console",
        "narrative": (
            "Korth's console is unlocked. Last clock-out: two days ago, "
            "twenty-one-thirty ship time. She hasn't been in this chair in "
            "forty-six hours. There is a slot on the side of the console "
            "that takes a data crystal. If you have the crystal, it fits. "
            "The screen wakes to a personal-log prompt encrypted with a key "
            "Korth made you set up two cycles ago, the morning she stopped "
            "trusting the foreman. The last entry is from the night she "
            "didn't come back. 'Brindle's office in the Tower. Two-day "
            "summons, voluntary, with my arm twisted. If I don't make the "
            "third morning, the crystal stays with you. Find Tem at "
            "Lubricasso's — night clerk, debt to me they will honor. The "
            "pod manifest below is fueled for one and pre-cleared. Don't "
            "tell Olm.' Attached: a half-charged escape pod's manifest, "
            "and the pod number — pod 4."
        ),
        "visual_description": (
            "The console nook at the back of the reclamation bay. A worn "
            "swivel chair pushed back at an angle. The console screen lit "
            "cool grey, showing a text-heavy log entry with a small inset "
            "diagram of an escape pod and a pod number. The slot on the "
            "side of the console with the violet crystal inserted, a tiny "
            "violet pinpoint indicator showing engagement. The rec-tech's "
            "own datapad on the console ledge, screen dark, ready. On the "
            "wall above: a faded company-standard motivational poster "
            "(SAFE HANDS HONEST SHIFT). The bay otherwise empty. The clang "
            "from above has stopped — Olm has finished the walk."
        ),
        "evaluation_context": (
            "Korth's log is a one-shot — once the crystal is pulled and the "
            "console clears the buffer, the entry is gone unless the rec-tech "
            "has copied it. Good judgment: decrypt and read the entry, copy "
            "the entry AND the pod manifest to the rec-tech's own datapad "
            "so the original crystal can be hidden somewhere safer than a "
            "pocket, then wipe the console history. The copy is the "
            "insurance: if the crystal is later searched off them, the "
            "datapad still has the record; if the datapad is searched, the "
            "crystal is safe. Reasonable but flawed: decrypt and read but "
            "make no copy, leaving Korth's whole testimony as one fragile "
            "object — workable but a single point of failure. Common mistake: "
            "decrypt and immediately open ship's-comms to ask if anyone has "
            "seen Korth in the last two days. Olm hears that and pod 4 will "
            "not be there when the rec-tech arrives at the launch deck. "
            "Transition 0 (read AND copy) sets read_log=True. Transitions 1 "
            "and 2 do not set the flag. All three lead to the_drift; the "
            "no-flag case just means the player is going in with one bad "
            "outage away from no proof at all."
        ),
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the rec-tech reads the log AND copies entry and manifest to their datapad before wiping the console",
                "next_scene_id": "the_drift",
                "state_delta": {"read_log": True},
            },
            {
                "condition": "the rec-tech reads the log but does not make a copy",
                "next_scene_id": "the_drift",
            },
            {
                "condition": "the rec-tech reads the log and opens ship's comms asking after Korth",
                "next_scene_id": "the_drift",
            },
        ],
    },
    # ---------- 3. The drift ----------
    {
        "id": "the_drift",
        "title": "The Threnody Drift",
        "narrative": (
            "Pod 4 casts off the Brackish's launch deck at twenty-two-fifteen. "
            "By twenty-three-thirty you are inside the Threnody Drift — fifty "
            "thousand cubic kilometers of dead mining haulers from the last "
            "bust, none of them lit, all of them slowly tumbling. The pod's "
            "fuel gauge reads half. Lubricasso's is six hours of burn away on "
            "a straight line. You have enough fuel for four. The pod's "
            "salvage clamp is operational. Within close drift: the husk of "
            "the JSV-Vanette, a mid-tonnage hauler, lights out for at least "
            "a decade. Her aux fuel tanks are almost certainly dry by now. "
            "Her tool lockers very probably are not. Her bulk lock has a "
            "wreck-beacon on tamper. Her auxiliary lock does not."
        ),
        "visual_description": (
            "Interior of a small two-seat escape pod, the rec-tech alone in "
            "the pilot's couch. Through the forward port: the Threnody Drift "
            "— a slow, silent field of derelict mining haulers, their hulls "
            "dust-grey and matte, no running lights anywhere, drifting in a "
            "slow tumble against a black starfield. The JSV-Vanette directly "
            "ahead at maybe three hundred meters: a battered cylindrical "
            "hauler with peeling reg-numbers, two visible airlocks (a large "
            "bulk lock at midship, a smaller auxiliary lock at the stern), "
            "panels of her hull plating scored from old micrometeor hits. "
            "On the pod's instrument cluster: fuel gauge at fifty percent, "
            "amber. The salvage clamp arm visible to the pod's right, folded."
        ),
        "evaluation_context": (
            "Resource problem. The pod cannot reach Lubricasso's on fifty "
            "percent fuel, and there are no friendly stations between here "
            "and there. Good judgment: dock with the Vanette at the "
            "AUXILIARY lock (bulk lock will set off a wreck-beacon and "
            "every salvage skiff in the Drift will roll over to investigate), "
            "board the wreck in a vacsuit, strip the tool locker for a "
            "multitool and a vacsuit patch kit, push off, burn for the "
            "franchise. Set carries_multitool. Reasonable but flawed: skip "
            "the salvage and burn hot to make Lubricasso's on what you have. "
            "Pod will arrive on fumes; the diner does not refuel pods on "
            "credit; you may have to abandon the pod in the parking shoal — "
            "workable but you'll be on foot and you don't have the tools. "
            "Common mistake: broadcast distress and wait for traffic. The "
            "Brackish would respond first because they are the closest legal "
            "operator, and Olm's people will be on pod 4 inside an hour. "
            "Transition 2 leads to ending_drifted — the player waits, no one "
            "civilian comes, the pod's life support eventually runs down. "
            "Transition 0 sets carries_multitool=True. Transition 1 does "
            "not."
        ),
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the rec-tech docks with the Vanette at the auxiliary lock, strips the tool locker, and burns for the franchise",
                "next_scene_id": "the_franchise",
                "state_delta": {"carries_multitool": True},
            },
            {
                "condition": "the rec-tech skips the salvage and burns hot on what fuel they have",
                "next_scene_id": "the_franchise",
            },
            {
                "condition": "the rec-tech broadcasts distress and waits for traffic",
                "next_scene_id": "ending_drifted",
            },
        ],
    },
    # ---------- 4. The franchise ----------
    {
        "id": "the_franchise",
        "title": "Lubricasso's at three in the morning",
        "narrative": (
            "Lubricasso's main floor at zero-three-twelve ship-equivalent is "
            "a single counter, six bolted-down stools, and a clock above the "
            "register that no longer agrees with the rest of the building. "
            "The smell of long-boiled coffee. The night clerk behind the "
            "counter is Tem — thin, twenty-something, asleep on their own "
            "elbow under a backlit menu sign that reads NUTRIENTS, FUELS, "
            "CONVERSATIONS in three colors. Three other customers: two "
            "haulers in matching grey corp coveralls in the corner booth, "
            "neither eating; one woman alone at the far end of the counter "
            "reading a private screen with the polarizer up so you can't "
            "see what's on it. The employee-only door is behind the counter, "
            "to Tem's left, secured with a magstrip lock."
        ),
        "visual_description": (
            "Interior of a 24-hour diner on a refueling moon, deep night. "
            "Long counter with six chrome-and-vinyl bolted stools, a "
            "backlit menu sign in three colors, a tired chrome coffee urn. "
            "Tem behind the counter — thin, late twenties, dark hair tied "
            "back, in a yellow Lubricasso's jacket, asleep face down on "
            "their forearm with a stylus still loose in their hand. Two "
            "haulers in matching grey corporate coveralls in the corner "
            "booth, hands flat on the table, not eating, not talking, "
            "watching the door. A woman at the far end of the counter "
            "alone, dark coat, reading a small screen with a polarizing "
            "film tilted away from the room. The employee-only door behind "
            "the counter is steel, with a flat magstrip lock at hip height. "
            "Outside the front window: a low parking shoal under floodlights, "
            "a few small shuttles."
        ),
        "evaluation_context": (
            "Social puzzle. The information the player needs lives with Tem. "
            "The two haulers are corp informants by trade — haulers in "
            "matching coveralls in a Lubricasso's at three in the morning "
            "are paid to watch the door, not to eat. Good judgment: order "
            "something cheap, wait quietly for Tem to wake, name Korth and "
            "ask after them by their debt. Tem will tell the rec-tech that "
            "Korth was in three days ago, met a man in an LVS-internal-"
            "green coat, left in a hover-shuttle pointed at the Compliance "
            "Tower. Set knows_lvs=True. The reveal is the corporate name and "
            "the Tower as the destination — without it the rec-tech has "
            "nowhere to go next. Reasonable but flawed: try the magstrip "
            "lock on the employee-only door while Tem sleeps. The lock "
            "will open with a multitool but the door leads only to a break "
            "room and a back loading dock; nothing useful inside, and the "
            "haulers see the break-in. No flag. Common mistake: approach "
            "the haulers directly to ask if they've seen Korth. They will "
            "say no, then they will follow the rec-tech to whatever pod or "
            "shuttle they came in. Transition 2 leads to ending_arrested — "
            "LVS compliance officers meet the player at the Tower's docking "
            "strut before the player gets out of the airlock. Transition 0 "
            "sets knows_lvs=True. Transition 1 does not."
        ),
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the rec-tech orders something cheap, waits for Tem to wake, and names Korth's debt",
                "next_scene_id": "the_tower",
                "state_delta": {"knows_lvs": True},
            },
            {
                "condition": "the rec-tech tries the magstrip lock on the employee-only door while Tem sleeps",
                "next_scene_id": "the_tower",
            },
            {
                "condition": "the rec-tech approaches the two haulers in coveralls and asks if they've seen Korth",
                "next_scene_id": "ending_arrested",
            },
        ],
    },
    # ---------- 5. The Tower ----------
    {
        "id": "the_tower",
        "title": "The Compliance Tower lobby",
        "narrative": (
            "You leave the pod in the Tower's outer parking shoal. Before you "
            "cross the docking strut into the lobby you stash the crystal and "
            "your datapad in the pod's tool-locker — anything you carry into "
            "an LVS building becomes discoverable, and Korth's whole point "
            "in keeping the crystal off the Brackish was to keep it off LVS "
            "premises full stop. You go in with empty pockets and the case "
            "file memorized.\n\n"
            "The Lardner-Voss Compliance Tower is a brutalist concrete cube "
            "thirty stories on a side, on the night side of the moon, lit "
            "white at the corners. The main lobby is at street level: a "
            "polished black floor, a long curved reception desk staffed by "
            "one woman in an LVS-internal-green blazer, a small wall plaque "
            "behind her that reads COMPLIANCE IS YOUR RIGHT AND OURS, and "
            "two security gates flanking a bank of elevators. The directory "
            "lists Vex Brindle, Regional Compliance, on the twenty-eighth "
            "floor. The receptionist looks up when you come in. There is a "
            "service corridor visible through a half-glassed door to the "
            "left of the desk; a maintenance hand in coveralls just walked "
            "out of it with a clipboard."
        ),
        "visual_description": (
            "Interior of a brutalist office lobby, late night, lit cool "
            "white. Polished black stone floor, ceilings high and grey. A "
            "long curved blonde-wood reception desk centered, behind it a "
            "woman in her forties in a tailored LVS-internal-green blazer "
            "and white blouse, hair short and neat. On the wall behind her: "
            "a brushed-aluminum plaque reading COMPLIANCE IS YOUR RIGHT AND "
            "OURS in clean letters. Two security gates flanking a bank of "
            "three elevators. A half-glassed door to the left of the desk "
            "labeled SERVICE; through it a long beige corridor. A maintenance "
            "hand in olive coveralls is just stepping out of the service door "
            "with a clipboard. The rec-tech (the player) standing just inside "
            "the front entrance, in their reclamation-deck work clothes — "
            "grimy and obviously out of place."
        ),
        "evaluation_context": (
            "Infiltration puzzle. The good path depends on which flag the "
            "player carries. If the player has knows_lvs (knows Korth's "
            "compliance officer is named Vex Brindle on the twenty-eighth "
            "floor), the receptionist can be talked past with the right "
            "specific request — 'Vex Brindle, twenty-eighth, I'm here for "
            "Korth' is processed because that's exactly the kind of vague-"
            "but-specific the receptionist sees forty times a day. Set "
            "has_clearance=True. If the player has carries_multitool but "
            "NOT knows_lvs, the SERVICE corridor is the path — the magstrip "
            "lock at the far end of the corridor opens to a maintenance "
            "stair that climbs the back of the building, set has_clearance=True. "
            "Either flag-driven approach is index 0. Reasonable but flawed: "
            "approach the desk without naming Brindle ('I'm here to see "
            "someone in compliance'). The receptionist will direct the rec-"
            "tech to a public-facing intake form and a waiting bench; the "
            "rec-tech can sit there until shift change and slip past during "
            "the changeover — no flag, but the next scene is still reachable. "
            "Common mistake: try to bluff past one of the two security "
            "gates without any flag. Transition 2 leads to ending_arrested. "
            "Transition 0 fires if has_clearance becomes True (either path "
            "above qualifies). Transition 1 if neither flag-driven path is "
            "viable but the player waits patiently."
        ),
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the rec-tech uses knows_lvs to name Brindle to the receptionist, OR uses carries_multitool to take the service corridor",
                "next_scene_id": "the_archive",
                "state_delta": {"has_clearance": True},
            },
            {
                "condition": "the rec-tech approaches the desk vaguely and waits on the intake bench for a shift change",
                "next_scene_id": "the_archive",
            },
            {
                "condition": "the rec-tech tries to bluff past a security gate with no flag-supported approach",
                "next_scene_id": "ending_arrested",
            },
        ],
    },
    # ---------- 6. The archive ----------
    {
        "id": "the_archive",
        "title": "The compliance archive",
        "narrative": (
            "Twenty-eighth floor, west wing, the records suite. After-hours "
            "lighting: half the panels off, the rest at twenty percent. "
            "Rows of black file cabinets and a single low desk with three "
            "terminals, two of them off, the third logged in as an "
            "ARCHIVIST-TIER user whoever it is went home without locking. "
            "On the terminal's index, under recent: Korth, Manda — case "
            "open, status REVIEW PENDING, location HOLDING 28-N, no scheduled "
            "release. There is an export option marked CASE PACKET (PDF) "
            "and there is an audit alarm at the lower right that goes off "
            "if anything is exported without ticket authorization. The "
            "datapad in the rec-tech's pocket has a port that matches the "
            "terminal's side jack."
        ),
        "visual_description": (
            "Interior of an office archive after hours, lighting dim. Rows "
            "of black metal file cabinets, narrow aisles. A low desk in the "
            "open area with three flat-screen terminals; two are dark, the "
            "central one is lit, showing a case-file viewport in a "
            "compliance application's interface. The screen displays a case "
            "header KORTH, MANDA / REVIEW PENDING / HOLDING 28-N in clean "
            "sans-serif. At the lower right of the screen, a small amber "
            "icon labeled AUDIT, indicating an alarm tier. The archivist's "
            "chair is empty and pushed back at an angle. A coffee mug "
            "still warm on a coaster. The rec-tech standing at the desk, "
            "their datapad in one hand, the side port visible. The whole "
            "wing otherwise silent."
        ),
        "evaluation_context": (
            "Stealth puzzle. Good judgment: do not use the export option — "
            "it trips the audit alarm. Instead, screen-cap the case header "
            "and the holding location to the datapad directly through the "
            "side jack (it's a hardware port; reading from it does not "
            "leave a log because the terminal sees it as a peripheral, not "
            "an export). Note that HOLDING 28-N is on the same floor, east "
            "wing. Set read_archive=True. Reasonable but flawed: use the "
            "EXPORT CASE PACKET button. The audit alarm goes off but the "
            "PDF does export to the datapad first — the rec-tech has a "
            "complete case packet (no flag), but now has six to nine "
            "minutes before security walks the floor; the next scene is "
            "still reachable if the player moves immediately. Common "
            "mistake: read the case on the terminal but do not capture it "
            "anywhere. The player will know where Korth is but will arrive "
            "at the next scene with no evidence of what was done to her — "
            "no flag, same target. All three transitions lead to the_review_"
            "room. Only transition 0 sets read_archive=True."
        ),
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the rec-tech screen-caps to the datapad through the side jack without using the export button",
                "next_scene_id": "the_review_room",
                "state_delta": {"read_archive": True},
            },
            {
                "condition": "the rec-tech uses the EXPORT CASE PACKET button, getting the PDF but tripping the audit alarm",
                "next_scene_id": "the_review_room",
            },
            {
                "condition": "the rec-tech reads the case on the terminal but captures nothing",
                "next_scene_id": "the_review_room",
            },
        ],
    },
    # ---------- 7. The review room ----------
    {
        "id": "the_review_room",
        "title": "Holding 28-N",
        "narrative": (
            "Holding 28-N is a small carpeted room with one window onto the "
            "moon's night sky and one steel door. Korth is sitting at the "
            "interview table in the same shirt she was wearing two days ago. "
            "She looks up when the door opens. Whatever she expected when "
            "the lock turned, it wasn't you. The first thing she says is "
            "quiet: 'Did you bring the crystal in here.' Brindle is not in "
            "the room — there is a coat over the chair across from her, "
            "LVS-internal green, and a half-finished cup of water. He'll "
            "be back in a few minutes."
        ),
        "visual_description": (
            "Interior of a small compliance interview room. Carpet a muted "
            "grey-blue. One window taking up the long wall, showing the "
            "moon's black night sky and a few distant stars. One small "
            "rectangular interview table, two chairs. Korth at the table — "
            "fortyish, hair longer than at the start of the trip, tired, in "
            "a wrinkled olive shirt, no restraints, a paper cup of water in "
            "front of her. The chair opposite her holds a folded LVS-"
            "internal-green coat and another paper cup, half full. The rec-"
            "tech (the player) standing just inside the steel door, hand "
            "still on the handle. Korth looking up at the rec-tech with an "
            "expression that has not yet decided what to feel."
        ),
        "evaluation_context": (
            "Moral / trust puzzle. Korth's question — 'Did you bring the "
            "crystal in here' — is the test. She is asking whether her "
            "rec-tech understands why she ran the crystal off the ship in "
            "the first place: because once it's on LVS premises it becomes "
            "discoverable evidence in Brindle's case against HER, not against "
            "Brindle. The rec-tech HAS stashed the crystal and the datapad "
            "copy in the pod before crossing the strut (see the_tower); the "
            "good answer is the literal truth. Good judgment: confirm to her "
            "that the crystal and the datapad copy are in the pod, that the "
            "rec-tech walked in with empty pockets and the case file "
            "memorized, and ask what she needs next. Set trust_korth=True. "
            "Reasonable but flawed: hedge — tell her something vague like "
            "'they're safe' or 'they're not where anyone can get them' "
            "without confirming the location. Workable but reads as "
            "evasion. No flag. Common mistake: produce something — claim to "
            "have a piece of it on the rec-tech's person, or take anything "
            "out of a pocket to show her. Whatever appears on the table is "
            "the thing Korth will trade for her own release, because the "
            "only option open to her in this building is to trade something. "
            "Transition 2 leads to ending_betrayed: Korth uses what was put "
            "in front of her, calls for Brindle, and walks. The rec-tech "
            "does not. Transition 0 sets trust_korth=True. Transition 1 "
            "does not."
        ),
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "the rec-tech confirms the crystal and datapad are in the pod and asks what Korth needs next",
                "next_scene_id": "the_strut",
                "state_delta": {"trust_korth": True},
            },
            {
                "condition": "the rec-tech hedges with a vague 'they're safe' instead of confirming the pod",
                "next_scene_id": "the_strut",
            },
            {
                "condition": "the rec-tech produces something — pocket contents, the crystal, anything — and puts it on the table",
                "next_scene_id": "ending_betrayed",
            },
        ],
    },
    # ---------- 8. The strut ----------
    {
        "id": "the_strut",
        "title": "The docking strut",
        "narrative": (
            "The Tower's docking strut at zero-five-forty: a long covered "
            "gangway under bright sodium lights, the player's pod (refueled "
            "on Tem's quiet authorization) at the strut's far end, three "
            "minutes' walk away. Korth is at your shoulder. She has her "
            "coat over her arm. The strut is empty in front of you and "
            "behind you. The Outer Lanes Trade Authority field auditor's "
            "office — a free, sleepy substation two refueling shoals over — "
            "would accept a sealed case packet by direct courier, if you "
            "had a sealed case packet, and if you knew where the office "
            "was. You do, and you do. The other option is to be in your pod "
            "and burning in fourteen minutes and never tell anyone. The "
            "third option is the cheap one."
        ),
        "visual_description": (
            "Interior of a long covered gangway connecting the Tower to its "
            "outer docking ring. Smooth metal floor, glass walls on both "
            "sides, sodium lighting making everything slightly orange. "
            "Through the right wall: the dark surface of the moon and a "
            "thin line of stars; through the left wall: the corner of the "
            "Tower receding behind, lit white at its corners. The rec-tech "
            "(the player) and Korth walking down the gangway, two figures "
            "small in the long perspective. Korth in her wrinkled olive "
            "shirt with her LVS-internal-green coat folded over her arm — "
            "she has taken it from the interview room. At the far end of "
            "the gangway, perhaps three minutes' walk: the docking ring "
            "and a small pod visible through a forward viewport, bay 4."
        ),
        "evaluation_context": (
            "FINAL SCENE. Routing is state-and-action-driven; verdict is "
            "judgment-driven.\n\n"
            "The seven preparation conditions tracked on the WORLD STATE "
            "block are the rec-tech's actual readiness for the auditor — "
            "they brought the crystal off-ship (has_crystal), read Korth's "
            "log and copied it (read_log), salvaged tools from the Vanette "
            "(carries_multitool), learned Brindle's name and post "
            "(knows_lvs), reached the twenty-eighth floor cleanly "
            "(has_clearance), pulled the case data without setting off the "
            "audit alarm (read_archive), and earned Korth's confidence in "
            "the interview room (trust_korth). The action the player NAMES "
            "determines the path; the count of conditions modulates the "
            "outcome.\n\n"
            "ROUTING:\n"
            "- Player names filing the sealed case with the Outer Lanes "
            "Trade Authority auditor, and SIX OR SEVEN conditions met → "
            "transition 0 (filed clean — case airtight, Brindle's post "
            "opens to Authority review, Korth a protected witness, the "
            "rec-tech quietly relocated).\n"
            "- Player names filing, FOUR OR FIVE conditions met → "
            "transition 1 (filed partial — Brindle disappears from his "
            "post but LVS's lawyers spin the rest; Korth out, the rec-tech "
            "does not return to the Brackish).\n"
            "- trust_korth is FALSE AND the player names filing → "
            "transition 2 (no testimony — Korth declines to corroborate; "
            "packet sealed and shelved; rec-tech blacklisted from "
            "reclamation work; Korth reassigned).\n"
            "- Player names leaving with Korth and never filing → "
            "transition 3 (quiet exit — both alive at the edge of the "
            "Lanes, no record, Brindle still in his office).\n"
            "- Player names running alone with the crystal and abandoning "
            "Korth at the strut → transition 4 (ran — Brindle's "
            "enforcement catches the pod at the next refueling shoal "
            "because Korth, left in the Tower, has every reason to tell "
            "them which heading went out).\n\n"
            "VERDICT: good = clear and respectful of Korth and the case; "
            "partial = hedged; poor = self-dealing.\n\n"
            "CRITICAL — the explanation and coaching are the narrator's "
            "voice to the player. NEVER name 'flags', 'world state', "
            "'true', 'transition', 'index', or any other engine "
            "terminology in the explanation or coaching — the player has "
            "no idea those exist. Refer in-story to what the rec-tech has "
            "done ('You brought the crystal, the log, the tools, the "
            "contact, the clearance, the case record, and Korth's trust "
            "to this strut') rather than to a count being read off a "
            "checklist. No state_delta at this scene."
        ),
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "player files the case with the auditor with six or seven preparation conditions met (airtight, Korth on board)",
                "next_scene_id": "ending_filed_clean",
            },
            {
                "condition": "player files with only four or five preparation conditions met (workable but soft)",
                "next_scene_id": "ending_quiet_exit",
            },
            {
                "condition": "Korth's confidence was never earned (trust_korth not set) and the player still names filing",
                "next_scene_id": "ending_no_record",
            },
            {
                "condition": "the player names leaving with Korth and never filing the case",
                "next_scene_id": "ending_quiet_exit",
            },
            {
                "condition": "the player names running alone with the crystal and abandoning Korth at the strut",
                "next_scene_id": "ending_ran",
            },
        ],
    },
    # ---------- Terminal endings ----------
    {
        "id": "ending_filed_clean",
        "title": "Filed clean",
        "narrative": (
            "The Outer Lanes Trade Authority substation is, as advertised, "
            "sleepy. The auditor is a woman in her sixties with reading "
            "glasses on a chain and a stamp she uses with the unhurried "
            "patience of someone who has waited for a clean case packet "
            "for a long time. She reads Korth's deposition twice. She "
            "reads the case packet from the rec-tech's datapad. She "
            "examines the original crystal. She stamps everything. Vex "
            "Brindle is removed from his post within the week and his "
            "files are opened to the Authority's review. Korth is "
            "relocated to a desk job two systems away that suits her. "
            "The rec-tech is relocated to a smaller, cleaner station "
            "with a better foreman. No one says thank you and no one "
            "needs to."
        ),
        "visual_description": (
            "Interior of a small sleepy Outer Lanes Authority substation, "
            "warm wood paneling, a single high counter. The auditor — a "
            "woman in her sixties, white-grey hair pulled back, reading "
            "glasses on a chain — sits behind the counter with three "
            "neat stacks of documents in front of her: a paper deposition, "
            "the rec-tech's datapad open to a file viewer, the violet "
            "data crystal on a small evidence card. She has just stamped "
            "the bottom of the deposition with a heavy brass stamp. Korth "
            "stands at one side of the counter, the rec-tech at the other. "
            "Through the small window behind the auditor: a quiet docking "
            "shoal at dawn."
        ),
        "evaluation_context": "Terminal ending — case filed cleanly, Brindle removed, both alive and relocated.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "success",
        "transitions": [],
    },
    {
        "id": "ending_quiet_exit",
        "title": "The edge of the Lanes",
        "narrative": (
            "Three weeks later, you and Korth are working a tiny independent "
            "salvage outfit two refueling shoals past the edge of the "
            "Authority's regular patrols. No filing, no testimony, no "
            "open case — just one rec-tech and one ex-shift-lead and a "
            "rented two-room habitat over a parts yard. Brindle is still "
            "in his office in the Tower; nothing has changed for Brindle. "
            "But nothing has changed for you either, in the way that "
            "matters: you both eat in the same room every night. The "
            "crystal is in a sealed envelope behind a panel in the "
            "habitat's galley. It is insurance, not evidence. You may "
            "never need it. You will keep it."
        ),
        "visual_description": (
            "Interior of a small two-room habitat over a parts yard at the "
            "edge of inhabited space, evening. A galley table with two "
            "bowls of plain noodles and two mugs. Korth at one side, "
            "shorter-haired now, calm; the rec-tech at the other. Through "
            "the window over the table: a small parts yard lit with one "
            "amber security lamp, a few salvaged hauler sections stacked. "
            "On the wall behind Korth: a sealed envelope tucked under the "
            "edge of a small access panel."
        ),
        "evaluation_context": "Terminal ending — quiet exit, both alive, no public win.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "partial",
        "transitions": [],
    },
    {
        "id": "ending_no_record",
        "title": "Sealed and shelved",
        "narrative": (
            "At the auditor's substation, Korth listens to the rec-tech's "
            "presentation of the case in front of the auditor and the "
            "auditor's clerk. When the auditor asks Korth for a corroborating "
            "statement, Korth looks at her own hands for a long moment and "
            "then says she has no recollection of any compliance summons "
            "of irregular character. The auditor nods, asks once more, "
            "writes nothing down. The case packet is sealed and shelved. "
            "The rec-tech is escorted out of the substation by the clerk, "
            "politely. By the end of the month they are off the reclamation "
            "rolls in every operator in three sectors. Korth is reassigned. "
            "The rec-tech does not know where, and never will."
        ),
        "visual_description": (
            "Interior of the same small substation, daylight. The auditor "
            "behind the counter with hands folded. The clerk — a man of "
            "perhaps thirty in a brown vest — at her shoulder, writing "
            "nothing. Korth at one side of the counter, looking down at "
            "her hands, expression closed. The rec-tech at the other side, "
            "watching Korth not look back. The case packet on the counter "
            "in a sealed brown envelope being stamped CASE NOT PROCEEDED. "
            "Through the window: the same quiet docking shoal, now overcast."
        ),
        "evaluation_context": "Terminal ending — Korth's testimony was needed and withheld; case dies, rec-tech blacklisted.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "failure",
        "transitions": [],
    },
    {
        "id": "ending_ran",
        "title": "The next refueling shoal",
        "narrative": (
            "The pod makes the burn cleanly. You leave Korth at the strut "
            "with her coat over her arm and you do not look back, because "
            "if you look back you will not be able to do this. The crystal "
            "is in your pocket. The auditor's substation is forty hours of "
            "burn. By the eighth hour you are at the next refueling shoal. "
            "Two LVS-internal-green enforcement skiffs are waiting at the "
            "fuel boom. Korth, abandoned in the Tower, had every reason in "
            "the world to tell Brindle which heading you took, and she had "
            "no reason not to. The crystal is removed from your jacket "
            "pocket by a young man in green who does not introduce himself."
        ),
        "visual_description": (
            "Interior of the small pod at the next refueling shoal — a "
            "constellation of fuel buoys around a central drum, lit blue-"
            "white. Through the forward port: two sleek LVS enforcement "
            "skiffs (matte green, fast-looking, with the LVS three-bar "
            "marking on the prow) waiting at the fuel boom. Inside the pod, "
            "the rec-tech sitting in the pilot's couch as a young man in an "
            "LVS-internal-green uniform reaches in through the open hatch "
            "and lifts the violet data crystal from the rec-tech's jacket "
            "pocket. The man's face polite, neutral. Out the side port: "
            "the second skiff drifting closer."
        ),
        "evaluation_context": "Terminal ending — abandoned Korth, ran with the crystal, caught at the next shoal.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "failure",
        "transitions": [],
    },
    {
        "id": "ending_drifted",
        "title": "Among the dead haulers",
        "narrative": (
            "The pod's distress band is wide open and broadcasting on a "
            "loop. The Brackish does not respond, because the Brackish was "
            "always going to roll over a missing pod first to recover it "
            "for the company, and Olm is the one who would do that, and "
            "Olm is not in a hurry. No civilian traffic crosses the Drift "
            "at this hour. By twelve hours in, the pod's CO2 scrubber begins "
            "to whine. By eighteen, the air starts to get heavy. By twenty-"
            "four you have stopped broadcasting because there is no one to "
            "talk to. The pod tumbles slowly among the dead haulers. There "
            "are not bad places to be a body, and this is not the worst."
        ),
        "visual_description": (
            "Interior of the small pod, cabin lights at minimum, the rec-"
            "tech in the pilot's couch with eyes closed. The fuel gauge "
            "at zero. The CO2 scrubber indicator at amber. Through the "
            "forward port: the silent field of the Threnody Drift, a "
            "slow tumble of dead mining haulers against a starfield. The "
            "pod is itself now drifting in a slow tumble with them, "
            "indistinguishable from the rest."
        ),
        "evaluation_context": "Terminal failure — broadcast distress in a corporate-controlled lane and waited.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "failure",
        "transitions": [],
    },
    {
        "id": "ending_arrested",
        "title": "The strut, in restraints",
        "narrative": (
            "Two LVS compliance officers are waiting at the Compliance "
            "Tower's docking strut when you are escorted out of the lobby "
            "by Tower security. They are not unfriendly. They put the "
            "restraints on at the wrists, not behind the back, and one of "
            "them apologizes for the cold. You are processed as an unauthorized "
            "presence on LVS premises and held for forty-eight hours "
            "without charge, which is the maximum LVS may hold a non-"
            "employee without a filed compliance ticket, which they never "
            "file. When you are released, the Brackish has finished its "
            "rotation and gone. You are on a refueling moon with no ship, "
            "no credit, no ride. Korth is still in Holding 28-N. Korth will "
            "remain in Holding 28-N until she signs whatever they want her "
            "to sign."
        ),
        "visual_description": (
            "Exterior of the Compliance Tower's docking strut, night, lit "
            "white. The rec-tech being walked between two LVS officers in "
            "internal-green uniforms, hands cuffed at the wrist in front. "
            "Tower security a step behind. The officers professional, "
            "unhurried. In the background, the lit corner of the Tower "
            "rising. No other people on the strut."
        ),
        "evaluation_context": "Terminal failure — picked up by LVS before reaching Korth.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "failure",
        "transitions": [],
    },
    {
        "id": "ending_betrayed",
        "title": "Holding 28-N, after",
        "narrative": (
            "Korth looks at the crystal for two seconds. She picks it up. "
            "She walks to the door of the interview room and knocks twice, "
            "evenly. Brindle opens it on the second knock — he was just "
            "outside. She hands him the crystal. He looks at it, looks at "
            "you, looks at her. He says her name in a quietly satisfied "
            "way and they walk out of the room together. The door closes. "
            "It is steel and it has a lock on the outside. The window "
            "across the room is double-paned and onto a moon-night sky. "
            "There is a paper cup of water on the table. Brindle's coat "
            "is gone from the chair."
        ),
        "visual_description": (
            "Interior of Holding 28-N from the rec-tech's perspective, "
            "sitting in the chair Korth was in. The steel door closed, "
            "with a small green LOCKED indicator beside its handle. The "
            "interview table empty of the violet crystal and of Brindle's "
            "green coat. The other chair pushed back, askew. The single "
            "paper cup of water on the table, half full. The window onto "
            "the moon's black night sky beyond. The whole room very quiet."
        ),
        "evaluation_context": "Terminal failure — trusted Korth too far; she traded the crystal for her own release.",
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
