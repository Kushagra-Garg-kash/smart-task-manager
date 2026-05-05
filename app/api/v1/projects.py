from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.project import (
    ProjectCreate, ProjectUpdate,
    ProjectResponse, ProjectDetailResponse,
    ProjectMemberAdd, ProjectMemberUpdate, ProjectMemberResponse,
)
from app.services import project as project_service

router = APIRouter(prefix="/projects", tags=["Projects"])


# ─── Project CRUD ─────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=list[ProjectResponse],
    summary="List all projects you belong to",
)
def list_projects(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return project_service.list_projects(db, current_user, skip, limit)


@router.post(
    "/",
    response_model=ProjectDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return project_service.create_project(db, project_in, current_user)


@router.get(
    "/{project_id}",
    response_model=ProjectDetailResponse,
    summary="Get a project with members",
)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return project_service.get_project_detail(db, project_id, current_user)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update a project (owner/admin only)",
)
def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return project_service.update_project(db, project_id, project_in, current_user)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a project (owner/admin only)",
)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project_service.delete_project(db, project_id, current_user)


# ─── Project Members ──────────────────────────────────────────────────────────

@router.post(
    "/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a member to a project (owner/admin only)",
)
def add_member(
    project_id: int,
    member_in: ProjectMemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return project_service.add_member(db, project_id, member_in, current_user)


@router.patch(
    "/{project_id}/members/{user_id}",
    response_model=ProjectMemberResponse,
    summary="Update a member's role (owner/admin only)",
)
def update_member(
    project_id: int,
    user_id: int,
    role_in: ProjectMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return project_service.update_member(db, project_id, user_id, role_in, current_user)


@router.delete(
    "/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member from a project (owner/admin only)",
)
def remove_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project_service.remove_member(db, project_id, user_id, current_user)
