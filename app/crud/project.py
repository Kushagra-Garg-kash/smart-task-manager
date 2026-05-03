from sqlalchemy.orm import Session, joinedload
from app.models.project import Project, ProjectMember, ProjectMemberRole
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectMemberAdd


# ─── Project ──────────────────────────────────────────────────────────────────

def get_project(db: Session, project_id: int) -> Project | None:
    return (
        db.query(Project)
        .options(joinedload(Project.members).joinedload(ProjectMember.user))
        .filter(Project.id == project_id, Project.is_deleted == False)
        .first()
    )


def get_projects_for_user(
    db: Session, user_id: int, skip: int = 0, limit: int = 50
) -> list[Project]:
    """Return all non-deleted projects where user is owner OR member."""
    owned = db.query(Project.id).filter(
        Project.owner_id == user_id, Project.is_deleted == False
    )
    member_of = (
        db.query(ProjectMember.project_id)
        .join(Project)
        .filter(ProjectMember.user_id == user_id, Project.is_deleted == False)
    )
    project_ids = owned.union(member_of).subquery()

    return (
        db.query(Project)
        .filter(Project.id.in_(project_ids))
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_project(db: Session, project_in: ProjectCreate, owner_id: int) -> Project:
    project = Project(**project_in.model_dump(), owner_id=owner_id)
    db.add(project)
    db.flush()  # get project.id without committing

    # Auto-add owner as a member with 'owner' role
    member = ProjectMember(
        project_id=project.id, user_id=owner_id, role=ProjectMemberRole.owner
    )
    db.add(member)
    db.commit()
    db.refresh(project)
    return project


def update_project(db: Session, project: Project, project_in: ProjectUpdate) -> Project:
    update_data = project_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


def soft_delete_project(db: Session, project: Project) -> Project:
    project.is_deleted = True
    db.commit()
    db.refresh(project)
    return project


# ─── Project Members ──────────────────────────────────────────────────────────

def get_member(db: Session, project_id: int, user_id: int) -> ProjectMember | None:
    return (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
        .first()
    )


def add_member(db: Session, project_id: int, member_in: ProjectMemberAdd) -> ProjectMember:
    member = ProjectMember(
        project_id=project_id,
        user_id=member_in.user_id,
        role=member_in.role,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def update_member_role(
    db: Session, member: ProjectMember, role: ProjectMemberRole
) -> ProjectMember:
    member.role = role
    db.commit()
    db.refresh(member)
    return member


def remove_member(db: Session, member: ProjectMember) -> None:
    db.delete(member)
    db.commit()
