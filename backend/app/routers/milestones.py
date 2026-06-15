from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.progress import build_burndown, milestone_progress
from app.models import Milestone, User
from app.schemas import (
    BurndownResponse,
    MilestoneCreate,
    MilestoneOut,
    MilestoneUpdate,
)

router = APIRouter(prefix="/api/milestones", tags=["milestones"])


def _get_owned(milestone_id: int, db: Session, user: User) -> Milestone:
    m = (
        db.query(Milestone)
        .filter(Milestone.id == milestone_id, Milestone.owner_id == user.id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Milestone not found")
    return m


def _serialize(m: Milestone) -> MilestoneOut:
    out = MilestoneOut.model_validate(m)
    out.progress = milestone_progress(m)
    return out


@router.get("", response_model=list[MilestoneOut])
def list_milestones(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    milestones = (
        db.query(Milestone)
        .filter(Milestone.owner_id == user.id)
        .order_by(Milestone.id)
        .all()
    )
    return [_serialize(m) for m in milestones]


@router.post("", response_model=MilestoneOut, status_code=201)
def create_milestone(
    payload: MilestoneCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    m = Milestone(**payload.model_dump(), owner_id=user.id)
    db.add(m)
    db.commit()
    db.refresh(m)
    return _serialize(m)


@router.get("/{milestone_id}", response_model=MilestoneOut)
def get_milestone(
    milestone_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _serialize(_get_owned(milestone_id, db, user))


@router.patch("/{milestone_id}", response_model=MilestoneOut)
def update_milestone(
    milestone_id: int,
    payload: MilestoneUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    m = _get_owned(milestone_id, db, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(m, field, value)
    db.commit()
    db.refresh(m)
    return _serialize(m)


@router.delete("/{milestone_id}", status_code=204)
def delete_milestone(
    milestone_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    m = _get_owned(milestone_id, db, user)
    db.delete(m)
    db.commit()


@router.get("/{milestone_id}/burndown", response_model=BurndownResponse)
def milestone_burndown(
    milestone_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return build_burndown(_get_owned(milestone_id, db, user))
