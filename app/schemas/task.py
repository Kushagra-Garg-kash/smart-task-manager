from datetime import datetime, date
from pydantic import BaseModel
from app.models.task import TaskStatus, TaskPriority
from app.schemas.user import UserPublic


# ─── Task ─────────────────────────────────────────────────────────────────────

class TaskBase(BaseModel):
    title: str
    description: str | None = None
    priority: TaskPriority = TaskPriority.medium
    due_date: date | None = None


class TaskCreate(TaskBase):
    assigned_to: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: TaskPriority | None = None
    due_date: date | None = None
    assigned_to: int | None = None


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class TaskResponse(TaskBase):
    id: int
    status: TaskStatus
    project_id: int
    assigned_to: int | None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskDetailResponse(TaskResponse):
    """Task with nested assignee info."""
    assignee: UserPublic | None = None

    model_config = {"from_attributes": True}


# ─── Filters & Pagination ─────────────────────────────────────────────────────

class TaskFilters(BaseModel):
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assigned_to: int | None = None


class PaginatedTaskResponse(BaseModel):
    items: list[TaskDetailResponse]
    total: int
    page: int
    size: int
    pages: int
