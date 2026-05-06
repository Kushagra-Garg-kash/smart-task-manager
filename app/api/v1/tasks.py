from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.task import TaskStatus, TaskPriority
from app.models.user import User
from app.schemas.task import (
    TaskCreate, TaskUpdate, TaskStatusUpdate, TaskFilters,
    TaskDetailResponse, PaginatedTaskResponse,
)
from app.services import task as task_service

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["Tasks"])


@router.get(
    "/",
    response_model=PaginatedTaskResponse,
    summary="List tasks in a project with filters and pagination",
)
def list_tasks(
    project_id: int,
    status: Optional[TaskStatus] = Query(None),
    priority: Optional[TaskPriority] = Query(None),
    assigned_to: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = TaskFilters(status=status, priority=priority, assigned_to=assigned_to)
    return task_service.list_tasks(db, project_id, current_user, filters, page, size)


@router.post(
    "/",
    response_model=TaskDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task in a project",
)
def create_task(
    project_id: int,
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return task_service.create_task(db, project_id, task_in, current_user)


@router.get(
    "/{task_id}",
    response_model=TaskDetailResponse,
    summary="Get a single task",
)
def get_task(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return task_service.get_task(db, project_id, task_id, current_user)


@router.patch(
    "/{task_id}",
    response_model=TaskDetailResponse,
    summary="Update task details",
)
def update_task(
    project_id: int,
    task_id: int,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return task_service.update_task(db, project_id, task_id, task_in, current_user)


@router.patch(
    "/{task_id}/status",
    response_model=TaskDetailResponse,
    summary="Update task status only",
)
def update_task_status(
    project_id: int,
    task_id: int,
    status_in: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return task_service.update_task_status(db, project_id, task_id, status_in, current_user)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a task (owner/editor/admin only)",
)
def delete_task(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task_service.delete_task(db, project_id, task_id, current_user)
