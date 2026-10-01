"""Smoke tests. Run with:  pytest -q   (works without a Gemini key; uses the offline planner)"""
import os, tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["GOOGLE_API_KEY"] = ""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.utils import split_plan

ADMIN = ("admin", "admin123")


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


FORM = {"username": "Asha", "user_id": "7", "age": "22", "weight": "60", "height": "165",
        "goal": "lose belly fat", "intensity": "high", "experience": "beginner",
        "equipment": "home", "notes": ""}


def test_home_and_health(client):
    assert client.get("/").status_code == 200
    assert client.get("/health").json()["status"] == "ok"


def test_full_flow(client):
    r = client.post("/generate-workout", data=FORM)          # follows redirect to /result/7
    assert r.status_code == 200 and "Day 1" in r.text and "Nutrition tip" in r.text
    r = client.post("/submit-feedback", data={"user_id": "7", "feedback": "more cardio and yoga"})
    assert r.status_code == 200 and "updated based on your feedback" in r.text
    assert "Original plan" in r.text


def test_validation_error(client):
    r = client.post("/generate-workout", data={**FORM, "age": "3"})
    assert r.status_code == 422 and "Age" in r.text


def test_feedback_unknown_user(client):
    r = client.post("/submit-feedback", data={"user_id": "999", "feedback": "more cardio"})
    assert r.status_code == 404


def test_admin_requires_login(client):
    assert client.get("/view-all-users").status_code == 401
    r = client.get("/view-all-users", auth=ADMIN)
    assert r.status_code == 200 and "Asha" in r.text


def test_json_api(client):
    r = client.post("/generate-plan", json={"user_id": 8, "username": "Ravi", "age": 30, "weight": 80,
                                            "goal": "muscle gain", "intensity": "medium"})
    assert r.status_code == 200 and "workout_plan" in r.json()
    assert client.get("/nutrition-tip", params={"goal": "muscle gain"}).status_code == 200
    r = client.post("/update-plan/8", json={"feedback": "add more rest days"})
    assert "updated_plan" in r.json()


def test_delete(client):
    assert client.post("/admin/delete/8", auth=ADMIN).status_code == 200
    assert client.get("/result/8").status_code == 404


def test_parser_handles_gemini_style_markdown():
    text = "## Plan\n\n**Day 1: Upper Body**\n* **Warm-up:** x\n\n**Day 2: Rest or Active Recovery**\n* walk\n\n**Important Notes:**\n* drink water"
    p = split_plan(text)
    assert p["ok"] and len(p["days"]) == 2 and p["days"][1]["is_rest"] and "drink water" in p["notes"]
