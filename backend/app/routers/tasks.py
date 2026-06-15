from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Milestone, Tag, Task, User
from app.schemas import TaskCreate, TaskOut, TaskUpdate

router = APIRouter(prefix="/api", tags=["tasks"])


def _owned_milestone(milestone_id: int, db: Session, user: User) -> Milestone:
    m = (
        db.query(Milestone)
        .filter(Milestone.id == milestone_id, Milestone.owner_id == user.id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Milestone not found")
    return m


def _owned_task(task_id: int, db: Session, user: User) -> Task:
    task = (
        db.query(Task)
        .join(Milestone)
        .filter(Task.id == task_id, Milestone.owner_id == user.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def _apply_tags(task: Task, tag_ids: list[int], db: Session):
    task.tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all() if tag_ids else []


def _sync_completion(task: Task):
    """Keep is_completed, completion and completed_at consistent."""
    if task.is_completed:
        task.completion = 100
        if task.completed_at is None:
            task.completed_at = date.today()
    else:
        task.completed_at = None
        if task.completion >= 100:
            task.completion = 99  # cap so it isn't "completed" without the flag


@router.post(
    "/milestones/{milestone_id}/tasks", response_model=TaskOut, status_code=201
)
def create_task(
    milestone_id: int,
    payload: TaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _owned_milestone(milestone_id, db, user)
    data = payload.model_dump(exclude={"tag_ids"})
    task = Task(**data, milestone_id=milestone_id)
    _apply_tags(task, payload.tag_ids, db)
    _sync_completion(task)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = _owned_task(task_id, db, user)
    data = payload.model_dump(exclude_unset=True)
    tag_ids = data.pop("tag_ids", None)
    for field, value in data.items():
        setattr(task, field, value)
    if tag_ids is not None:
        _apply_tags(task, tag_ids, db)
    _sync_completion(task)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = _owned_task(task_id, db, user)
    db.delete(task)
    db.commit()
