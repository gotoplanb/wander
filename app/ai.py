"""Ollama backend for Wanderer's FastAPI playtest UI.

The end-user playtest path: git clone, install Ollama with the recommended
model, run uvicorn. The MCP authoring path does NOT use this module.
"""

import json
import os
import re
from typing import Any

from ollama import AsyncClient as OllamaAsyncClient
from pydantic import BaseModel, ValidationError

from app.models import ChoicesResponse, Evaluation, GeneratedChoice
from app.prompts import (
    CHOICES_SYSTEM_PROMPT,
    EVAL_SYSTEM_PROMPT,
    choices_user_prompt,
    eval_user_prompt,
)
from app.scenes import Scene

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
WANDERER_MODEL = os.getenv("WANDERER_MODEL", "gemma4:e4b")


_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


def _extract_json_object(raw: str) -> str:
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


class OllamaBackend:
    name = "ollama"

    def __init__(self, host: str, model: str) -> None:
        self.host = host
        self.model = model
        self._client = OllamaAsyncClient(host=host)

    async def _chat(
        self, system: str, user: str, schema: dict, temperature: float
    ) -> str:
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

    async def generate_choices(
        self, scene: Scene, world_state: dict[str, Any]
    ) -> list[GeneratedChoice]:
        raw = await self._chat(
            CHOICES_SYSTEM_PROMPT,
            choices_user_prompt(scene, world_state),
            ChoicesResponse.model_json_schema(),
            temperature=0.7,
        )
        return _parse_as(ChoicesResponse, raw).choices  # type: ignore[attr-defined]

    async def evaluate_action(
        self, scene: Scene, action_text: str, world_state: dict[str, Any]
    ) -> Evaluation:
        raw = await self._chat(
            EVAL_SYSTEM_PROMPT,
            eval_user_prompt(scene, action_text, world_state),
            Evaluation.model_json_schema(),
            temperature=0.3,
        )
        return _parse_as(Evaluation, raw)  # type: ignore[return-value]


backend = OllamaBackend(host=OLLAMA_HOST, model=WANDERER_MODEL)


def backend_description() -> str:
    return f"ollama @ {OLLAMA_HOST} (model {WANDERER_MODEL})"


async def generate_choices(
    scene: Scene, world_state: dict[str, Any]
) -> list[GeneratedChoice]:
    return await backend.generate_choices(scene, world_state)


async def evaluate_action(
    scene: Scene, action_text: str, world_state: dict[str, Any]
) -> Evaluation:
    return await backend.evaluate_action(scene, action_text, world_state)
