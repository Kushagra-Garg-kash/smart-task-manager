from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.crud import project as project_crud
from app.crud import user as user_crud
from app.models.project import Project, ProjectMember, ProjectMemberRole
from app.models.user import User, UserRole
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectMemberAdd, ProjectMemberUpdate,
    ProjectResponse, ProjectDetailResponse, ProjectMemberResponse,
)


def _require_project(db: Session, project_id: int) -> Project:
    project = project_crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def _require_membership(db: Session, project_id: int, user_id: int) -> ProjectMember:
    member = project_crud.get_member(db, project_id, user_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a project member")
    return member


def _require_owner_or_admin(current_user: User, project: Project) -> None:
    is_owner = project.owner_id == current_user.id
    is_admin = current_user.role == UserRole.admin
    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project owner or an admin can perform this action",
        )


# ─── Project Operations ───────────────────────────────────────────────────────

def list_projects(db: Session, current_user: User, skip: int, limit: int) -> list[ProjectResponse]:
    projects = project_crud.get_projects_for_user(db, current_user.id, skip, limit)
    return [ProjectResponse.model_validate(p) for p in projects]


def get_project_detail(db: Session, project_id: int, current_user: User) -> ProjectDetailResponse:
    project = _require_project(db, project_id)
    _require_membership(db, project_id, current_user.id)
    return ProjectDetailResponse.model_validate(project)


def create_project(db: Session, project_in: ProjectCreate, current_user: User) -> ProjectDetailResponse:
    project = project_crud.create_project(db, project_in, current_user.id)
    return ProjectDetailResponse.model_validate(project)


def update_project(
    db: Session, project_id: int, project_in: ProjectUpdate, current_user: User
) -> ProjectResponse:
    project = _require_project(db, project_id)
    _require_owner_or_admin(current_user, project)
    updated = project_crud.update_project(db, project, project_in)
    return ProjectResponse.model_validate(updated)


def delete_project(db: Session, project_id: int, current_user: User) -> None:
    project = _require_project(db, project_id)
    _require_owner_or_admin(current_user, project)
    project_crud.soft_delete_project(db, project)


# ─── Member Operations ────────────────────────────────────────────────────────

def add_member(
    db: Session, project_id: int, member_in: ProjectMemberAdd, current_user: User
) -> ProjectMemberResponse:
    project = _require_project(db, project_id)
    _require_owner_or_admin(current_user, project)

    # Verify user to be added exists
    if not user_crud.get_user(db, member_in.user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check not already a member
    if project_crud.get_member(db, project_id, member_in.user_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member")

    # Prevent demoting/re-adding an owner via this endpoint
    if member_in.role == ProjectMemberRole.owner:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot assign owner role via this endpoint")

    member = project_crud.add_member(db, project_id, member_in)
    return ProjectMemberResponse.model_validate(member)


def update_member(
    db: Session, project_id: int, user_id: int, role_in: ProjectMemberUpdate, current_user: User
) -> ProjectMemberResponse:
    project = _require_project(db, project_id)
    _require_owner_or_admin(current_user, project)
    member = _require_membership(db, project_id, user_id)

    if member.role == ProjectMemberRole.owner:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change owner's role")

    updated = project_crud.update_member_role(db, member, role_in.role)
    return ProjectMemberResponse.model_validate(updated)


def remove_member(
    db: Session, project_id: int, user_id: int, current_user: User
) -> None:
    project = _require_project(db, project_id)
    _require_owner_or_admin(current_user, project)
    member = _require_membership(db, project_id, user_id)

    if member.role == ProjectMemberRole.owner:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove the project owner")

    project_crud.remove_member(db, member)
