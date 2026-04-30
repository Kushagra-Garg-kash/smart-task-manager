# Import Base and all models here so that Alembic autogenerate can detect them.
from app.db.base_class import Base  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.project import Project, ProjectMember  # noqa: F401
from app.models.task import Task  # noqa: F401
from app.models.token import RefreshToken  # noqa: F401
