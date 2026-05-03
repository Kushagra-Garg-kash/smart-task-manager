from datetime import datetime
from pydantic import BaseModel
from app.models.project import ProjectMemberRole
from app.schemas.user import UserPublic


# ─── Project ──────────────────────────────────────────────────────────────────

class ProjectBase(BaseModel):
    name: str
    description: str | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectDetailResponse(ProjectResponse):
    """Full project with members list."""
    members: list["ProjectMemberResponse"] = []

    model_config = {"from_attributes": True}


# ─── Project Members ──────────────────────────────────────────────────────────

class ProjectMemberAdd(BaseModel):
    user_id: int
    role: ProjectMemberRole = ProjectMemberRole.viewer


class ProjectMemberUpdate(BaseModel):
    role: ProjectMemberRole


class ProjectMemberResponse(BaseModel):
    id: int
    user_id: int
    project_id: int
    role: ProjectMemberRole
    joined_at: datetime
    user: UserPublic

    model_config = {"from_attributes": True}


ProjectDetailResponse.model_rebuild()
