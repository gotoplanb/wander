"""AI backend layer for Wanderer.

Two interchangeable backends both fulfill the AIBackend protocol:
- OllamaBackend: direct chat with a local/remote Ollama server, using
  Ollama's `format` parameter for schema-constrained output.
- ConductBackend: synchronous job submission to a Conduct service.
  Conduct does not enforce schema, so the client (us) is responsible
  for prompt-engineering JSON and post-validating with Pydantic.

Selected at import time via WANDERER_BACKEND env var. Any failure
(connection error, parse failure, schema mismatch) raises — callers
are expected to surface the error to the player, not paper over it.
"""

import json
import os
import re
from typing import Literal, Protocol

import httpx
from ollama import AsyncClient as OllamaAsyncClient
from pydantic import BaseModel, Field, ValidationError

from app.scenes import Scene

WANDERER_BACKEND = os.getenv("WANDERER_BACKEND", "ollama").lower()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
WANDERER_MODEL = os.getenv("WANDERER_MODEL", "llama3.1:8b")

CONDUCT_URL = os.getenv("CONDUCT_URL", "http://localhost:8000")
CONDUCT_API_KEY = os.getenv("CONDUCT_API_KEY", "")
CONDUCT_TASK_TYPE = os.getenv("CONDUCT_TASK_TYPE", "")


# --- Shared response models ----------------------------------------------


class GeneratedChoice(BaseModel):
    text: str
    quality: Literal["correct", "flawed", "mistake"]


class ChoicesResponse(BaseModel):
    choices: list[GeneratedChoice] = Field(min_length=3, max_length=3)


class Evaluation(BaseModel):
    verdict: Literal["good", "partial", "poor"]
    explanation: str
    coaching: str


# --- Shared prompts ------------------------------------------------------

_CHOICES_SYSTEM_PROMPT = """\
You generate three choices for a text adventure player at a decision point.

The choices must reflect what a real person in this situation might genuinely \
consider. A well-crafted distractor teaches as much as the correct answer — \
no obvious red herrings.

Generate exactly three choices:
- one that demonstrates clearly correct judgment (quality: "correct")
- one that is reasonable on its face but flawed in a non-obvious way (quality: "flawed")
- one that reflects a common mistake an undertrained person would make (quality: "mistake")

Each choice is a single action stated in first person, present tense, one sentence. \
Do NOT include the quality label in the visible text — the text is what the player \
reads as a button label.

Stay strictly within the scene as described. Do not invent objects, characters, or \
geography not mentioned in the scene or evaluation context.

OUTPUT FORMAT: Respond with a single JSON object and nothing else — no commentary, \
no markdown code fences, no preamble. Exact shape:
{"choices":[{"text":"...","quality":"correct"},{"text":"...","quality":"flawed"},{"text":"...","quality":"mistake"}]}
"""

_EVAL_SYSTEM_PROMPT = """\
You evaluate a player's action against the scene's standard of good judgment.

Return:
- verdict: "good" if the action reflects sound judgment; "partial" if it has merit \
  but misses something important; "poor" if it reflects a meaningful error.
- explanation: 1-2 sentences explaining the verdict. Address the player directly in \
  second person ("You..."). Be specific about what was right or wrong. Avoid generic \
  praise or criticism.
- coaching: 1-2 sentences of forward-looking advice tied to the specific error or \
  strength. Not a restatement of the explanation.

Do not invent consequences not implied by the scene. Do not advance the narrative — \
that is a separate step.

OUTPUT FORMAT: Respond with a single JSON object and nothing else — no commentary, \
no markdown code fences, no preamble. Exact shape:
{"verdict":"good|partial|poor","explanation":"...","coaching":"..."}
"""


def _scene_brief(scene: Scene) -> str:
    return (
        f"SCENE:\n{scene.narrative}\n\n"
        f"WHAT GOOD JUDGMENT LOOKS LIKE HERE:\n{scene.evaluation_context}"
    )


def _choices_user_prompt(scene: Scene) -> str:
    return f"{_scene_brief(scene)}\n\nGenerate three choices."


def _eval_user_prompt(scene: Scene, action_text: str) -> str:
    return (
        f"{_scene_brief(scene)}\n\nPLAYER ACTION:\n{action_text}\n\nEvaluate the action."
    )


# --- Defensive JSON extraction -------------------------------------------

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


def _extract_json_object(raw: str) -> str:
    """Strip markdown fences and slice from first { to last } (inclusive).

    Models that ignore "no fences" still tend to put one valid object somewhere
    in the response. We accept that and fail loudly only if no braces are present.
    """
    text = _FENCE_RE.sub("", raw).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"No JSON object found in response: {raw[:500]!r}")
    return text[start : end + 1]


def _parse_as(model_cls: type[BaseModel], raw: str) -> BaseModel:
    payload = _extract_json_object(raw)
    try:
        return model_cls.model_validate(json.loads(payload))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError(
            f"Could not parse {model_cls.__name__} from response.\n"
            f"--- error ---\n{exc}\n--- raw ---\n{raw[:1000]}"
        ) from exc


# --- Backend protocol ----------------------------------------------------


class AIBackend(Protocol):
    name: str

    async def generate_choices(self, scene: Scene) -> list[GeneratedChoice]: ...

    async def evaluate_action(self, scene: Scene, action_text: str) -> Evaluation: ...


# --- Ollama backend ------------------------------------------------------


class OllamaBackend:
    name = "ollama"

    def __init__(self, host: str, model: str) -> None:
        self.host = host
        self.model = model
        self._client = OllamaAsyncClient(host=host)

    async def _chat(self, system: str, user: str, schema: dict, temperature: float) -> str:
        response = await self._client.chat(
            model=self.model,
            format=schema,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            options={"temperature": temperature},
        )
        return response.message.content

    async def generate_choices(self, scene: Scene) -> list[GeneratedChoice]:
        raw = await self._chat(
            _CHOICES_SYSTEM_PROMPT,
            _choices_user_prompt(scene),
            ChoicesResponse.model_json_schema(),
            temperature=0.7,
        )
        return _parse_as(ChoicesResponse, raw).choices  # type: ignore[attr-defined]

    async def evaluate_action(self, scene: Scene, action_text: str) -> Evaluation:
        raw = await self._chat(
            _EVAL_SYSTEM_PROMPT,
            _eval_user_prompt(scene, action_text),
            Evaluation.model_json_schema(),
            temperature=0.3,
        )
        return _parse_as(Evaluation, raw)  # type: ignore[return-value]


# --- Conduct backend -----------------------------------------------------


class ConductBackend:
    name = "conduct"

    def __init__(self, url: str, api_key: str, task_type: str) -> None:
        if not api_key:
            raise RuntimeError("CONDUCT_API_KEY is required when WANDERER_BACKEND=conduct")
        if not task_type:
            raise RuntimeError("CONDUCT_TASK_TYPE is required when WANDERER_BACKEND=conduct")
        self.url = url.rstrip("/")
        self.task_type = task_type
        self._client = httpx.AsyncClient(
            base_url=self.url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(120.0),
        )

    async def _job(self, system: str, user: str) -> str:
        prompt = f"{system}\n\n---\n\n{user}"
        response = await self._client.post(
            "/jobs",
            json={"task_type": self.task_type, "prompt": prompt},
        )
        response.raise_for_status()
        envelope = response.json()
        text = envelope.get("response")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"Conduct envelope missing usable .response: {envelope}")
        return text

    async def generate_choices(self, scene: Scene) -> list[GeneratedChoice]:
        raw = await self._job(_CHOICES_SYSTEM_PROMPT, _choices_user_prompt(scene))
        return _parse_as(ChoicesResponse, raw).choices  # type: ignore[attr-defined]

    async def evaluate_action(self, scene: Scene, action_text: str) -> Evaluation:
        raw = await self._job(_EVAL_SYSTEM_PROMPT, _eval_user_prompt(scene, action_text))
        return _parse_as(Evaluation, raw)  # type: ignore[return-value]


# --- Selector ------------------------------------------------------------


def _build_backend() -> AIBackend:
    if WANDERER_BACKEND == "ollama":
        return OllamaBackend(host=OLLAMA_HOST, model=WANDERER_MODEL)
    if WANDERER_BACKEND == "conduct":
        return ConductBackend(url=CONDUCT_URL, api_key=CONDUCT_API_KEY, task_type=CONDUCT_TASK_TYPE)
    raise RuntimeError(
        f"Unknown WANDERER_BACKEND={WANDERER_BACKEND!r}. Use 'ollama' or 'conduct'."
    )


backend: AIBackend = _build_backend()


def backend_description() -> str:
    if WANDERER_BACKEND == "ollama":
        return f"ollama @ {OLLAMA_HOST} (model {WANDERER_MODEL})"
    return f"conduct @ {CONDUCT_URL} (task_type {CONDUCT_TASK_TYPE})"


# Module-level shortcuts so route handlers don't import the instance.

async def generate_choices(scene: Scene) -> list[GeneratedChoice]:
    return await backend.generate_choices(scene)


async def evaluate_action(scene: Scene, action_text: str) -> Evaluation:
    return await backend.evaluate_action(scene, action_text)
