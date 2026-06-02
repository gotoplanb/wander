from dataclasses import dataclass

SAMPLE_INTRO_1 = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"
SAMPLE_AMBIENT_1 = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
SAMPLE_INTRO_2 = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4"
SAMPLE_AMBIENT_2 = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4"


@dataclass
class Scene:
    id: str
    title: str
    narrative: str
    evaluation_context: str
    next_scene_id: str | None = None
    intro_video: str | None = None
    ambient_video: str | None = None
    is_terminal: bool = False


SCENES: dict[str, Scene] = {
    "opening": Scene(
        id="opening",
        title="The forest edge",
        intro_video=SAMPLE_INTRO_1,
        ambient_video=SAMPLE_AMBIENT_1,
        narrative=(
            "You stand at the edge of a darkening forest. A narrow path winds "
            "east beneath the trees. A stream burbles south toward open meadow. "
            "Behind you, the lights of the village have already faded."
        ),
        evaluation_context=(
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
        next_scene_id="forest",
    ),
    "forest": Scene(
        id="forest",
        title="Deeper in",
        intro_video=SAMPLE_INTRO_2,
        ambient_video=SAMPLE_AMBIENT_2,
        narrative=(
            "The trees close overhead. You find yourself in a small clearing "
            "where moss covers a flat stone slab. Something glints beneath it. "
            "From somewhere ahead, you hear water — but not the stream you left."
        ),
        evaluation_context=(
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
        next_scene_id="opening",
    ),
}
