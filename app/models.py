"""Pydantic models for AI structured outputs.

Note: state changes are NO LONGER part of the Evaluation. They are declared
on each `Transition` in the episode SQLite and applied deterministically by
the engine when the chosen transition fires. The AI only picks the
transition_index; the engine handles state.
"""

from typing import Literal

from pydantic import BaseModel, Field


class GeneratedChoice(BaseModel):
    text: str
    quality: Literal["correct", "flawed", "mistake"]


class ChoicesResponse(BaseModel):
    choices: list[GeneratedChoice] = Field(min_length=3, max_length=3)


class Evaluation(BaseModel):
    """The AI's response to a player action.

    `transition_index` is the 0-based index into the current scene's
    transitions list. For terminal scenes (no transitions) it should be 0
    and is ignored by the engine.
    """

    verdict: Literal["good", "partial", "poor"]
    explanation: str
    coaching: str
    transition_index: int = Field(ge=0, default=0)
