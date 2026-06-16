# BuildTrack — Home Build Manager

Track the final stretch of a home build: organize work into **milestones** (e.g. *Electrical rough-in*), break each into **tasks** with tags, completion %, and a done checkbox, watch milestone progress roll up automatically, and read a **burndown chart** that projects the likely finish date from your actual pace.

## Stack

- **Backend** — FastAPI + SQLAlchemy, JWT auth
- **Database** — PostgreSQL 16
- **Frontend** — React + Vite, served by nginx, charts via Recharts
- **Deploy** — Docker Compose

## Run it

```bash
# from the project root
docker compose up --build
```

Then open:

- Frontend → http://localhost:3000
- API docs (Swagger) → http://localhost:8000/docs

Create an account on the login screen and start adding milestones.

> Set a strong `SECRET_KEY` before deploying for real:
> `SECRET_KEY=$(openssl rand -hex 32) docker compose up --build`

## How it works

### Milestone progress
A milestone's percentage is the **average completion across its tasks**. A task checked *completed* counts as 100%; otherwise its slider value (0–100) is used.

### Burndown & projection
The chart shows two lines of *tasks remaining* over time:

- **Ideal** — a straight line from the total task count at the start date down to zero at the expected end date.
- **Actual** — the real count of incomplete tasks, dropping each time a task is completed (using its completion date).

The **projected finish date** is estimated from your observed velocity (tasks completed per day since the start) extrapolated to the remaining tasks. If the projection lands on or before the target date, the milestone is flagged **On track**, otherwise **Behind**.

## Local development (without Docker)

Backend:
```bash
cd backend
pip install -r requirements.txt
# point at a local Postgres, or run one via docker:
#   docker run -e POSTGRES_USER=buildtrack -e POSTGRES_PASSWORD=buildtrack \
#     -e POSTGRES_DB=buildtrack -p 5432:5432 postgres:16-alpine
export DATABASE_URL=postgresql://buildtrack:buildtrack@localhost:5432/buildtrack
uvicorn app.main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev   # proxies /api to http://localhost:8000
```

## API overview

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/register` | Create account, returns JWT |
| POST | `/api/auth/login` | Log in (form: username=email), returns JWT |
| GET | `/api/auth/me` | Current user |
| GET/POST | `/api/milestones` | List / create milestones (with rolled-up progress) |
| GET/PATCH/DELETE | `/api/milestones/{id}` | Read / update / delete a milestone |
| GET | `/api/milestones/{id}/burndown` | Burndown points + projection |
| POST | `/api/milestones/{id}/tasks` | Add a task |
| PATCH/DELETE | `/api/tasks/{id}` | Update / delete a task |
| GET/POST | `/api/tags` | List / create tags |
| POST | `/api/import/csv` | Bulk-create milestones + tasks from a CSV upload |

All endpoints except register/login require `Authorization: Bearer <token>`.

## Importing a project from CSV

Bulk-create milestones and tasks from a CSV file using the **Import CSV** button
on the Dashboard (you must be logged in), or via `POST /api/import/csv`. See
[docs/csv-import.md](docs/csv-import.md) for the file format and step-by-step
instructions. A sample file is at `data/Gerenciamento_execução_de_obra.csv`.

## Notes

- Tables are auto-created on backend startup. For production schema changes, wire in Alembic (already in requirements).
- CORS is open (`*`) for convenience; tighten `allow_origins` in `app/main.py` before exposing publicly.

## License

Released under the [MIT License](LICENSE).
