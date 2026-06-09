"""Seed `episodes/lost-tail/episode.sqlite`.

A playable adaptation in the spirit of A. A. Milne's WINNIE-THE-POOH (1926)
— public domain in the United States as of 1 January 2022. Eeyore has lost
his tail and Pooh, being a friendly bear, has agreed to find it. The
tail-as-bell-pull-at-Owl's is the central beat from Chapter IV of the book.

Source: Milne's 1926 book exclusively (and where relevant, 1928's THE HOUSE
AT POOH CORNER — also PD as of 2024). The Disney red shirt and all post-
Milne stylings are OUT OF SCOPE: Pooh wears nothing; "bother" is the
strongest exclamation; the tone is gentle and matter-of-fact without irony.

Structural pattern follows the established episodes: 7 active scenes, 5
terminal endings, 5 boolean state flags. Final scene branches on state AND
action via the in-world enumeration template. Lower-stakes register than
the other episodes — judgment is measured in kindness, patience, and
attention, not in survival.

Idempotent — drops and recreates the DB.
"""

import json
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
EPISODE_DIR = REPO_ROOT / "episodes" / "lost-tail"
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
    "id": "lost-tail",
    "title": "The Lost Tail",
    "description": (
        "Eeyore has lost his tail and is more melancholy about it than "
        "usual. You are Pooh, a Bear of Very Little Brain but a steady "
        "heart, and you have offered to find it. The tail has been "
        "borrowed by someone in the Forest as a useful thing, and you "
        "must visit your friends carefully to find out where. A short, "
        "kind adventure in the spirit of A. A. Milne's 1926 book."
    ),
    "version": "0.1.0",
    "author": "Dave Stanton",
    "world_constraints": (
        "Source: A. A. Milne's WINNIE-THE-POOH (1926) — public domain in "
        "the United States as of 1 January 2022 — and where appropriate "
        "THE HOUSE AT POOH CORNER (1928), also public domain as of 1 "
        "January 2024. Use Milne's BOOKS exclusively. The Disney "
        "adaptations and all post-Milne stylings are OUT OF SCOPE: Pooh "
        "wears NOTHING (no red shirt — Disney addition); the tone is "
        "Milne's gentle matter-of-fact narration without irony, "
        "snark, or modern American idiom; 'Bother' is the strongest "
        "exclamation; specific Disney character designs, songs, plots, "
        "and added characters (Gopher) are NOT in scope.\n\n"
        "The PLAYER is Winnie-the-Pooh, sometimes called Pooh Bear, "
        "Edward Bear, or simply Pooh. He/him pronouns. A Bear of Very "
        "Little Brain (his own gentle self-description, used "
        "affectionately and never as an insult). He is small, fond of "
        "honey, slow but loyal, friendly to all and especially to "
        "Christopher Robin and Piglet. He is NOT cynical, sarcastic, "
        "world-weary, or in possession of adult vocabulary. He thinks "
        "slowly and out loud; he hums; he sometimes invents a 'hum' "
        "(a little song) about whatever is happening.\n\n"
        "Named characters and what they are:\n"
        "- Christopher Robin: a small boy of perhaps six or seven who "
        "is friend and quiet authority to all the Forest animals. He "
        "lives at the edge of the Forest. He/him. He is kind, patient, "
        "and always treats the animals seriously, never indulgently.\n"
        "- Piglet: a Very Small Animal, pink, with a striped scarf "
        "knitted by his Grandfather Trespassers Will. He/him. Anxious "
        "by nature but brave when the moment calls. Pooh's closest "
        "friend. Lives in a beech tree with a sign reading TRESPASSERS W.\n"
        "- Rabbit: a fussy, organized animal who lives in a sandy hole "
        "with many tunnels. He/him. Rather proud of his many friends-"
        "and-relations and rather inclined to organize everyone. "
        "Generous with honey, jam, and condensed milk but mildly put "
        "out at unannounced visits.\n"
        "- Owl: a large brown owl who lives in a chestnut called The "
        "Chestnuts. He/him. Believes himself wise and well-read; he "
        "can in fact only spell his own name (and that wrong: WOL). "
        "Uses a long word where a short one would do.\n"
        "- Kanga: a kangaroo who arrived in the Forest with her son "
        "Roo. She/her. Calm, motherly, gently practical, carries Roo "
        "in her pocket.\n"
        "- Roo: Kanga's infant son. He/him. Excitable and tireless.\n"
        "- Eeyore: a gloomy grey donkey who lives in a field of "
        "thistles. He/him. Believes the worst will happen and is "
        "vindicated when it does. His tail is fixed on with a pin and "
        "comes off from time to time. Has just lost it again.\n\n"
        "Locations: the Hundred Acre Wood (everything happens there). "
        "Specific places: Eeyore's thistly field, Christopher Robin's "
        "house at the edge of the Forest with the green door, Rabbit's "
        "hole, Owl's chestnut tree (called The Chestnuts), Piglet's "
        "house in the beech, Kanga's house at the sandy edge of the "
        "Forest.\n\n"
        "Reject actions that import: modern slang, irony, sarcasm, "
        "real-world technology, anything cynical, any character not "
        "in Milne (no Gopher, no invented siblings, no boy/girlfriends, "
        "no extended family unless given by Milne). Tail is fixed on "
        "with a pin (Milne's detail), not with anything else. Pooh "
        "does not speak about anyone unkindly; the worst he says is "
        "'Bother.'"
    ),
    "opening_scene_id": "eeyores_field",
    "initial_world_state": {
        "asked_christopher_robin": False,
        "treated_rabbit_kindly": False,
        "helped_kanga": False,
        "noticed_at_owls": False,
        "piglet_helped": False,
    },
}


SCENES = [
    # ---------- 1. Eeyore's field ----------
    {
        "id": "eeyores_field",
        "title": "Eeyore's thistly field",
        "narrative": (
            "Eeyore is standing in the middle of his field of thistles, "
            "looking gloomily at the place where his tail should be. "
            "When he hears you coming, he does not turn around. 'Good "
            "morning, Pooh Bear,' he says. 'If it is a good morning, "
            "which I doubt.' You go round to look at him properly and "
            "you see at once that his tail is missing. There is only "
            "the place where the pin should hold it on, and the pin is "
            "still there, but the tail is not. Eeyore sighs. He says "
            "he has lost it. He says, with no real hope, that someone "
            "in the Forest must have taken it for a useful thing. He "
            "would like it back, please, very much, although he does "
            "not expect anything."
        ),
        "visual_description": (
            "A wide thistly field under a grey but kindly sky. Eeyore — "
            "a small grey donkey with long ears and a melancholy "
            "expression — standing in the middle of the field with his "
            "back to the camera at first, then turning to face Pooh. "
            "Where his tail should be there is only a small bow of "
            "pink ribbon and a brass pin, no tail. Pooh: a small bear "
            "of golden-brown plush, no clothing, standing at the edge "
            "of the field with his round face concerned. The path to "
            "the rest of the Forest behind him."
        ),
        "evaluation_context": (
            "Opening. Pooh has offered to look for Eeyore's tail. The "
            "question is how he begins. Good judgment: take a moment "
            "with Eeyore to be sure he is heard (Eeyore feels worst "
            "when he is hurried), then set out toward Christopher "
            "Robin's house — Christopher Robin will know what to do, "
            "and Pooh always knows to ask Christopher Robin first when "
            "a thing is too big to solve alone. Reasonable but flawed: "
            "rush off at once without sitting with Eeyore — well-meant "
            "but Eeyore will feel he was not listened to, which is "
            "the part of the trouble he feels worst about. No flag. "
            "Common mistake: make a Promise to find it Today, in a "
            "loud voice, the way bears in stories do. Eeyore will "
            "shake his head and say he expected something like that. "
            "No flag. All three transitions go to christopher_robins_"
            "door."
        ),
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "Pooh sits with Eeyore a moment, lets him be heard, then sets off toward Christopher Robin's house",
                "next_scene_id": "christopher_robins_door",
            },
            {
                "condition": "Pooh rushes off at once without taking time with Eeyore",
                "next_scene_id": "christopher_robins_door",
            },
            {
                "condition": "Pooh makes a big loud Promise to find the tail before tea-time",
                "next_scene_id": "christopher_robins_door",
            },
        ],
    },
    # ---------- 2. Christopher Robin's door ----------
    {
        "id": "christopher_robins_door",
        "title": "The green door",
        "narrative": (
            "Christopher Robin's house is at the edge of the Forest "
            "where a great oak grows beside a green door. You knock. "
            "Christopher Robin opens it himself, in a blue smock, with "
            "a piece of marmalade toast in his hand. When you tell him "
            "about Eeyore's tail, he thinks about it carefully — "
            "Christopher Robin always thinks before he speaks, which "
            "is one of the things you most like about him — and he "
            "says: 'I should ask everyone you meet today, Pooh Bear. "
            "Someone may have it without quite knowing it is a tail.' "
            "He gives you half the marmalade toast for the journey."
        ),
        "visual_description": (
            "The edge of the Forest where it opens into a clearing "
            "with a small white-painted house with a green door under "
            "a great old oak. Christopher Robin — a small boy of six "
            "or seven, fair-haired, in a blue smock and short trousers "
            "and Wellington boots — standing in the doorway with half "
            "a piece of marmalade toast in his hand. Pooh small in "
            "front of him, holding his paw out for the other half. "
            "Morning light through the oak's leaves."
        ),
        "evaluation_context": (
            "Pooh asks Christopher Robin for help. Good judgment: ask "
            "Christopher Robin directly and simply, accept his advice "
            "to ask everyone you meet, eat the marmalade toast he "
            "gives you (not eating it would be rude). Set asked_"
            "christopher_robin=True. Reasonable but flawed: tell "
            "Christopher Robin a long roundabout story about Eeyore's "
            "sadness without asking the question (Christopher Robin "
            "will give the same advice but you will have lost half the "
            "morning). No flag. Common mistake: insist that you, Pooh, "
            "can find the tail by yourself without anyone's help — "
            "this is the kind of pride that, in Milne, leads to "
            "circling a tree following one's own tracks. No flag. All "
            "three transitions go to rabbits_hole."
        ),
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "Pooh asks Christopher Robin directly and simply, takes the advice and the toast",
                "next_scene_id": "rabbits_hole",
                "state_delta": {"asked_christopher_robin": True},
            },
            {
                "condition": "Pooh tells a long story about Eeyore without asking the question clearly",
                "next_scene_id": "rabbits_hole",
            },
            {
                "condition": "Pooh insists he can find the tail by himself and turns down advice",
                "next_scene_id": "rabbits_hole",
            },
        ],
    },
    # ---------- 3. Rabbit's hole ----------
    {
        "id": "rabbits_hole",
        "title": "Rabbit's hole",
        "narrative": (
            "Rabbit's hole is in a sandy bank with a polished wooden "
            "door at the top. You knock. Rabbit puts his head out. "
            "Behind him, you can see his neat sitting-room with the "
            "honey pots arranged on a shelf and the condensed milk in "
            "tins. 'Oh,' says Rabbit, who has been expecting his "
            "friends-and-relations, 'it's you, Pooh.' He asks you in "
            "out of politeness rather than enthusiasm. He has not "
            "seen Eeyore's tail. He has not been near Eeyore in days. "
            "Would you like a little smackerel of something, he asks, "
            "in the tone of a host who would prefer you said no."
        ),
        "visual_description": (
            "A sandy bank at the side of a Forest path, a small wooden "
            "door set into it with a polished brass knob. Rabbit — a "
            "neat brown rabbit with long ears and an organized "
            "expression — standing in the doorway in a small green "
            "waistcoat, an apron over it. Through the doorway behind "
            "him: a tidy round sitting-room with a low table, shelves "
            "of honey pots, three or four tins of condensed milk in "
            "a row. Pooh on the threshold, small, hungry-looking."
        ),
        "evaluation_context": (
            "Pooh's central failing is honey. Rabbit's central failing "
            "is fussiness. Good judgment: accept a small amount only "
            "(or none) so as not to put Rabbit out — Pooh has had "
            "many adventures stuck in Rabbit's doorway from eating "
            "too much, and he remembers — ask politely about the "
            "tail, leave when Rabbit shows you are no longer needed. "
            "Set treated_rabbit_kindly=True. Reasonable but flawed: "
            "stay longer than the visit needed because the honey is "
            "very good, then ask about the tail at the end as you "
            "leave. Rabbit will fuss but Pooh will get the answer "
            "(no tail seen). No flag. Common mistake: eat as much "
            "honey as is offered and a bit more. Pooh will be stuck "
            "in the doorway for an hour. No flag and a sore middle. "
            "All three transitions go to kangas_house."
        ),
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "Pooh accepts only a little, asks about the tail politely, leaves when the visit is over",
                "next_scene_id": "kangas_house",
                "state_delta": {"treated_rabbit_kindly": True},
            },
            {
                "condition": "Pooh stays for a long while because the honey is very good, then asks about the tail",
                "next_scene_id": "kangas_house",
            },
            {
                "condition": "Pooh eats as much honey as offered and a bit more — gets stuck in the doorway",
                "next_scene_id": "kangas_house",
            },
        ],
    },
    # ---------- 4. Kanga's house ----------
    {
        "id": "kangas_house",
        "title": "Kanga's house",
        "narrative": (
            "Kanga's house is at the sandy edge of the Forest. She is "
            "in her front garden hanging out small handkerchiefs to "
            "dry. Roo is in her pocket — only his head and one paw "
            "out — and he is bouncing his head excitedly because here "
            "comes Pooh. 'Hello, Pooh dear,' says Kanga. She asks if "
            "Pooh would like some malt extract; she has had Roo on "
            "his and it has done him a great deal of good. Roo tries "
            "to leap out of her pocket to come and play. Kanga puts "
            "her paw down to steady him without scolding."
        ),
        "visual_description": (
            "A small whitewashed house at the sandy edge of the "
            "Forest, a low picket fence around the front garden. "
            "Kanga — a tall slim kangaroo, kind-faced — at a "
            "clothesline strung between two posts, pinning small "
            "handkerchiefs to it. Roo in her belly-pocket, only his "
            "head and one paw out, bouncing eagerly toward Pooh. "
            "Pooh in the gate, small and pleased to be seen. The "
            "morning sun warming everything."
        ),
        "evaluation_context": (
            "Pooh's visit to Kanga is a kindness scene. Good "
            "judgment: greet Kanga warmly, accept the malt extract "
            "if she insists (it is very nasty but accepting is "
            "kind), say a kind word to Roo and play a small game "
            "with him for a moment so he feels visited, ask about "
            "the tail. Set helped_kanga=True. Kanga has not seen "
            "the tail. Reasonable but flawed: greet Kanga but "
            "ignore Roo, take the malt extract reluctantly, ask "
            "only about the tail. Kanga will tell what she knows "
            "but Roo will be sad and Kanga will notice. No flag. "
            "Common mistake: refuse the malt extract loudly because "
            "it is nasty, then ask only about Pooh's quest. Both "
            "Kanga and Roo will feel Pooh did not really visit. No "
            "flag. All three transitions go to owl_pavilion."
        ),
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "Pooh greets Kanga warmly, accepts the malt extract, plays a small moment with Roo",
                "next_scene_id": "owl_pavilion",
                "state_delta": {"helped_kanga": True},
            },
            {
                "condition": "Pooh greets Kanga but ignores Roo and asks only about the tail",
                "next_scene_id": "owl_pavilion",
            },
            {
                "condition": "Pooh refuses the malt extract loudly and presses straight on with his question",
                "next_scene_id": "owl_pavilion",
            },
        ],
    },
    # ---------- 5. Owl's pavilion (the key scene) ----------
    {
        "id": "owl_pavilion",
        "title": "The Chestnuts",
        "narrative": (
            "Owl lives in a chestnut he has named The Chestnuts. His "
            "front door is high in the trunk and there is a long grey "
            "string hanging down beside it with a notice underneath: "
            "PLES RING IF AN RNSER IS REQUIRD. There is also a knocker "
            "with a notice: PLES CNOKE IF AN RNSER IS NOT REQUIRD. "
            "(Owl's spelling is his own.) You pull the long grey "
            "string and the bell rings somewhere inside. Owl appears "
            "in the doorway and is very pleased to see you and at "
            "once begins to tell you a long story about how he has "
            "just been writing a notice in seven letters."
        ),
        "visual_description": (
            "Inside Owl's house at the top of the tall chestnut. A "
            "round dim sitting-room with a low ceiling, a small "
            "fire, a number of pictures hanging slightly crooked, "
            "and on the wall by the door: a hand-lettered notice "
            "with 'PLES RING IF AN RNSER IS REQUIRD' that Owl is "
            "particularly proud of. The bell-pull on the outside "
            "wall of the chestnut: a long grey string with — at the "
            "end of it, attached as the actual bell-pull — a small "
            "tuft of grey hair with a faded pink bow at the top. "
            "Owl: a large brown owl in steel spectacles, holding "
            "forth. Pooh listening politely but looking past Owl at "
            "the bell-pull, where the tuft of grey hair with the "
            "pink bow is unmistakably a donkey's tail."
        ),
        "evaluation_context": (
            "The pivotal scene. The tail is here, IN PLAIN SIGHT, "
            "being used by Owl as a bell-pull (he found it in the "
            "Forest some days ago and thought it would do nicely). "
            "Owl does not realize it is a tail. The question is "
            "whether Pooh notices. Good judgment: listen patiently "
            "to Owl's story (Owl needs to be heard before he will "
            "listen), then SAY WHAT POOH SEES — that the bell-pull "
            "is, in fact, Eeyore's tail — and ask Owl kindly if he "
            "might return it. Owl, surprised, will of course agree. "
            "Set noticed_at_owls=True. Reasonable but flawed: notice "
            "the tail but be too polite to interrupt Owl's long "
            "story; the tail stays where it is until next time. No "
            "flag — Eeyore's tail is still missing. Common mistake: "
            "do not look around the room at all; only listen to "
            "Owl; leave without seeing the tail at all. No flag. "
            "All three transitions go to piglets_house."
        ),
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "Pooh listens to Owl, then notices the bell-pull is Eeyore's tail and asks for it back",
                "next_scene_id": "piglets_house",
                "state_delta": {"noticed_at_owls": True},
            },
            {
                "condition": "Pooh notices the tail but is too polite to interrupt and leaves without mentioning it",
                "next_scene_id": "piglets_house",
            },
            {
                "condition": "Pooh only listens and does not look around the room — does not see the tail",
                "next_scene_id": "piglets_house",
            },
        ],
    },
    # ---------- 6. Piglet's house ----------
    {
        "id": "piglets_house",
        "title": "Trespassers W.",
        "narrative": (
            "Piglet's house is in a beech tree in the middle of the "
            "Forest, with a sign by the door reading TRESPASSERS W. — "
            "which Piglet says is short for the name of his "
            "grandfather, Trespassers William. Piglet is at his front "
            "door looking out anxiously when you arrive; he is a Very "
            "Small Animal and you are very glad to see him. He has "
            "not seen Eeyore's tail. But he says — as he always "
            "does — that he would very much like to help, if there "
            "is anything a Very Small Animal can do."
        ),
        "visual_description": (
            "A large beech tree in a small Forest clearing. A small "
            "door set into the trunk at the bottom, beside it a "
            "wooden sign on a post: TRESPASSERS W. Piglet — a small "
            "pink pig animal in a long striped scarf knitted by his "
            "Grandfather — standing in the doorway, looking up "
            "anxiously at Pooh. The clearing dappled with afternoon "
            "light through the leaves. Pooh small but solid in front "
            "of the door."
        ),
        "evaluation_context": (
            "Piglet is a Very Small Animal and is happiest when made "
            "to feel useful. Good judgment: tell Piglet about "
            "Eeyore's tail kindly, ask him to come along to "
            "Eeyore's field for moral support and to be there when "
            "the tail is returned — Piglet's presence will please "
            "Eeyore, and being asked will please Piglet. Set piglet_"
            "helped=True. Reasonable but flawed: tell Piglet about "
            "the tail but say you can manage on your own from here — "
            "Piglet will smile bravely but Pooh will have missed a "
            "kindness and Eeyore will have one fewer friend at the "
            "field. No flag. Common mistake: tell Piglet but "
            "complain about Owl's long story and how Pooh is doing "
            "all the work — Piglet will be alarmed and Pooh will "
            "have made the day about himself. No flag. All three "
            "transitions go to return_to_eeyore."
        ),
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "Pooh tells Piglet about the tail kindly and asks him to come along to Eeyore's field",
                "next_scene_id": "return_to_eeyore",
                "state_delta": {"piglet_helped": True},
            },
            {
                "condition": "Pooh tells Piglet but says he can manage alone from here",
                "next_scene_id": "return_to_eeyore",
            },
            {
                "condition": "Pooh complains about his day to Piglet, making it about himself",
                "next_scene_id": "return_to_eeyore",
            },
        ],
    },
    # ---------- 7. Return to Eeyore (final) ----------
    {
        "id": "return_to_eeyore",
        "title": "Back at the thistly field",
        "narrative": (
            "The sun is past its highest when you come back across "
            "the bridge to Eeyore's field. Eeyore is exactly where he "
            "was that morning. He has, perhaps, moved one step. He "
            "looks at you when you come up — at you, and at "
            "whatever you have brought, and at whoever has come with "
            "you. He does not say anything. He waits."
        ),
        "visual_description": (
            "The thistly field again in the gentle afternoon light. "
            "Eeyore in the middle of it, standing with his head a "
            "little low, looking at Pooh. Pooh small at the edge "
            "of the field, in front of the camera. Behind him: "
            "Piglet (if helped), small and earnest with his striped "
            "scarf. The tail (if noticed at Owl's) held in Pooh's "
            "paws, a tuft of grey hair with a pink bow."
        ),
        "evaluation_context": (
            "FINAL SCENE. Routing is state-and-action-driven; verdict "
            "is judgment-driven.\n\n"
            "Five preparation conditions on the WORLD STATE block "
            "track what Pooh did today: asked Christopher Robin "
            "(asked_christopher_robin), was kind at Rabbit's "
            "(treated_rabbit_kindly), visited Kanga and Roo with "
            "warmth (helped_kanga), NOTICED the bell-pull was the "
            "tail at Owl's (noticed_at_owls), brought Piglet along "
            "(piglet_helped). The action NAMED here picks the path; "
            "the count modulates it.\n\n"
            "ROUTING:\n"
            "- Pooh presents the tail simply and warmly AND 4–5 "
            "conditions met → 0 (Eeyore is genuinely cheered; "
            "Christopher Robin will nail the tail back on; the "
            "Forest is a better place — ending_eeyore_cheerful).\n"
            "- Presents the tail AND 2–3 conditions met → 1 (Eeyore "
            "is grateful but a little quiet; partial return — "
            "ending_eeyore_quiet).\n"
            "- noticed_at_owls is FALSE → 2 (Pooh has come back "
            "without the tail at all; Eeyore is exactly as sad as "
            "before — ending_tail_still_lost).\n"
            "- Pooh presents the tail with a long boastful story "
            "about how clever he was → 3 (Eeyore feels smaller, not "
            "bigger; the tail is back but the day is spoiled — "
            "ending_eeyore_smaller).\n"
            "- Pooh delivers the tail and leaves at once because he "
            "is hungry → 4 (functional return; Eeyore is alone "
            "again with his tail — ending_lonely_eeyore).\n\n"
            "VERDICT: good = warm, simple, present with Eeyore; "
            "partial = hedged or rushed; poor = boastful or self-"
            "centered.\n\n"
            "Explanation and coaching are in the narrator's voice "
            "to Pooh at the field. NEVER use 'flags', 'world "
            "state', 'transition', or engine terminology — refer to "
            "what Pooh did today ('You sat with Eeyore; you asked "
            "Christopher Robin; you were kind at Rabbit's; you "
            "visited Kanga; you noticed the bell-pull; you brought "
            "Piglet'). Keep the tone Milne's: gentle, plain, no "
            "irony. No state_delta."
        ),
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": False,
        "outcome": None,
        "transitions": [
            {
                "condition": "Pooh presents the tail simply and warmly with four or five kindnesses behind him",
                "next_scene_id": "ending_eeyore_cheerful",
            },
            {
                "condition": "Pooh presents the tail with only two or three kindnesses behind him",
                "next_scene_id": "ending_eeyore_quiet",
            },
            {
                "condition": "Pooh did not notice the tail at Owl's and has come back with nothing",
                "next_scene_id": "ending_tail_still_lost",
            },
            {
                "condition": "Pooh presents the tail with a long boastful story about his own cleverness",
                "next_scene_id": "ending_eeyore_smaller",
            },
            {
                "condition": "Pooh delivers the tail and leaves at once because he is hungry",
                "next_scene_id": "ending_lonely_eeyore",
            },
        ],
    },
    # ---------- Terminal endings ----------
    {
        "id": "ending_eeyore_cheerful",
        "title": "Eeyore at the bridge",
        "narrative": (
            "Eeyore looks at his tail in your paws and then at Piglet "
            "behind you and at you and back at the tail. He does not "
            "say anything for a long moment. Then he says, 'That's "
            "kind of you, Pooh. That's really very kind.' Piglet "
            "comes forward and offers to help hold the tail steady. "
            "You walk together to Christopher Robin's house, where "
            "Christopher Robin nails the tail back on with great "
            "care and a small hammer. Eeyore looks round at his tail "
            "to be sure it is properly his again. 'Yes,' he says. "
            "'That's it.' He gives a slow wag. It is the closest "
            "thing to happiness he has had in some time, and it is "
            "enough."
        ),
        "visual_description": (
            "Christopher Robin's clearing in the late afternoon. "
            "Eeyore standing with his tail freshly pinned on, "
            "looking back at it. Christopher Robin kneeling beside "
            "him with a small hammer, smiling. Pooh on Eeyore's "
            "other side, paws clasped. Piglet behind, beaming. "
            "Eeyore's grey ear angled the way a donkey's ear "
            "angles when something is, for once, all right."
        ),
        "evaluation_context": "Terminal ending — tail returned with kindness; Eeyore is genuinely cheered.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "success",
        "transitions": [],
    },
    {
        "id": "ending_eeyore_quiet",
        "title": "Eeyore's tail back",
        "narrative": (
            "Eeyore takes the tail with a small nod and lets "
            "Christopher Robin pin it on at the end of the "
            "afternoon. He thanks you, politely but quietly. He "
            "stands in his field again with his tail proper, "
            "looking at the thistles. It is, on the whole, a "
            "better afternoon than the morning was. That is the "
            "kind of small good thing the Forest has, on its "
            "better days."
        ),
        "visual_description": (
            "Eeyore in his thistly field at evening, his tail "
            "pinned back on, head down at the thistles. Pooh "
            "small at the edge of the field, paw raised in a "
            "small wave. The sky pinkening toward dusk."
        ),
        "evaluation_context": "Terminal ending — tail back, but with a smaller warmth than it could have been.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "partial",
        "transitions": [],
    },
    {
        "id": "ending_tail_still_lost",
        "title": "Without the tail",
        "narrative": (
            "You come back without the tail. Eeyore looks at you. "
            "He looks at you and at where the tail should be and at "
            "you again. He does not say anything for a long time. "
            "When he does say something, he says, 'Thank you, Pooh. "
            "I knew you would try.' He turns his head away because "
            "he does not want you to see him being any sadder than "
            "usual. You go home with the feeling, very strong, that "
            "the tail was somewhere today and you missed it. "
            "Tomorrow, perhaps, you will look again."
        ),
        "visual_description": (
            "Eeyore in his thistly field in the late afternoon, "
            "head turned away, the place where his tail should be "
            "still empty. Pooh small at the edge of the field, "
            "ears down, paws empty."
        ),
        "evaluation_context": "Terminal failure — Pooh did not notice the bell-pull at Owl's; tail still lost.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "failure",
        "transitions": [],
    },
    {
        "id": "ending_eeyore_smaller",
        "title": "A long story",
        "narrative": (
            "Eeyore listens to your story about how Owl was using "
            "his tail as a bell-pull and how YOU were the one who "
            "noticed and how clever it really was of YOU to notice "
            "such a thing. He listens to all of it. When you have "
            "finished, he takes the tail with a small nod and "
            "thanks you, very quietly. He has gone smaller "
            "somewhere inside himself. The tail is back on by "
            "evening. It does not make as much difference as it "
            "should have."
        ),
        "visual_description": (
            "Eeyore in his field at evening with his tail pinned "
            "back on but standing very still, head low, the "
            "thistles around him. Pooh small at the edge of the "
            "field, paws still raised in the last gesture of his "
            "story. The afternoon light just slightly cold."
        ),
        "evaluation_context": "Terminal failure — tail returned but Pooh's boasting made Eeyore feel smaller, not bigger.",
        "intro_video": None,
        "ambient_video": None,
        "is_terminal": True,
        "outcome": "failure",
        "transitions": [],
    },
    {
        "id": "ending_lonely_eeyore",
        "title": "Off to look for honey",
        "narrative": (
            "You hand Eeyore his tail with a paw and turn "
            "immediately for home because you are thinking, very "
            "strongly, about honey. Eeyore takes the tail in his "
            "teeth (he can hold it that way until he finds "
            "Christopher Robin to pin it back on). 'Thank you, "
            "Pooh,' he says. You are already on the path. He stands "
            "in his field alone, the tail in his teeth. The Forest "
            "is very quiet around him. He will find Christopher "
            "Robin presently. It is, all in all, only a small "
            "spoiling of an afternoon — but it is one Eeyore "
            "remembers, in the way Eeyores remember small "
            "spoilings of afternoons."
        ),
        "visual_description": (
            "Eeyore in his thistly field, the tail held in his "
            "teeth, head low, watching Pooh's small retreating "
            "back on the path through the trees. The field very "
            "empty around him. The afternoon light unspoiled but "
            "the moment slightly so."
        ),
        "evaluation_context": "Terminal failure — tail delivered but Pooh's hunger pulled him away from the moment Eeyore needed.",
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
