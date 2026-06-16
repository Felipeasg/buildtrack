# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

BuildTrack is a home-build progress tracker. Work is organized into **milestones** → **tasks** (with tags, a 0–100 completion slider, and a done flag). Milestone progress rolls up from its tasks, and a burndown chart projects a likely finish date from observed velocity.

Stack: FastAPI + SQLAlchemy 2.0 + PostgreSQL 16 (backend), React 18 + Vite + Recharts (frontend), JWT auth, deployed via Docker Compose.

## Commands

Full stack (from repo root):
```bash
docker compose up --build          # frontend :3000, backend :8000 (/docs for Swagger)
SECRET_KEY=$(openssl rand -hex 32) docker compose up --build   # with a real secret
```

Backend (from `backend/`):
```bash
pip install -r requirements.txt
export DATABASE_URL=postgresql://buildtrack:buildtrack@localhost:5432/buildtrack
uvicorn app.main:app --reload      # serves on :8000
```

Frontend (from `frontend/`):
```bash
npm install
npm run dev        # Vite dev server on :5173, proxies /api → http://localhost:8000
npm run build      # production build to dist/
```

Backend tests live in `backend/tests/` (pytest, isolated in-memory SQLite via a `get_db` dependency override — they never touch Postgres). Run them through Compose:
```bash
docker compose run --rm --no-deps backend sh -c "pip install -q -r requirements-dev.txt && python -m pytest tests/ -q"
```
There is **no frontend test suite, linter, or formatter configured** in this repo. Alembic is in `requirements.txt` but **not wired up** — tables are created via `Base.metadata.create_all` at startup (`app/main.py`), so model changes only take effect on a fresh DB. There are no migrations; altering a column requires dropping/recreating the table or adding Alembic.

## Architecture

### Backend layout (`backend/app/`)
- `main.py` — app assembly: creates tables, opens CORS to `*`, mounts the four routers, exposes `/api/health`.
- `core/config.py` — `Settings` (pydantic-settings) read from env / `.env`. All config flows through the singleton `settings`.
- `core/database.py` — `engine`, `SessionLocal`, `Base`, and the `get_db` dependency.
- `core/security.py` — bcrypt hashing + JWT encode/decode. The JWT `sub` is the user's **email** (not id).
- `core/deps.py` — `get_current_user` resolves the bearer token's email to a `User`; this is the auth gate on every protected route.
- `core/progress.py` — pure functions `milestone_progress()` and `build_burndown()` (the only non-CRUD business logic; see below).
- `models/__init__.py` — all SQLAlchemy models in one file (`User`, `Milestone`, `Tag`, `Task`, `task_tags` join table).
- `schemas/__init__.py` — all Pydantic request/response models in one file.
- `routers/` — `auth`, `milestones`, `tasks`, `tags`. Note `tasks.py` uses prefix `/api` (its routes are `/milestones/{id}/tasks` and `/tasks/{id}`), while the others prefix their resource.

### Ownership / authorization model
Data is scoped per-user through `Milestone.owner_id`. There is **no row-level framework** — every router re-checks ownership manually via helpers like `_get_owned` (milestones.py) and `_owned_milestone` / `_owned_task` (tasks.py), which filter on `Milestone.owner_id == user.id` and raise 404 if not found. When adding endpoints that touch milestones or tasks, you **must** route through these helpers or replicate the ownership filter, or you'll leak other users' data.

**Tags are global and shared across all users** (`tags.py` has no owner scoping) — creating a tag with an existing name returns the existing one. Keep this in mind: tags are not per-user.

### Task completion invariant
`tasks.py::_sync_completion` is the single source of truth keeping `is_completed`, `completion` (0–100), and `completed_at` consistent, and it runs on every create/update:
- `is_completed=True` → forces `completion=100` and stamps `completed_at=today` (if unset).
- `is_completed=False` → clears `completed_at`, and caps `completion` at 99 so a task can't read as "done" without the flag.

Always go through this helper rather than setting those three fields directly.

### Progress & burndown (`core/progress.py`)
- `milestone_progress` = average task completion (a completed task counts as 100). Exposed as `MilestoneOut.progress`, computed in the router's `_serialize` after `model_validate` (it is not a DB column).
- `build_burndown` produces day-by-day **ideal** vs **actual** remaining-task lines plus a `projected_end_date` extrapolated from velocity (`completed_count / elapsed_days`). `on_track` = projection ≤ `expected_end_date`. The actual line stops at today (future days fall back to the ideal value). All dates here are plain `date`, not datetime.

### Frontend (`frontend/src/`)
- `api/index.js` — single axios instance (`baseURL: /api`). A request interceptor attaches the bearer token from `localStorage`; a response interceptor redirects to `/login` on any 401. All API calls live here — add new endpoints to this file.
- `context/AuthContext.jsx` — holds the current user; `App.jsx` gates routes via `<Protected>` / `<PublicOnly>`.
- Pages: `Login`, `Dashboard` (milestone list), `MilestoneDetail` (tasks + burndown). Components: `Burndown`, `MilestoneForm`, `TaskForm`, `Modal`.
- Login posts form-encoded `username`/`password` (OAuth2 convention) — the backend treats `username` as the email.

### Request flow
React → axios `/api/*` → (dev: Vite proxy / prod: nginx `proxy_pass` to `backend:8000`) → FastAPI router → `get_current_user` → SQLAlchemy session → PostgreSQL.

## Conventions
- Models and schemas each live in a single `__init__.py` — add new ones there, don't split into per-entity files unless refactoring deliberately.
- Updates use `model_dump(exclude_unset=True)` for partial PATCH semantics; respect that pattern.
- The backend runs as the `app` package (`uvicorn app.main:app`) — imports are absolute from `app.` (e.g. `from app.core.database import ...`).

## Working Guidelines

Behavioral guidelines to reduce common coding mistakes. These bias toward caution over speed — for trivial tasks, use judgment.

### 1. Think before coding
Don't assume, don't hide confusion, surface tradeoffs.
- State assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop, name what's confusing, and ask.

### 2. Simplicity first
Minimum code that solves the problem. Nothing speculative.
- No features beyond what was asked; no abstractions for single-use code.
- No "flexibility"/"configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it. Ask: "Would a senior engineer say this is overcomplicated?"

### 3. Surgical changes
Touch only what you must. Clean up only your own mess.
- Don't "improve" adjacent code, comments, or formatting; don't refactor what isn't broken.
- Match existing style, even if you'd do it differently.
- Remove imports/variables/functions that YOUR changes made unused; leave pre-existing dead code alone (mention it, don't delete it) unless asked.
- The test: every changed line should trace directly to the user's request.

### 4. Goal-driven execution
Define success criteria, then loop until verified.
- "Add validation" → write tests for invalid inputs, then make them pass.
- "Fix the bug" → write a test that reproduces it, then make it pass.
- "Refactor X" → ensure tests pass before and after.
- For multi-step tasks, state a brief plan with a verification check for each step.
