from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine
from app.routers import auth, imports, milestones, tags, tasks

# Create tables on startup (simple approach; use Alembic for real migrations)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="BuildTrack API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(milestones.router)
app.include_router(tasks.router)
app.include_router(tags.router)
app.include_router(imports.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
