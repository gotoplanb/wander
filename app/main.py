from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import ai
from app.scenes import SCENES

BASE_DIR = Path(__file__).parent

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


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    scene = SCENES["opening"]
    try:
        choices = await ai.generate_choices(scene)
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
    scene = SCENES.get(scene_id)
    if scene is None:
        raise HTTPException(status_code=404)

    try:
        evaluation = await ai.evaluate_action(scene, action_text)
    except Exception as exc:
        return _render_error(request, exc)

    if scene.next_scene_id is None:
        next_scene = scene  # terminal: stay put
        next_choices: list[ai.GeneratedChoice] = []
    else:
        next_scene = SCENES[scene.next_scene_id]
        try:
            next_choices = await ai.generate_choices(next_scene)
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
