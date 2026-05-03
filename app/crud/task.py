from sqlalchemy.orm import Session, joinedload
from app.models.task import Task, TaskStatus, TaskPriority
from app.schemas.task import TaskCreate, TaskUpdate, TaskFilters


def get_task(db: Session, task_id: int) -> Task | None:
    return (
        db.query(Task)
        .options(joinedload(Task.assignee))
        .filter(Task.id == task_id, Task.is_deleted == False)
        .first()
    )


def get_tasks_for_project(
    db: Session,
    project_id: int,
    filters: TaskFilters,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Task], int]:
    """Returns (tasks, total_count) with applied filters."""
    query = (
        db.query(Task)
        .options(joinedload(Task.assignee))
        .filter(Task.project_id == project_id, Task.is_deleted == False)
    )

    if filters.status is not None:
        query = query.filter(Task.status == filters.status)
    if filters.priority is not None:
        query = query.filter(Task.priority == filters.priority)
    if filters.assigned_to is not None:
        query = query.filter(Task.assigned_to == filters.assigned_to)

    total = query.count()
    tasks = query.order_by(Task.created_at.desc()).offset(skip).limit(limit).all()
    return tasks, total


def create_task(db: Session, task_in: TaskCreate, project_id: int) -> Task:
    task = Task(**task_in.model_dump(), project_id=project_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task: Task, task_in: TaskUpdate) -> Task:
    update_data = task_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


def update_task_status(db: Session, task: Task, status: TaskStatus) -> Task:
    task.status = status
    db.commit()
    db.refresh(task)
    return task


def soft_delete_task(db: Session, task: Task) -> Task:
    task.is_deleted = True
    db.commit()
    db.refresh(task)
    return task
