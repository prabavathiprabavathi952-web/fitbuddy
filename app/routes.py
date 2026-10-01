"""All FitBuddy routes: HTML pages, JSON API and admin dashboard."""
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app import config, database as db
from app.gemini_client import is_configured
from app.gemini_flash_generator import generate_nutrition_tip
from app.gemini_generator import generate_workout
from app.nutrition import bmi_category, calculate_bmi, water_target_litres
from app.schemas import FeedbackRequest, UserInput, WorkoutRequest
from app.updated_plan import update_workout
from app.utils import render_markdown, source_label, split_plan

router = APIRouter()
templates = Jinja2Templates(directory=str(config.APP_DIR / "templates"))
templates.env.filters["md"] = render_markdown
templates.env.filters["source"] = source_label
security = HTTPBasic()


# --------------------------------------------------------------------------- helpers
def _clean(v: Optional[str]) -> Optional[str]:
    v = (v or "").strip()
    return v or None


def _friendly_errors(exc: ValidationError) -> list[str]:
    names = {"username": "Name", "user_id": "User ID", "age": "Age", "weight": "Weight",
             "height": "Height", "goal": "Goal", "intensity": "Intensity", "feedback": "Feedback"}
    out = []
    for e in exc.errors():
        field = str(e["loc"][-1]) if e["loc"] else "Input"
        out.append(f"{names.get(field, field)}: {e['msg']}")
    return out


def _home(request: Request, errors=None, form=None, status=200):
    return templates.TemplateResponse(request, "index.html", {
        "errors": errors or [], "form": form or {}, "next_id": db.next_user_id(),
        "ai_ready": is_configured(),
    }, status_code=status)


def _create_plan(data: UserInput) -> dict:
    """Save user, generate plan + tip, store them. Shared by the page and JSON API."""
    uid = data.user_id or db.next_user_id()
    db.save_user(uid, data.username, data.age, data.weight, data.goal, data.intensity,
                 height=data.height, experience=data.experience,
                 equipment=data.equipment, notes=data.notes)
    plan, source = generate_workout({
        "goal": data.goal, "intensity": data.intensity, "experience": data.experience,
        "equipment": data.equipment, "age": data.age, "weight": data.weight,
        "height": data.height, "notes": data.notes, "name": data.username,
    })
    tip, _ = generate_nutrition_tip(data.goal)
    db.save_plan(uid, plan, tip, source)
    return {"user_id": uid, "plan": plan, "tip": tip, "source": source}


def _result_context(user_id: int) -> Optional[dict]:
    user, plan = db.get_user(user_id), db.get_plan(user_id)
    if not user or not plan:
        return None
    bmi = calculate_bmi(user.weight, user.height)
    return {
        "user": user, "plan": plan,
        "username": user.name, "user_id": user.id, "age": user.age, "weight": user.weight,
        "goal": user.goal, "intensity": user.intensity,
        "workout_plan": plan.updated_plan or plan.original_plan,
        "nutrition_tip": plan.nutrition_tip,
        "original": split_plan(plan.original_plan),
        "current": split_plan(plan.updated_plan) if plan.updated_plan else None,
        "has_update": bool(plan.updated_plan),
        "bmi": bmi, "bmi_label": bmi_category(bmi),
        "water": water_target_litres(user.weight),
        "history": db.get_feedback_history(user_id),
    }


def require_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    ok_user = secrets.compare_digest(credentials.username.encode(), config.ADMIN_USERNAME.encode())
    ok_pass = secrets.compare_digest(credentials.password.encode(), config.ADMIN_PASSWORD.encode())
    if not (ok_user and ok_pass):
        raise HTTPException(401, "Incorrect admin credentials",
                            headers={"WWW-Authenticate": "Basic"})
    return credentials.username


# --------------------------------------------------------------------------- pages
@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return _home(request)


@router.post("/generate-workout", response_class=HTMLResponse)
def generate_workout_page(
    request: Request,
    username: str = Form(""), user_id: str = Form(""), age: str = Form(""),
    weight: str = Form(""), height: str = Form(""), goal: str = Form(""),
    intensity: str = Form("medium"), experience: str = Form("beginner"),
    equipment: str = Form("gym"), notes: str = Form(""),
):
    form = {"username": username, "user_id": user_id, "age": age, "weight": weight,
            "height": height, "goal": goal, "intensity": intensity,
            "experience": experience, "equipment": equipment, "notes": notes}
    try:
        data = UserInput(**{k: (_clean(v) if k in ("user_id", "height", "notes") else v)
                            for k, v in form.items()})
    except ValidationError as exc:
        return _home(request, _friendly_errors(exc), form, status=422)
    result = _create_plan(data)
    return RedirectResponse(f"/result/{result['user_id']}?created=1", status_code=303)


@router.get("/result/{user_id}", response_class=HTMLResponse)
def result_page(request: Request, user_id: int, created: int = 0, updated: int = 0):
    ctx = _result_context(user_id)
    if ctx is None:
        return _home(request, [f"No plan found for User ID {user_id}. Create one below."], status=404)
    ctx.update({"created": bool(created), "updated": bool(updated)})
    return templates.TemplateResponse(request, "result.html", ctx)


@router.get("/lookup")
def lookup(user_id: int):
    return RedirectResponse(f"/result/{user_id}", status_code=303)


@router.get("/feedback", response_class=HTMLResponse)
def feedback_page(request: Request, user_id: Optional[int] = None):
    return templates.TemplateResponse(request, "feedback.html",
                                      {"user_id": user_id or "", "errors": []})


@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback(request: Request, user_id: str = Form(""), feedback: str = Form("")):
    def fail(msgs, status=422):
        return templates.TemplateResponse(request, "feedback.html",
                                          {"user_id": user_id, "errors": msgs}, status_code=status)
    try:
        uid = int(user_id)
    except ValueError:
        return fail(["User ID must be a number."])
    try:
        fb = FeedbackRequest(feedback=feedback)
    except ValidationError as exc:
        return fail(_friendly_errors(exc))
    user, base = db.get_user(uid), db.get_current_plan(uid)
    if not user or not base:
        return fail([f"No plan found for User ID {uid}. Generate a plan first."], 404)
    revised, source = update_workout(
        base, fb.feedback, {"goal": user.goal, "intensity": user.intensity,
                            "experience": user.experience})
    db.update_plan(uid, revised, fb.feedback, source)
    return RedirectResponse(f"/result/{uid}?updated=1", status_code=303)


@router.get("/download/{user_id}", response_class=PlainTextResponse)
def download_plan(user_id: int, version: str = "current"):
    plan = db.get_plan(user_id)
    if not plan:
        raise HTTPException(404, "Plan not found")
    text = plan.original_plan if version == "original" else (plan.updated_plan or plan.original_plan)
    return PlainTextResponse(text, headers={
        "Content-Disposition": f'attachment; filename="fitbuddy-plan-{user_id}.txt"'})


# --------------------------------------------------------------------------- JSON API
@router.get("/health")
def health():
    return {"status": "ok", "ai_configured": is_configured(),
            "pro_model": config.GEMINI_PRO_MODEL, "flash_model": config.GEMINI_FLASH_MODEL}


@router.post("/generate-workout/gemini")
def api_generate_workout(request: WorkoutRequest):
    plan, source = generate_workout(request.model_dump())
    return {"model": source, "workout_plan": plan}


@router.get("/nutrition-tip")
def api_nutrition_tip(goal: str):
    if not 2 <= len(goal.strip()) <= 200:
        raise HTTPException(422, "goal must be 2-200 characters")
    tip, source = generate_nutrition_tip(goal.strip())
    return {"goal": goal, "nutrition_tip": tip, "model": source}


@router.post("/generate-plan")
def api_generate_plan(user_data: UserInput):
    try:
        r = _create_plan(user_data)
    except Exception as exc:
        raise HTTPException(500, f"Something went wrong: {exc}")
    return {"message": "Workout plan generated and saved successfully!", "user_id": r["user_id"],
            "model": r["source"], "workout_plan": r["plan"], "nutrition_tip": r["tip"]}


@router.post("/update-plan/{user_id}")
def api_update_plan(user_id: int, data: FeedbackRequest):
    user, base = db.get_user(user_id), db.get_current_plan(user_id)
    if not user or not base:
        raise HTTPException(404, "Original plan not found for this user.")
    revised, source = update_workout(base, data.feedback, {"goal": user.goal,
                                     "intensity": user.intensity, "experience": user.experience})
    db.update_plan(user_id, revised, data.feedback, source)
    return {"model": source, "updated_plan": revised}


# --------------------------------------------------------------------------- admin
@router.get("/view-all-users", response_class=HTMLResponse)
def view_all_users(request: Request, _: str = Depends(require_admin)):
    rows = db.get_admin_rows()
    return templates.TemplateResponse(request, "all_users.html",
                                      {"users": rows, "stats": db.get_admin_stats(rows)})


@router.post("/admin/delete/{user_id}")
def admin_delete(user_id: int, _: str = Depends(require_admin)):
    db.delete_user(user_id)
    return RedirectResponse("/view-all-users", status_code=303)


@router.get("/api/users")
def api_users(_: str = Depends(require_admin)):
    return db.get_admin_rows()
