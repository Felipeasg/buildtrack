from datetime import date
from pydantic import BaseModel, EmailStr, ConfigDict, Field


# ---------- Auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = ""


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ImportResult(BaseModel):
    milestones_created: int
    tasks_created: int


# ---------- Tags ----------
class TagBase(BaseModel):
    name: str
    color: str = "#6366f1"


class TagCreate(TagBase):
    pass


class TagOut(TagBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- Tasks ----------
class TaskBase(BaseModel):
    title: str
    description: str = ""
    completion: int = Field(default=0, ge=0, le=100)
    is_completed: bool = False
    start_date: date | None = None
    expected_end_date: date | None = None


class TaskCreate(TaskBase):
    tag_ids: list[int] = []


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    completion: int | None = Field(default=None, ge=0, le=100)
    is_completed: bool | None = None
    start_date: date | None = None
    expected_end_date: date | None = None
    tag_ids: list[int] | None = None


class TaskOut(TaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    milestone_id: int
    completed_at: date | None = None
    tags: list[TagOut] = []


# ---------- Milestones ----------
class MilestoneBase(BaseModel):
    name: str
    description: str = ""
    start_date: date | None = None
    expected_end_date: date | None = None


class MilestoneCreate(MilestoneBase):
    pass


class MilestoneUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    start_date: date | None = None
    expected_end_date: date | None = None


class MilestoneOut(MilestoneBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tasks: list[TaskOut] = []
    progress: float = 0.0  # computed % completion


class BurndownPoint(BaseModel):
    date: date
    ideal_remaining: float
    actual_remaining: float


class BurndownResponse(BaseModel):
    milestone_id: int
    total_tasks: int
    points: list[BurndownPoint]
    projected_end_date: date | None = None
    expected_end_date: date | None = None
    on_track: bool | None = None
