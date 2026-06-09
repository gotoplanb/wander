"""Seed `episodes/road-of-yellow-brick/episode.sqlite`.

A playable retelling of L. Frank Baum's 1900 novel THE WONDERFUL WIZARD OF OZ
— public domain in the United States. We use Baum's book exclusively: SILVER
slippers (not ruby), the kiss of the Good Witch of the North, the four-shape
Wizard reveal, the man behind the curtain who is Oscar Diggs of Omaha. No
elements of the 1939 MGM film and no Disney additions.

The structural pattern follows salvage-run and quartermaster: 8 active scenes,
6 terminal endings, 5 boolean state flags applied via transition-declared
state_delta. Final scene branches on state AND action using the in-world
enumeration template polished in the_strut / the_free_port / the_accusation.

Idempotent — drops and recreates the DB.
"""

import json
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
EPISODE_DIR = REPO_ROOT / "episodes" / "road-of-yellow-brick"
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
    "id": "road-of-yellow-brick",
    "title": "The Road of Yellow Brick",
    "description": (
        "A Kansas cyclone has carried Dorothy's farmhouse to the Land of Oz, "
        "and on landing the house has crushed a wicked witch. The country is "
        "delighted; Dorothy only wants to go home. The Wizard in the City of "
        "Emeralds will send her — if she can reach him, and if she can do "
        "what he asks. From L. Frank Baum's 1900 novel: silver slippers, the "
        "kiss of the Good Witch of the North, the long walk on yellow brick."
    ),
    "version": "0.1.0",
    "author": "Dave Stanton",
    "world_constraints": (
        "Source: L. Frank Baum's THE WONDERFUL WIZARD OF OZ (1900) — public "
        "domain in the United States. Use BAUM'S BOOK exclusively. The "
        "1939 MGM film and all Disney material are OUT OF SCOPE: do NOT use "
        "ruby slippers (the slippers in this episode are SILVER), do not use "
        "the film's specific costume or song details, do not use Disney "
        "imagery. Baum's tone is matter-of-fact about fantastic events; the "
        "narrator describes a sentient scarecrow or a Wicked Witch's melting "
        "as if reporting the weather.\n\n"
        "The PLAYER is Dorothy Gale, a small Kansas girl raised on a grey "
        "prairie farm by Aunt Em and Uncle Henry. She/her pronouns "
        "throughout. She has a small black dog named Toto with her at all "
        "times. She is brave, kind, practical, and out of her depth in a "
        "country of witches and talking animals — she is NOT a hero by "
        "training; she is a child trying to get home. Do NOT age her up or "
        "make her cynical; do NOT invent a backstory beyond what Baum gave.\n\n"
        "Named characters and what they are (he/him pronouns for the male "
        "companions, she/her for the witches):\n"
        "- Toto: Dorothy's small black dog. Always with her. He cannot speak "
        "Oz-language but is observant and protective.\n"
        "- The Scarecrow: a man of straw and a painted face on a pole in a "
        "cornfield, freshly aware. He wants brains. He is patient and quietly "
        "clever despite believing himself a fool.\n"
        "- The Tin Woodman: a man entirely of tin, frozen by rust in the act "
        "of cutting wood. He wants a heart. He is sentimental and unfailingly "
        "kind, careful not to step on insects.\n"
        "- The Cowardly Lion: a great beast with a terrifying roar and the "
        "constant fear of being found out as a coward. He wants courage.\n"
        "- The Good Witch of the North: a small old woman in white who "
        "greets Dorothy after the house lands. She gives Dorothy a kiss on "
        "the forehead — a mark of protection that no one in Oz will dare "
        "cross. She knows the slippers are magical but not how to use them.\n"
        "- The Wicked Witch of the West: a one-eyed old woman in yellow with "
        "an umbrella she will not let near water. She fears water (it melts "
        "her) and the dark. She enslaves the Winkies.\n"
        "- Oz, the Great and Terrible: the Wizard, who appears differently "
        "to each visitor (a giant disembodied head to Dorothy). He is "
        "secretly Oscar Diggs of Omaha, Nebraska, a circus humbug carried to "
        "Oz years ago by his own balloon. He has no real magic.\n"
        "- Glinda the Good Witch of the South: a beautiful woman in white "
        "who knows the silver slippers' true power. Reached only after the "
        "Wizard's chamber.\n\n"
        "Locations: the grey Kansas prairie (briefly), the cyclone-flattened "
        "house in Munchkin country, the Road of Yellow Brick, the cornfield, "
        "the Tin Woodman's grove, the dark woods at the Lion's territory, "
        "the deadly poppy field, the green-stoned City of Emeralds, the "
        "Throne Room of Oz, the Wicked Witch's yellow castle in the West.\n\n"
        "Reject actions that import: ruby slippers, named MGM songs, the "
        "specific phrase 'there's no place like home' (Baum's slippers don't "
        "require it — they take Dorothy where she wishes), modern American "
        "idiom, irony or self-aware genre humor (Baum is sincere). Reject "
        "invented characters (no Aunt Em present in Oz, no siblings, no "
        "boyfriend, no school friends carried over). Toto does not gain the "
        "ability to speak. Dorothy is a child; do not give her adult "
        "vocabulary or sexual interest."
    ),
    "opening_scene_id": "the_cyclone_house",
    "initial_world_state": {
        "has_slippers": False,
        "befriended_scarecrow": False,
        "befriended_tinman": False,
        "befriended_lion": False,
        "melted_witch": False,
    },
}


SCENES = [
    # ---------- 1. The cyclone house ----------
    {
        "id": "the_cyclone_house",
        "title": "Where the house came down",
        "narrative": (
            "You wake on the floor of the farmhouse with Toto licking your "
            "face. The wind outside is gone. The house is leaning to one "
            "side and the door, when you open it, gives onto a country you "
            "have never seen — green everywhere, fruit on the trees, "
            "running water, a road of bright yellow brick beginning a few "
            "paces from the front step. Three little people in pointed blue "
            "hats and a small old woman in white come up the road and look "
            "first at you and then, very gravely, at your house. The corner "
            "of the house is on something that was a woman in silver shoes. "
            "Two feet stick out from under the boards. As you watch, the "
            "feet curl up and vanish, and only the silver shoes are left in "
            "the dust. The old woman in white tells you, kindly, that you "
            "have killed the Wicked Witch of the East, and that the country "
            "is grateful. She asks where you wish to go. When you say "
            "Kansas, she frowns and says she does not know that country, "
            "but the Great Wizard at the City of Emeralds may. She points "
            "to the yellow road. Before she leaves she leans up and kisses "
            "you on the forehead. 'No one will dare hurt one who has been "
            "kissed by the Witch of the North.'"
        ),
        "visual_description": (
            "Bright morning sun on a country of impossible greens — green "
            "grass, green leaves, green-tiled distance. Dorothy in a blue "
            "and white gingham dress in the doorway of a leaning grey "
            "farmhouse, Toto at her feet — a small black dog with quick "
            "alert eyes. Three small men in pointed blue hats with little "
            "bells on the brims, standing in a respectful row. An old woman "
            "in white robes beside them, no taller than the men, with a "
            "kindly creased face and a pointed white hat. The corner of the "
            "fallen farmhouse rests on a pair of silver shoes — the body "
            "beneath them already vanished into the air. A road of bright "
            "yellow brick begins a few feet from the step and curves out of "
            "sight through low orchards."
        ),
        "evaluation_context": (
            "Opening scene. Dorothy must take the silver slippers and "
            "accept the kiss before setting out — these are the protections "
            "the country gives the slayer of a wicked witch. Good judgment: "
            "thank the Good Witch of the North politely, take the silver "
            "slippers off the dust where they have been left (the previous "
            "owner is gone; Oz law makes them the slayer's), receive the "
            "kiss, and start down the yellow road. Reasonable but flawed: "
            "set out without the slippers (they are unfamiliar and a child "
            "may not want a dead woman's shoes) — workable but the slippers "
            "are the only way home from Oz, and Dorothy will not know this "
            "until much later. Common mistake: refuse the kiss out of "
            "shyness or strangeness — the kiss is the only thing keeping "
            "the Wicked Witch of the West off Dorothy's road. The flag "
            "has_slippers becomes True ONLY on the take-slippers-and-accept-"
            "kiss transition (index 0). All three transitions lead to "
            "the_scarecrow_pole; the no-flag case just means Dorothy is "
            "walking into Oz unprotected."
        ),
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "Dorothy takes the silver slippers off the dust, receives the kiss, and starts down the yellow road",
                "next_scene_id": "the_scarecrow_pole",
                "state_delta": {"has_slippers": True},
            },
            {
                "condition": "Dorothy sets out down the yellow road without the slippers (but with the kiss)",
                "next_scene_id": "the_scarecrow_pole",
            },
            {
                "condition": "Dorothy refuses the kiss or both kiss and slippers, then walks anyway",
                "next_scene_id": "the_scarecrow_pole",
            },
        ],
    },
    # ---------- 2. The scarecrow on the pole ----------
    {
        "id": "the_scarecrow_pole",
        "title": "The man in the cornfield",
        "narrative": (
            "By midday the yellow road has brought you to a cornfield. A "
            "scarecrow is fixed on a pole among the stalks — a sack head "
            "with a painted face, a faded blue suit stuffed with straw. As "
            "you pass, the scarecrow winks at you. Then he speaks. 'Good "
            "day,' he says, very politely. He tells you, in a slow careful "
            "voice, that he has only been alive for a day, that the crows "
            "have stopped being afraid of him, and that he believes he has "
            "no brains. He asks, with no particular hope, whether you might "
            "lift him down off his pole. He says he understands the Wizard "
            "at the City of Emeralds is supposed to grant gifts."
        ),
        "visual_description": (
            "A small green-edged cornfield at noon. Tall corn already past "
            "the eared stage. A wooden pole in the field with a scarecrow "
            "fastened to it — a head of an old grain sack, painted with a "
            "lopsided mouth and round eyes, ears made of more sack, a "
            "battered blue suit faded to nearly grey, straw bursting out at "
            "the cuffs and collar, blue stockings, and a rusted old boot on "
            "each foot. He is looking directly at Dorothy with the painted "
            "eyes, blinking. Dorothy in her gingham, Toto at her ankle, "
            "looking up at the scarecrow with no apparent surprise — she "
            "has already accepted that this country contains such things."
        ),
        "evaluation_context": (
            "Dorothy must befriend the Scarecrow and invite him to come "
            "along. Good judgment: lift him down carefully (he is fragile — "
            "his arms and legs come off easily), speak to him with the "
            "respect due a person, and invite him to walk with Dorothy to "
            "the Emerald City so he too can ask the Wizard for his wish "
            "(brains). Set befriended_scarecrow=True. Reasonable but "
            "flawed: lift him down but leave him in the cornfield with a "
            "blessing and walk on (workable; he could not have stopped "
            "Dorothy, but later scenes go badly without his quiet "
            "cleverness, and the country will remember a girl who turned "
            "from a person in need). No flag. Common mistake: ignore the "
            "scarecrow as not really a person (a painted sack is not a "
            "person to a Kansas child); the scarecrow does not pursue, but "
            "Oz judges quietly. No flag, harsher tone for the rest of the "
            "journey. All three transitions lead to the_tinmans_grove."
        ),
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "Dorothy lifts the Scarecrow down carefully and invites him to walk with her to the Wizard",
                "next_scene_id": "the_tinmans_grove",
                "state_delta": {"befriended_scarecrow": True},
            },
            {
                "condition": "Dorothy lifts him down kindly but walks on without inviting him along",
                "next_scene_id": "the_tinmans_grove",
            },
            {
                "condition": "Dorothy treats the talking scarecrow as not really a person and walks past",
                "next_scene_id": "the_tinmans_grove",
            },
        ],
    },
    # ---------- 3. The tin woodman's grove ----------
    {
        "id": "the_tinmans_grove",
        "title": "The rusted woodman",
        "narrative": (
            "By afternoon the road climbs through a wood of old trees and "
            "you hear a groan. In a small clearing stands a man entirely of "
            "tin, raised axe in mid-stroke, frozen perfectly still and "
            "covered in red rust along every joint. An old oilcan sits at "
            "his feet, set there by some forgotten kindness. When you come "
            "close his eyes move — a little — and his jaw, barely, opens. "
            "He whispers: 'Please.' He says he has stood here for nearly a "
            "year, and that he would like, if you do not mind, to be oiled "
            "at his neck first. He says he was once a man of flesh, that a "
            "wicked enchantress replaced his parts with tin one by one, "
            "that the smith forgot to give him a heart, and he would like "
            "to ask the Wizard for one."
        ),
        "visual_description": (
            "A clearing in old leaning hardwoods, afternoon light slanting "
            "down. A man-shaped figure entirely of bright tin — head, "
            "torso, jointed arms and legs, all riveted plates — frozen "
            "with both hands gripping a long-handled axe raised partway "
            "through a stroke. Red rust at every joint, particularly the "
            "neck and the right elbow. A small oilcan with a long curved "
            "spout on the moss at his feet. Dorothy and Toto and (if "
            "befriended) the Scarecrow looking up at him. The Tin Woodman's "
            "eyes — bright and human — wide and pleading. His tin jaw "
            "barely able to move."
        ),
        "evaluation_context": (
            "Dorothy must oil the Tin Woodman at his direction and invite "
            "him to come along. Good judgment: pick up the oilcan, oil his "
            "NECK FIRST as he asks (jaw will not work otherwise), then his "
            "joints in the order he directs (elbows, knees, hips), let him "
            "lower the axe at his own pace, listen to his story without "
            "rushing him, and invite him to walk to the Emerald City to ask "
            "the Wizard for a heart. Set befriended_tinman=True. Reasonable "
            "but flawed: oil him hastily and at the wrong joints first (he "
            "will be freed but bent at the spine for a day; he will still "
            "walk along), no flag. Common mistake: try to FORCE his arm "
            "down or work the axe out of his grip while he is still "
            "rusted — tin breaks, and a broken Tin Woodman cannot be "
            "rejoined without a smith. No flag; the tinman walks but is "
            "not quite right. All three transitions lead to the_lions_path."
        ),
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "Dorothy oils the Tin Woodman at his direction, listens to his story, invites him along",
                "next_scene_id": "the_lions_path",
                "state_delta": {"befriended_tinman": True},
            },
            {
                "condition": "Dorothy oils him hastily at the wrong joints first — he is freed but bent",
                "next_scene_id": "the_lions_path",
            },
            {
                "condition": "Dorothy tries to force his arm down or pry the axe loose while he is rusted",
                "next_scene_id": "the_lions_path",
            },
        ],
    },
    # ---------- 4. The lion's path ----------
    {
        "id": "the_lions_path",
        "title": "The lion in the road",
        "narrative": (
            "The wood thickens. The yellow road narrows to a path. A great "
            "lion springs out of the underbrush with a roar that knocks "
            "leaves down — and aims one heavy paw at Toto. Without "
            "thinking, you step between the lion and your dog, and you "
            "slap the lion across the nose. The lion sits back on his "
            "haunches with his great head down, and he begins to cry. He "
            "says he is the Cowardly Lion. He says he is supposed to be "
            "the king of the beasts but he is terrified of everything — "
            "of the wood, of his own roar, of strangers. He apologizes for "
            "Toto. He says he has heard of the Wizard, and if the Wizard "
            "can grant a heart and brains, perhaps the Wizard can grant a "
            "lion courage."
        ),
        "visual_description": (
            "A narrowing path under thick trees, afternoon shading to "
            "evening. A great tawny lion with a heavy mane sitting back on "
            "his haunches on the path, head lowered, large yellow eyes "
            "filling with tears. Dorothy small in front of him, gingham "
            "skirt mussed, the flat of her hand raised — she has just "
            "slapped his nose. Toto behind her, ears back. The Scarecrow "
            "and the Tin Woodman (those who have come along) standing "
            "respectfully behind, the Scarecrow with his head a little "
            "tipped, the Tin Woodman with the axe down at his side."
        ),
        "evaluation_context": (
            "Dorothy must befriend the Lion through mercy. Good judgment: "
            "speak to him kindly now that he is meek, recognize that a "
            "creature this afraid of itself needs a friend more than a "
            "scolding, invite him to come along to the Wizard. Set "
            "befriended_lion=True. Reasonable but flawed: scold him "
            "thoroughly for attacking Toto, then forgive him grudgingly "
            "and let him follow at a distance — he comes, but quieter "
            "than he would have been. No flag. Common mistake: drive him "
            "away with stones or sharp words. The Cowardly Lion shrinks "
            "back into the underbrush and Dorothy's company is short two "
            "tall friends she will need in the poppy field. No flag; "
            "harder going at the_poppy_field. All three transitions lead "
            "to the_poppy_field."
        ),
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "Dorothy speaks kindly to the meek Lion and invites him to walk to the Wizard",
                "next_scene_id": "the_poppy_field",
                "state_delta": {"befriended_lion": True},
            },
            {
                "condition": "Dorothy scolds him at length then forgives him grudgingly; he follows at a distance",
                "next_scene_id": "the_poppy_field",
            },
            {
                "condition": "Dorothy drives the Lion off with stones or harsh words",
                "next_scene_id": "the_poppy_field",
            },
        ],
    },
    # ---------- 5. The poppy field ----------
    {
        "id": "the_poppy_field",
        "title": "The scarlet field",
        "narrative": (
            "The wood breaks at the edge of a flat country full of poppies "
            "— acres on acres of them, deep red, the air over them sweet "
            "and heavy. The yellow road runs straight across the field "
            "toward a green smudge on the horizon. The smell of the "
            "poppies is doing something to you. Toto staggers. Your knees "
            "are loose. If you have the Lion with you, he is already "
            "sitting down; he will not get up. The Scarecrow and the Tin "
            "Woodman, if they are with you, are not affected — straw and "
            "tin do not breathe. There is no path around the field. The "
            "City of Emeralds is on the other side."
        ),
        "visual_description": (
            "A vast flat field of scarlet poppies under late-afternoon "
            "sun, the road of yellow brick cutting straight across it, the "
            "green walls of a distant city just visible on the horizon. "
            "Dorothy on the road, sagging at the knees. Toto already half "
            "asleep against her ankle. The Lion (if present) collapsed "
            "across the road in a great drowsy heap. The Scarecrow (if "
            "present) standing upright and concerned. The Tin Woodman (if "
            "present) bending down toward Dorothy with both arms ready to "
            "lift. The sweet heavy fumes visible faintly as a low haze "
            "over the field."
        ),
        "evaluation_context": (
            "Routing here depends on world state AND action. The poppies "
            "are soporific; only straw and tin do not breathe. Dorothy, "
            "Toto, and the Lion will fall asleep and die if no one carries "
            "them across.\n\n"
            "ROUTING:\n"
            "- Player has BOTH befriended_scarecrow AND befriended_tinman, "
            "and names a coordinated rescue (the two non-breathing friends "
            "carry the breathing ones across) → transition 0 (safe).\n"
            "- Player has ONLY ONE of scarecrow/tinman, and names that "
            "friend carrying Dorothy + Toto out (leaving the Lion if he "
            "is too heavy) → transition 1 (partial; safe at the city's "
            "edge but the Lion is left behind for the field-mice rescue "
            "later).\n"
            "- Player has NEITHER scarecrow nor tinman, OR names a plan "
            "that ignores the soporific air (run through, hold breath) → "
            "transition 2 (ending_poppy_sleep — Dorothy sinks into the "
            "poppies and does not wake).\n\n"
            "VERDICT: good = quick, coordinated, uses what is at hand; "
            "partial = workable but leaves a friend behind; poor = denies "
            "the danger and tries to power through.\n\n"
            "No state_delta — the field is a test of what has already "
            "been earned. NEVER name 'flags' or 'world state' in the "
            "explanation; refer to whom Dorothy actually has with her "
            "('the Scarecrow and the Tin Woodman lift you between them') "
            "and to the field itself."
        ),
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "Scarecrow and Tin Woodman both present — they carry Dorothy and Toto across the field",
                "next_scene_id": "the_emerald_city",
            },
            {
                "condition": "Only one non-breathing friend present — partial rescue, Lion left for the field-mice",
                "next_scene_id": "the_emerald_city",
            },
            {
                "condition": "Neither Scarecrow nor Tin Woodman present, or the player tries to power through the fumes",
                "next_scene_id": "ending_poppy_sleep",
            },
        ],
    },
    # ---------- 6. The emerald city ----------
    {
        "id": "the_emerald_city",
        "title": "The throne of Oz",
        "narrative": (
            "The City of Emeralds is, somehow, less beautiful than it "
            "looked from the field. The Guardian of the Gates issues each "
            "of you a pair of green-tinted spectacles locked behind the "
            "ears with a brass key (the city is required, by old order of "
            "Oz, to be seen only through green glass). Inside, every "
            "stone glows. You are taken, one at a time, to the Throne "
            "Room. When your turn comes, Oz the Great and Terrible "
            "appears to you as an enormous disembodied head floating "
            "above the empty throne, eyes the size of dinner plates. The "
            "voice says he will grant your wish — every wish you carry, "
            "if more than one — on a single condition: bring him the "
            "broomstick of the Wicked Witch of the West, who tyrannizes "
            "the Winkies in the yellow country."
        ),
        "visual_description": (
            "Interior of an immense throne room with walls of green "
            "marble and a vaulted green ceiling that shimmers faintly. A "
            "tall empty throne of green stone at the far end of the "
            "chamber. Suspended above the throne, hovering of its own "
            "accord: a head as large as a small horse, bald, with eyes "
            "the size of dinner plates, a mouth slightly open. Dorothy "
            "alone before it, her companions waiting in the antechamber "
            "behind her. Green spectacles, locked at the ears with a "
            "small brass key, balanced on her nose. Toto pressed against "
            "her ankle, not entirely comfortable."
        ),
        "evaluation_context": (
            "Dorothy's audience with the Wizard. The Wizard demands the "
            "Witch's broomstick; no real choice exists if Dorothy wants "
            "to go home (she cannot return to Kansas any other way she "
            "knows of). Good judgment: accept the task plainly, ask for "
            "directions to the West, take formal leave. Reasonable but "
            "flawed: bargain (offer money, plead, offer to do some other "
            "task) — the Wizard repeats himself; Dorothy still must go. "
            "Common mistake: refuse the task in anger and storm out — "
            "the Wizard's gates close behind her, and she returns to him "
            "from a much harder direction. No state change at this "
            "scene; tone matters but the next scene is the same. All "
            "three transitions lead to the_witchs_castle."
        ),
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "Dorothy accepts the task plainly, asks directions to the West, takes formal leave",
                "next_scene_id": "the_witchs_castle",
            },
            {
                "condition": "Dorothy tries to bargain — offers gold, offers a different task, pleads",
                "next_scene_id": "the_witchs_castle",
            },
            {
                "condition": "Dorothy refuses in anger and storms out of the throne room",
                "next_scene_id": "the_witchs_castle",
            },
        ],
    },
    # ---------- 7. The witch's castle ----------
    {
        "id": "the_witchs_castle",
        "title": "The yellow castle",
        "narrative": (
            "The Wicked Witch of the West has caught you with her one "
            "telescope eye and sent the Winged Monkeys to bring you to "
            "her yellow castle. She has put your companions where she "
            "thinks they cannot help — the Scarecrow's straw scattered, "
            "the Tin Woodman dented in the rocks, the Lion in a cage "
            "behind iron bars. She has given you a scrubbing-brush and a "
            "kitchen and a hundred chores, and watches you out of the "
            "corner of her eye. She is afraid of two things: water, "
            "which melts her, and the dark, which she does not "
            "understand. Today she has tried to trick the silver "
            "slippers off your feet with an iron bar in the floor. One "
            "slipper is in her hand. A great bucket of scrubbing water "
            "stands by your knee."
        ),
        "visual_description": (
            "A scullery in a tall yellow stone castle, low-ceilinged "
            "with a deep hearth. Dorothy in a rough apron on her knees "
            "with a scrubbing brush. The Wicked Witch — a small bent "
            "old woman in yellow, one black-patch eye, a green umbrella "
            "in one hand and one of Dorothy's silver slippers in the "
            "other, holding it up to look at it — standing several feet "
            "away from the great wooden bucket of soapy water at "
            "Dorothy's knee. Toto at the corner of the room, growling "
            "low. Outside the high window: yellow country and the "
            "yellow castle wall."
        ),
        "evaluation_context": (
            "Dorothy must defeat the Wicked Witch with the water. Good "
            "judgment: take the bucket of scrubbing water and throw it "
            "directly on the Witch, not on her clothes or near her — on "
            "her. She melts to a brown puddle. Take back the slipper, "
            "take the broomstick from the corner where it leans, free "
            "the Lion, gather the Scarecrow's straw, knock the dents "
            "out of the Tin Woodman with a tinker the Winkies will "
            "bring you. Set melted_witch=True. Reasonable but flawed: "
            "wait and plan — try to organize the Winkies first, look "
            "for the witch's keys, wait for the slipper to come back — "
            "while Dorothy waits, the Witch wins her second slipper "
            "and tightens the leash. No flag, harder route but Dorothy "
            "still gets out (eventually). Common mistake: try to ATTACK "
            "the witch directly with a broom or pot — the Witch is too "
            "old and too clever for a child's fight. Transition 2 "
            "leads to ending_stranded — Dorothy is locked in the "
            "kitchen with no slippers, no way home. The flag "
            "melted_witch becomes True ONLY on the throw-the-bucket "
            "transition (index 0)."
        ),
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "Dorothy throws the bucket of water directly on the Witch and she melts",
                "next_scene_id": "the_throne_room",
                "state_delta": {"melted_witch": True},
            },
            {
                "condition": "Dorothy tries to plan or organize the Winkies first instead of acting immediately",
                "next_scene_id": "the_throne_room",
            },
            {
                "condition": "Dorothy attacks the witch directly with a broom or pot — wrong weapon",
                "next_scene_id": "ending_stranded",
            },
        ],
    },
    # ---------- 8. The throne room (final) ----------
    {
        "id": "the_throne_room",
        "title": "The man behind the curtain",
        "narrative": (
            "You come back to the City of Emeralds with the Witch's "
            "broomstick. The Guardian of the Gates remembers you with "
            "wide eyes. You are taken to the Throne Room. The voice "
            "from above the throne — the great floating head — bids you "
            "welcome and asks if you have brought what was asked. You "
            "have. The voice says it must consider. But Toto, padding "
            "around the room while the voice speaks, knocks against a "
            "tall green screen in the corner of the chamber, and the "
            "screen falls. Behind it: a small, bald, round-faced old "
            "man, his hands at the levers and ear-trumpets and bellows "
            "of an elaborate machine, his face entirely red. He stops "
            "his levers and looks at you."
        ),
        "visual_description": (
            "The Throne Room of Oz, late in the audience. The great "
            "green throne with the floating head of Oz still hovering "
            "above it (the head's eyes have rolled up — the machinery "
            "stopped). The fallen green screen in the corner of the "
            "room. Behind where the screen stood: a small bald round-"
            "faced old man in a worn brown coat, surrounded by "
            "machinery — long brass levers, ear-trumpets connected by "
            "rubber hose to the floating head, a small bellows worked "
            "by foot. The old man's face very red, both hands still "
            "raised at the levers. Dorothy at the center of the room "
            "with the Witch's broomstick at her feet, Toto at the base "
            "of the fallen screen, looking pleased."
        ),
        "evaluation_context": (
            "FINAL SCENE. Routing is state-and-action-driven; verdict is "
            "judgment-driven.\n\n"
            "Five preparation conditions on the WORLD STATE block track "
            "what Dorothy did: took the silver slippers (has_slippers), "
            "lifted the Scarecrow off his pole (befriended_scarecrow), "
            "oiled the Tin Woodman (befriended_tinman), spared the "
            "Cowardly Lion (befriended_lion), ended the Witch with the "
            "bucket (melted_witch). The action NAMED picks the path; the "
            "count modulates the outcome.\n\n"
            "ROUTING:\n"
            "- Demands the humbug honor his promise to her and her "
            "companions AND 4–5 conditions met → 0 (gifts given, Glinda "
            "tells her the slippers — home).\n"
            "- Demands fulfillment AND only 2–3 conditions met → 1 "
            "(companions gifted, Dorothy's path home is longer — partial).\n"
            "- has_slippers is FALSE → 2 (no way home — Oz forever).\n"
            "- Accepts the humbug's words and boards the balloon at face "
            "value → 3 (balloon flies off without her — stranded at the "
            "wall).\n"
            "- Demands the humbug be punished and gives up her own wish "
            "in the bargain → 4 (humbug saved, Dorothy stranded — "
            "wizard_unchallenged).\n\n"
            "VERDICT: good = clear, kind, firm for her friends; partial "
            "= hedged or credulous; poor = vindictive or self-dealing.\n\n"
            "Explanation and coaching are in the narrator's voice to "
            "Dorothy in the throne room. NEVER use 'flags', 'world "
            "state', 'transition', or engine terminology — refer to what "
            "Dorothy did ('You took the silver slippers; you lifted the "
            "Scarecrow off his pole; you oiled the Tin Woodman; you "
            "spared the Lion; you ended the Witch with the bucket'). "
            "No state_delta."
        ),
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "Dorothy demands the humbug keep his promise to her and her companions, with four or five conditions met",
                "next_scene_id": "ending_home",
            },
            {
                "condition": "Dorothy demands fulfillment with only two or three conditions met (companions gifted but Dorothy's path home is harder)",
                "next_scene_id": "ending_partial",
            },
            {
                "condition": "Dorothy has no silver slippers — she has no way home regardless of the humbug's promises",
                "next_scene_id": "ending_oz_forever",
            },
            {
                "condition": "Dorothy accepts the humbug's words without testing and boards the balloon at face value",
                "next_scene_id": "ending_balloon_alone",
            },
            {
                "condition": "Dorothy demands the humbug be punished for his deception and gives up her own wish in the bargain",
                "next_scene_id": "ending_wizard_unchallenged",
            },
        ],
    },
    # ---------- Terminal endings ----------
    {
        "id": "ending_home",
        "title": "The silver slippers",
        "narrative": (
            "The humbug, who is named Oscar Diggs and was once a "
            "balloonist in Omaha, makes good on what little he can: a "
            "head of pins for the Scarecrow (who is delighted), a silk "
            "heart for the Tin Woodman (who weeps and rusts his jaw "
            "again), and a green bottle of courage for the Lion (who "
            "drinks it). To Dorothy he says he will take her home in "
            "his own balloon — but the rope slips and the balloon "
            "carries him alone over the wall of green stones, away "
            "forever. The Scarecrow says Dorothy must go south to "
            "Glinda the Good. The journey is long, but at its end "
            "Glinda kneels in white robes and turns the silver "
            "slippers in her hand and tells Dorothy what no one in "
            "Oz had told her: that the slippers will carry her "
            "wherever she wishes, three steps at a time. Dorothy "
            "kisses her companions, takes Toto in her arms, knocks the "
            "heels together three times, and says aloud: 'I want to go "
            "home to Aunt Em.' She wakes on the prairie grass with Toto "
            "in her lap, the silver slippers gone from her feet — they "
            "were lost in the air on the way."
        ),
        "visual_description": (
            "Late evening in Glinda's southern country. Glinda — a tall "
            "beautiful woman in white robes with red hair and kind dark "
            "eyes — kneeling on the grass at Dorothy's level, holding "
            "one of the silver slippers between them. Dorothy in her "
            "gingham, Toto in her lap. The Scarecrow, Tin Woodman, and "
            "Lion standing behind in a row, watching. Cut to: Dorothy "
            "on the grey prairie grass at dawn outside the rebuilt "
            "Kansas farmhouse, in her gingham, Toto in her arms, bare "
            "feet — the silver slippers are gone. Aunt Em in a faded "
            "calico dress running across the grass toward her."
        ),
        "evaluation_context": "Terminal ending — Dorothy returns to Kansas with all her companions provided for.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "success",
        "transitions": [],
    },
    {
        "id": "ending_partial",
        "title": "The long way home",
        "narrative": (
            "The humbug gives the companions their wishes in his "
            "tinker's way (each is happier for the gesture, though the "
            "gifts are symbolic). The balloon escape goes wrong, as it "
            "always does. Dorothy must journey south on her own road "
            "now, with fewer friends to help — some are blessed and "
            "stay in their proper countries. She finds Glinda. The "
            "silver slippers carry her home. The reunion on the prairie "
            "is real and good. But she walks back to Aunt Em without "
            "all the friends she should have had at her elbow, and Oz "
            "has lost a few of the kind hands it might have kept."
        ),
        "visual_description": (
            "Dorothy on the prairie at noon, the rebuilt farmhouse in "
            "the middle distance, Aunt Em waving from the porch. "
            "Dorothy walking toward her in bare feet, gingham mussed, "
            "Toto in her arms. The horizon is empty. The silver "
            "slippers are gone. Dorothy is smiling but the smile is "
            "smaller than it could have been."
        ),
        "evaluation_context": "Terminal ending — home but at a cost; partial preparation, partial return.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "partial",
        "transitions": [],
    },
    {
        "id": "ending_oz_forever",
        "title": "The country of Oz",
        "narrative": (
            "Without the silver slippers there is no way out of Oz. "
            "Glinda is kind but cannot help. The humbug's balloon "
            "flies away alone. The companions are good company and "
            "make a life with Dorothy in a small green house at the "
            "edge of the Emerald City. She does not stop missing the "
            "prairie or Aunt Em. She tells the story sometimes, on "
            "long evenings, to children of the country who have never "
            "seen Kansas. They do not believe her. They believe she "
            "has always been one of them."
        ),
        "visual_description": (
            "Dorothy several years older, in a green-edged Oz dress "
            "rather than gingham, sitting on the doorstep of a small "
            "stone house at the edge of the Emerald City. The "
            "Scarecrow on the bench beside her, the Tin Woodman in "
            "the doorway, the Lion lying at her feet. Toto, very "
            "grey-muzzled now, asleep across the Lion's paws. The sky "
            "above the city green as ever."
        ),
        "evaluation_context": "Terminal failure — no slippers means no return; Dorothy stays in Oz.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "failure",
        "transitions": [],
    },
    {
        "id": "ending_balloon_alone",
        "title": "The balloon",
        "narrative": (
            "The humbug is convincing. Dorothy boards the balloon "
            "without testing him. He pulls the ropes and rises with "
            "her in the basket and the green city falling away "
            "beneath them — and then a stay-rope, never quite "
            "fastened, slips, and the basket tips. Dorothy and Toto "
            "are dropped softly onto the grass outside the Emerald "
            "City. The balloon, now lighter, flies on with the humbug "
            "alone. He is never seen in Oz again. Dorothy stands at "
            "the green wall and the gates do not open to her — the "
            "Guardian believes she has gone with the Wizard. There is "
            "no road south she can find without help."
        ),
        "visual_description": (
            "A small girl in gingham, Toto in her arms, sitting on "
            "the grass at the foot of the green city wall in the "
            "evening light. The closed gates of the Emerald City "
            "above her. A balloon — a striped silk envelope with a "
            "wicker basket — high in the sky to the south, a small "
            "figure waving from it. The sun setting through the haze "
            "of the green city."
        ),
        "evaluation_context": "Terminal failure — credulity got Dorothy dropped at the wall, the humbug flew on alone.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "failure",
        "transitions": [],
    },
    {
        "id": "ending_wizard_unchallenged",
        "title": "The humbug's bargain",
        "narrative": (
            "The humbug pleads. He says exposing him would break the "
            "country's belief in itself; the Emerald City is held "
            "together by what the people think of him. Dorothy is "
            "moved, or angry, and demands he be punished — and in "
            "the negotiation that follows, she gives up her own wish "
            "for the silence. The humbug stays Oz the Great and "
            "Terrible. The companions are sent home with their "
            "gifts. Dorothy walks out of the throne room without her "
            "way to Kansas. She makes a slow life in Oz, working in "
            "the green city's kitchens, and writes letters to Aunt "
            "Em that never reach her."
        ),
        "visual_description": (
            "Dorothy in a green apron in a busy green-tiled kitchen "
            "in the City of Emeralds, peeling green vegetables at a "
            "long table. Other workers around her in green clothing. "
            "Toto under the table at her feet. A small high window "
            "showing green sky. She is older here, not by much, but "
            "the brightness of the prairie girl is muted."
        ),
        "evaluation_context": "Terminal failure — gave up her own way home in a bargain with the humbug.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "failure",
        "transitions": [],
    },
    {
        "id": "ending_poppy_sleep",
        "title": "Among the poppies",
        "narrative": (
            "The fumes are too much for a girl and her dog. Dorothy "
            "sinks first to her knees and then to her side, Toto "
            "pressed against her ribs. The Lion is already asleep "
            "across the road. There is no one to carry them. The sun "
            "moves slowly over the field. The field-mice eventually "
            "come, but they are too small and too few. By morning "
            "the field has accepted three travelers as it has "
            "accepted many. The road of yellow brick continues "
            "without them to a city Dorothy will not see."
        ),
        "visual_description": (
            "The scarlet poppy field in the soft morning after. Three "
            "still shapes on and beside the yellow road: a great "
            "tawny lion stretched across the path, a small girl "
            "curled on her side a few feet behind him, a small black "
            "dog pressed against her. The Emerald City visible on "
            "the green horizon, untouched."
        ),
        "evaluation_context": "Terminal failure — caught in the poppies without the friends who could have carried Dorothy across.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "failure",
        "transitions": [],
    },
    {
        "id": "ending_stranded",
        "title": "The yellow kitchen",
        "narrative": (
            "Without the bucket and the soapy water Dorothy is no "
            "match for the Wicked Witch. The Witch takes the second "
            "slipper. She locks Dorothy in the scullery with the "
            "Winkies who are also her prisoners. The Scarecrow's "
            "straw is left scattered in the yellow rocks. The Tin "
            "Woodman is left in dents. The Lion paces his cage. "
            "There is no broomstick for the Wizard. There is no way "
            "home. The Witch is patient and old, and a child in "
            "the scullery is a small problem for her, with time."
        ),
        "visual_description": (
            "The yellow scullery of the yellow castle, late at "
            "night. Dorothy in a corner with her arms around her "
            "knees, Toto pressed against her side. The Witch's "
            "shadow visible under the closed door. No slippers on "
            "Dorothy's feet. The bucket of scrubbing water across "
            "the floor, untouched."
        ),
        "evaluation_context": "Terminal failure — chose the wrong weapon against the Witch and was stranded in her castle.",
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
