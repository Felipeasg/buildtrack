from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.csv_import import parse_build_csv
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Milestone, Tag, Task, User
from app.routers.tasks import _sync_completion  # the task-completion invariant
from app.schemas import ImportResult

router = APIRouter(prefix="/api/import", tags=["import"])


def _get_or_create_tag(name: str, db: Session) -> Tag:
    # Tags are global and shared across users (see tags router).
    tag = db.query(Tag).filter(Tag.name == name).first()
    if tag is None:
        tag = Tag(name=name)
        db.add(tag)
        db.flush()
    return tag


@router.post("/csv", response_model=ImportResult, status_code=201)
async def import_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    raw = await file.read()
    try:
        parsed = parse_build_csv(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    tasks_created = 0
    for pm in parsed:
        milestone = Milestone(
            name=pm.name,
            start_date=pm.start_date,
            expected_end_date=pm.expected_end_date,
            owner_id=user.id,
        )
        db.add(milestone)
        db.flush()  # assign milestone.id for the tasks below
        for pt in pm.tasks:
            task = Task(
                title=pt.title,
                description=pt.description,
                completion=pt.completion,
                is_completed=pt.is_completed,
                start_date=pt.start_date,
                expected_end_date=pt.expected_end_date,
                milestone_id=milestone.id,
            )
            task.tags = [_get_or_create_tag(name, db) for name in pt.tags]
            _sync_completion(task)
            db.add(task)
            tasks_created += 1

    db.commit()
    return ImportResult(
        milestones_created=len(parsed), tasks_created=tasks_created
    )
