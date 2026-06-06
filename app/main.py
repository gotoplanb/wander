from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import ai
from app.episodes import load_episode
from app.session import ActionRecord, SessionState

BASE_DIR = Path(__file__).parent
DEFAULT_EPISODE_ID = "forest-demo"

app = FastAPI(title="Wanderer")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def _render_error(request: Request, exc: Exception) -> HTMLResponse:
    context = {
        "error_type": type(exc).__name__,
        "error_message": str(exc),
        "backend": ai.backend.name,
        "backend_description": ai.backend_description(),
    }
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request, "_error.html", context)
    return templates.TemplateResponse(
        request, "base.html", {**context, "content_template": "_error.html"}
    )


def _ensure_session() -> SessionState:
    state = SessionState.load()
    if state.episode_id is None or state.current_scene_id is None:
        episode = load_episode(DEFAULT_EPISODE_ID)
        state = SessionState(
            episode_id=DEFAULT_EPISODE_ID,
            current_scene_id=episode.opening_scene_id,
            world_state=dict(episode.initial_world_state),
            action_history=[],
        )
        state.save()
    return state


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    state = _ensure_session()
    episode = load_episode(state.episode_id)  # type: ignore[arg-type]
    scene = episode.scenes[state.current_scene_id]  # type: ignore[index]
    try:
        choices = await ai.generate_choices(scene, state.world_state)
    except Exception as exc:
        return _render_error(request, exc)
    return templates.TemplateResponse(
        request,
        "base.html",
        {
            "scene": scene,
            "choices": choices,
            "evaluation": None,
            "prior_action": None,
            "content_template": "scene.html",
        },
    )


@app.post("/action/{scene_id}", response_class=HTMLResponse)
async def action(
    request: Request,
    scene_id: str,
    action_text: Annotated[str, Form()],
) -> HTMLResponse:
    state = SessionState.load()
    if state.episode_id is None or state.current_scene_id != scene_id:
        raise HTTPException(status_code=409, detail="Stale scene; reload.")

    episode = load_episode(state.episode_id)
    scene = episode.scenes.get(scene_id)
    if scene is None:
        raise HTTPException(status_code=404)

    try:
        evaluation = await ai.evaluate_action(scene, action_text, state.world_state)
    except Exception as exc:
        return _render_error(request, exc)

    state.action_history.append(
        ActionRecord(
            scene_id=scene.id,
            action=action_text,
            evaluation=evaluation.model_dump(),
        )
    )

    if scene.is_terminal or not scene.transitions:
        state.save()
        return templates.TemplateResponse(
            request,
            "scene.html",
            {
                "scene": scene,
                "choices": [],
                "evaluation": evaluation,
                "prior_action": action_text,
            },
        )

    # Pick transition (bounded by the model's index) and apply its declared
    # state_delta. The engine — not the AI — owns state transitions.
    idx = max(0, min(evaluation.transition_index, len(scene.transitions) - 1))
    transition = scene.transitions[idx]
    state.world_state.update(transition.state_delta)
    next_scene = episode.scenes[transition.next_scene_id]
    state.current_scene_id = next_scene.id
    state.save()

    try:
        next_choices = await ai.generate_choices(next_scene, state.world_state)
    except Exception as exc:
        return _render_error(request, exc)

    return templates.TemplateResponse(
        request,
        "scene.html",
        {
            "scene": next_scene,
            "choices": next_choices,
            "evaluation": evaluation,
            "prior_action": action_text,
        },
    )
