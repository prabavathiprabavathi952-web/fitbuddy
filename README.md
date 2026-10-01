# FitBuddy - AI Fitness Plan Generator (FastAPI + Gemini)

Personalised 7-day workout plans (Gemini Pro), nutrition tips (Gemini Flash), feedback-based plan updates,
SQLite storage and a coach dashboard. If Gemini is unavailable the built-in planner keeps the app working.

## Run locally (VS Code)
```bash
python -m venv venv
venv\Scripts\activate          # Windows   |   source venv/bin/activate  (Mac/Linux)
pip install -r requirements.txt
copy .env.example .env         # Mac/Linux: cp .env.example .env   -> then add GOOGLE_API_KEY
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000 (API docs at /docs). Coach dashboard: /view-all-users (login from `.env`).

## Test
```bash
pytest -q
```

## Deploy on Render
1. Push this folder to a GitHub repo (`.env` and `fitbuddy.db` are git-ignored).
2. Render dashboard -> New -> Blueprint (uses `render.yaml`), or New -> Web Service with:
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Add env var `GOOGLE_API_KEY`, and set `ADMIN_PASSWORD`.
4. Free-tier disk is wiped on every redeploy/restart, so SQLite data is lost. For permanent data, create a free
   Render PostgreSQL database and set `DATABASE_URL` to its Internal Database URL. No code change needed.
