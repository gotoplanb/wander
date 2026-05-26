# Wanderer — Product Specification v0.1

## Overview

Wanderer is a general-purpose AI-driven text adventure engine. Players navigate branching
narrative scenarios through typed input or AI-generated choices. Episode authors define
the world, the stakes, and the valid outcomes. The AI operates within that container —
generating choices, evaluating actions, and advancing the story — but never outside it.

The path is yours. The world is not.

---

## Core Concepts

### Engine vs. Episodes

Wanderer has two distinct layers:

**The engine** is the runtime. It handles rendering, input, AI orchestration, game state,
and mode switching. It knows nothing about specific stories.

**Episodes** are portable content packages stored as SQLite databases, bundled with
their MP4 assets in a folder. They define a complete scenario: scenes, branching logic,
evaluation criteria, video references, and authoring constraints. Episodes are independent
of the engine binary. They can be shared, versioned, and installed like software packages.
Anyone can author an episode and hand it to someone else to run.

### Scenes

A scene is the atomic unit of an episode. Each scene has:
- Two optional video slots (intro and ambient MP4)
- Narrative text describing the current situation
- Evaluation context — what the author considers good, plausible, and poor responses
- One or more possible transitions to other scenes, with conditions
- Optional metadata (difficulty weight, tags, SLA timers)

Scenes do not pre-write every possible player action. They define the space of valid
outcomes and let the AI interpret player input against that space.

### Episodes as Terrain

The episode author's job is to define terrain, not prescribe paths. They describe:
- What world the player is in
- What the stakes are
- What good judgment looks like at each decision point
- What the valid exits from each scene are
- What video assets belong to each scene

The AI's job is to interpret player actions against that terrain, evaluate quality,
generate choices (in easy mode), and determine which transition fires.

---

## Interaction Modes

### Easy Mode

The AI reads the current scene's evaluation context and generates three choices the
player might plausibly make — one clearly correct, one reasonable but flawed, one
a common mistake. The player selects one. The AI evaluates the selection and advances
the narrative.

Choice quality matters in authoring. The wrong options should reflect realistic errors
a reasonable but undertrained person would make — not obvious red herrings. A well-crafted
distractor teaches as much as the correct answer.

### Hard Mode

No scaffolding. The player types freely. The AI interprets intent, assesses correctness
against the evaluation context, and advances the narrative. This mode generates the most
realistic training signal and the most valuable evaluation data.

Both modes use identical episode content. The episode author does not need to write
separately for each mode.

---

## UI Layout

Wanderer uses a two-region layout inspired by early Sierra Online games (King's Quest era):

**Upper region (~65% of screen height)**
Scene video. Each scene has two MP4 slots: an intro clip that plays once on arrival,
followed by an ambient loop that runs until the player acts. A static scene is just
a single-frame MP4 that loops. The engine treats this as a display surface — it does
not interpret the video, it just plays it. Video sets visual context, atmosphere, and
optional ambient audio.

**Lower region (~35% of screen height)**
The text adventure interface. Displays narrative text describing the current situation,
followed by either:
- Easy mode: three AI-generated choice buttons
- Hard mode: a text input prompt

Evaluation feedback appears inline in the lower region after each action — what was
good, what was flawed, and a coaching note. The narrative then advances to the next scene.

No cursor-based movement. No inventory UI. No map. Interaction is purely through the
text layer.

---

## Episode Format (YAML Schema)

```yaml
id: unique_episode_id
title: "Human-readable episode title"
description: "One-line description shown in episode browser"
version: "1.0.0"
author: "Author name"
tags: [demo, ops, training, ...]

# Constrains the AI — defines the valid world for this episode.
# The AI must not generate choices or advance narrative outside this scope.
world_constraints: |
  Plain language description of what this episode is about, what domain
  the player is in, and what kinds of actions are in scope. This is passed
  to the AI as a system-level guardrail on every turn.

opening:
  ambient_video: "assets/opening_loop.mp4"
  narrative: |
    Multi-line text shown before the first scene begins.
    Sets the world and the player's role.

scenes:
  - id: scene_id
    title: "Short scene label (used in authoring/playtest views)"
    
    intro_video: "assets/scene_01_intro.mp4"    # optional — plays once on arrival
    ambient_video: "assets/scene_01_loop.mp4"   # optional — loops until player acts
    
    narrative: |
      What the player reads when they arrive at this scene.
      Describes the current situation.
    
    evaluation_context: |
      Instructions to the AI evaluator. Describes what good, plausible,
      and poor actions look like at this decision point. Written as if
      you are briefing a senior colleague on what to watch for.
      
      This field doubles as an automation rule — write it with that
      dual purpose in mind.
    
    # Optional: SLA timer. If set, player is on the clock.
    sla_seconds: 900  # 15 minutes
    sla_label: "Partner notification email required within 15 min"
    
    transitions:
      - condition: "player takes correct or reasonable action"
        next_scene: next_scene_id
      - condition: "player makes a specific common mistake"
        next_scene: consequence_scene_id
      - condition: "any action"   # catch-all fallback
        next_scene: default_next_id
    
    is_terminal: false
    outcome: null   # "success" | "failure" | "partial" if terminal

  - id: consequence_scene_id
    # ... consequence scenes teach through natural narrative result,
    # not just an evaluation message. Show what happens when you
    # make the wrong call.
```

---

## AI Responsibilities

The AI has four jobs in Wanderer. All four are scoped by the episode's world_constraints.

**1. Choice generation (easy mode only)**
Given the current scene's narrative and evaluation context, generate three choices:
one correct, one plausible-but-flawed, one common mistake. Choices should feel like
things a real person in this situation might genuinely consider.

**2. Action evaluation (both modes)**
Given the player's input and the scene's evaluation context, assess quality:
good / partial / poor. Return an explanation and a single coaching note.
Also return whether the action advances the incident (used for transition logic).

**3. Transition determination**
Given the evaluation result and the scene's defined transitions, determine which
scene fires next. The AI interprets player intent against transition conditions —
it does not require exact keyword matches.

**4. Narrative generation (optional, future)**
Optionally generate connective narrative text between scenes to make transitions
feel natural. Initially this can be handled by authored scene text alone.

---

## Modes of Use

### Play Mode
The learner experience. Easy or hard. Evaluation feedback after each action.
Score tracked across the episode. Debrief at completion.

### Author Mode
Episode creation. The author describes scenes, outcomes, and image references
in a structured interface or directly in YAML. Claude Code is the primary
authoring tool for v1 — a UI authoring mode is a future consideration.

### Playtest Mode
The author walks their own episode with editorial eyes. Not scored. After each
scene the author can flag issues, add notes, or mark transitions that feel wrong.
Playtest notes are stored separately from the episode content and used to guide
revision. This is distinct from playing — the goal is QA, not learning.

---

## Reference Implementation: Sierra Demo Episode

To validate the engine independently of any real-world content, the first episode
built on Wanderer is a Sierra Online-style adventure demo — a small self-contained
scenario in the style of King's Quest 1.

This episode:
- Has no domain-specific knowledge requirements (anyone can play and evaluate it)
- Exercises the full engine: scene rendering, both modes, branching, consequences
- Provides a reference for episode authors on structure and tone
- Is fun, which matters for adoption

The Sierra demo does not need to be long. Three to five scenes with meaningful
branching is sufficient to prove the engine.

---

## First Production Episode: Incident Response Training

The first real-world episode is an incident response training scenario for the
SRE/CloudOps team. It encodes the following workflow:

**Tier 1 responsibilities:**
- Acknowledge alert ("checking...") — MTTA is measured
- Execute the appropriate runbook
- Paste dashboard screenshot and link (with time range and filters set)
- Determine: hold-and-observe or escalate
- If escalating: write a Slack thread message naming the runbook used,
  how far they got, and why Tier 2 is needed

**Tier 2 responsibilities:**
- Read Tier 1's escalation context before acting
- Determine internal vs. external responsibility
  (signal: errors.responsibility_type field in logs)
- Assess booking availability across lines of business:
  - All LOBs at 100% failure → treat as P1, fifteen minute clock on partner email
  - Default to P1 behavior until scope is confirmed
- Ensure the appropriate party has been notified (internal incident email or
  external supplier notification with session IDs)
- If P1 scope: escalate to Tier 3 simultaneously, do not wait
- Write escalation message as a decision brief: impact scope, internal/external
  determination, priority assessment, actions already taken

**Tier 3:**
- Senior engineering leadership (SRE lead, platform engineering manager, DevOps manager)
- Receives a decision brief, not a status update
- Organizational and architectural authority

**Key training targets** (what people actually get wrong):
- Escalating before investigating
- Pasting dashboard links without time range set
- Not writing the escalation rationale message
- Missing the fifteen minute P1 email SLA
- Treating all escalations as the same regardless of LOB impact scope

---

## Scoring

Each player action is scored: good (2 points), partial (1 point), poor (0 points).
Final score is expressed as a percentage of maximum possible.

Ratings:
- 80%+ — Excellent
- 60–79% — Good
- Below 60% — Developing

A full debrief is shown at episode completion: each action, its evaluation, and
the coaching note. This is the primary learning artifact.

---

## Out of Scope for v1

- Multiplayer or shared sessions
- UI-based episode authoring (Claude Code is the v1 authoring tool)
- AI video generation (placeholder or static MP4 assets only for v1)
- Inventory, movement, or any Sierra-style cursor interaction
- Persistent user accounts or progress tracking across sessions
- Episode marketplace or sharing infrastructure

---

## Storage

Wanderer uses a two-file model with clean separation between content and state.

### episode.sqlite
The episode file is immutable during play. It contains everything needed to run
the episode: front matter, scenes, transitions, scene pools, image references,
world constraints, and evaluation context. It is never written to during gameplay.

The front matter table is the manifest — episode ID, title, author, version,
world constraints, Ollama model requirements, and any metadata the engine needs
to load and run the episode.

The episode file IS the episode. Sharing an episode means sharing this file.
Installing an episode means dropping it in a directory Wanderer scans at startup.

SQLite enables:
- Graph queries: "every scene that can reach this one," "dead end detection"
- Episode map derivation for playtest visualization
- Scene pools: multiple scenes of the same type the AI can select from,
  enabling genuine variation across runs of the same episode
- Richer playtest annotations stored relationally alongside episode content

YAML remains useful as a portable interchange format — episodes can serialize
to YAML for human review and deserialize back into SQLite. Authors work in
SQLite via Claude Code; YAML is an optional export format.

### session.sqlite (or flat file)
The session file captures a specific playthrough: player actions, timestamps,
AI evaluations, scores, and debrief data. It references the episode by ID but
never modifies it.

Session files are standalone artifacts. A completed session file can be shared
for review, archived for compliance, or compared against a later run of the same
episode. The format starts as a flat file and migrates to SQLite if querying
becomes useful.

Claude Code is the v1 authoring tool. A Wanderer-native authoring UI (powered by
local Ollama) is a future consideration for non-developer episode authors.

## Asset Bundling

An episode is a folder with a known structure:

```
my-episode/
  episode.sqlite
  assets/
    scene_01_intro.mp4
    scene_01_loop.mp4
    scene_02_intro.mp4
    scene_02_loop.mp4
```

Scenes reference assets by relative path (e.g. `assets/scene_02.mp4`). The engine
resolves paths against the episode folder at runtime. Remote assets are supported
by using an absolute URL in the same field — the engine treats any value starting
with `http` as a URL and everything else as a relative path.

Episodes are distributed as zip archives containing the full folder. For internal
team sharing this is sufficient. A hosted episode registry is a future consideration.

### Generation Prompt Storage

For AI-generated assets, the episode SQLite stores the generation prompt alongside
the asset path. This means a scene video can be regenerated, varied, or replaced
without losing the original intent. It also serves as documentation — future authors
can see exactly what was asked for and adjust the prompt rather than starting from
scratch.

```sql
-- assets table (illustrative)
asset_path        TEXT,   -- e.g. assets/scene_02_loop.mp4
generation_prompt TEXT,   -- e.g. "busy ops center at night, monitors flickering,
                          --       dim blue light, seamless loop, cinematic"
generation_model  TEXT,   -- e.g. "CogVideoX-5B"
generated_at      TEXT    -- ISO timestamp
```

Assets that are not AI-generated (screen recordings, filmed footage) simply leave
the generation fields null.

### Media Types

All scene visuals are MP4. Images are not a separate type — a static image is
just a single-frame MP4 that loops. One media format, consistent handling.

Each scene has two optional video slots, played in sequence:

**intro_video** — plays once when the scene loads. This is the action: the
transition, the thing that just happened, the table-setting moment. Plays through
to completion, then hands off to the ambient video automatically.

**ambient_video** — starts when the intro finishes (or immediately if there is no
intro). Loops until the player makes their choice. This is the world breathing:
flickering monitors, a stormy forest, a busy ops floor. Provides atmosphere and
optional ambient audio while the player reads and decides.

The rhythm this creates: action → breathe → decide → action → breathe → decide.

Both slots are optional. A scene with only an ambient video skips straight to the
loop. A scene with only an intro video plays once and holds on the last frame.
Audio is embedded in the MP4 — no separate audio format needed.

Episode schema for scene media:
```
intro_video: assets/scene_02_intro.mp4
ambient_video: assets/scene_02_loop.mp4
```

## Playtest Notes

Playtest notes are sidecar files — separate from the episode, stored alongside it.
This allows multiple people to playtest the same episode independently, share only
their notes with the author, and keep the episode file pristine.

Convention:

```
my-episode/
  episode.sqlite
  assets/
    ...
  playtests/
    dave_2026-05-26.sqlite
    patrick_2026-05-26.sqlite
```

Each sidecar references the episode by ID and scene IDs. It stores per-scene flags,
free-text notes, and revision suggestions. The author collects sidecars from multiple
playtesters, reviews the feedback, and revises the episode. Sidecars are shareable
independently — a playtester can send just their notes file without sharing their
full session data.
