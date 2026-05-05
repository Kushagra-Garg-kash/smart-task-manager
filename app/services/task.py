from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.crud import task as task_crud
from app.crud import project as project_crud
from app.crud import user as user_crud
from app.models.task import Task
from app.models.user import User, UserRole
from app.models.project import ProjectMemberRole
from app.schemas.task import (
    TaskCreate, TaskUpdate, TaskStatusUpdate, TaskFilters,
    TaskDetailResponse, PaginatedTaskResponse,
)


def _require_task(db: Session, task_id: int, project_id: int) -> Task:
    task = task_crud.get_task(db, task_id)
    if not task or task.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


def _require_project_membership(db: Session, project_id: int, user_id: int) -> None:
    project = project_crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    member = project_crud.get_member(db, project_id, user_id)
    if not member and project.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a project member")


def _can_edit_task(current_user: User, task: Task, project_id: int, db: Session) -> bool:
    """Admins can edit any task; members can only edit tasks assigned to them."""
    if current_user.role == UserRole.admin:
        return True
    member = project_crud.get_member(db, project_id, current_user.id)
    if member and member.role in (ProjectMemberRole.owner, ProjectMemberRole.editor):
        return True
    # Plain members can only touch their own tasks
    return task.assigned_to == current_user.id


# ─── Task Operations ──────────────────────────────────────────────────────────

def list_tasks(
    db: Session, project_id: int, current_user: User, filters: TaskFilters, page: int, size: int
) -> PaginatedTaskResponse:
    _require_project_membership(db, project_id, current_user.id)
    skip = (page - 1) * size
    tasks, total = task_crud.get_tasks_for_project(db, project_id, filters, skip, size)
    pages = (total + size - 1) // size if total > 0 else 1
    return PaginatedTaskResponse(
        items=[TaskDetailResponse.model_validate(t) for t in tasks],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


def get_task(db: Session, project_id: int, task_id: int, current_user: User) -> TaskDetailResponse:
    _require_project_membership(db, project_id, current_user.id)
    task = _require_task(db, task_id, project_id)
    return TaskDetailResponse.model_validate(task)


def create_task(
    db: Session, project_id: int, task_in: TaskCreate, current_user: User
) -> TaskDetailResponse:
    _require_project_membership(db, project_id, current_user.id)

    # Validate assignee is a project member
    if task_in.assigned_to:
        if not user_crud.get_user(db, task_in.assigned_to):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee user not found")
        if not project_crud.get_member(db, project_id, task_in.assigned_to):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee must be a member of this project",
            )

    task = task_crud.create_task(db, task_in, project_id)
    return TaskDetailResponse.model_validate(task)


def update_task(
    db: Session, project_id: int, task_id: int, task_in: TaskUpdate, current_user: User
) -> TaskDetailResponse:
    _require_project_membership(db, project_id, current_user.id)
    task = _require_task(db, task_id, project_id)

    if not _can_edit_task(current_user, task, project_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit this task",
        )

    # Validate new assignee if provided
    if task_in.assigned_to:
        if not user_crud.get_user(db, task_in.assigned_to):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee user not found")
        if not project_crud.get_member(db, project_id, task_in.assigned_to):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee must be a member of this project",
            )

    updated = task_crud.update_task(db, task, task_in)
    return TaskDetailResponse.model_validate(updated)


def update_task_status(
    db: Session, project_id: int, task_id: int, status_in: TaskStatusUpdate, current_user: User
) -> TaskDetailResponse:
    _require_project_membership(db, project_id, current_user.id)
    task = _require_task(db, task_id, project_id)

    if not _can_edit_task(current_user, task, project_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this task",
        )

    updated = task_crud.update_task_status(db, task, status_in.status)
    return TaskDetailResponse.model_validate(updated)


def delete_task(
    db: Session, project_id: int, task_id: int, current_user: User
) -> None:
    _require_project_membership(db, project_id, current_user.id)
    task = _require_task(db, task_id, project_id)

    # Only owner/editor/admin can delete tasks
    member = project_crud.get_member(db, project_id, current_user.id)
    is_privileged = (
        current_user.role == UserRole.admin
        or (member and member.role in (ProjectMemberRole.owner, ProjectMemberRole.editor))
    )
    if not is_privileged:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only editors, owners, or admins can delete tasks",
        )

    task_crud.soft_delete_task(db, task)
