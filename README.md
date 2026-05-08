# Smart Task Manager

A REST API backend for managing projects and tasks — think a stripped-down Jira/Trello backend. Built with FastAPI and PostgreSQL as a way to get hands-on with real backend engineering concepts like JWT auth, role-based access control, and layered architecture.

## What it does

- Users can register, login, and manage their sessions via JWT access + refresh tokens
- Refresh tokens rotate on every use and are revoked server-side on logout — no replay attacks
- Users can create projects and invite members with different roles (owner, editor, viewer)
- Tasks can be created inside projects, filtered by status/priority, paginated, and soft deleted
- Assignee validation — you can only assign a task to someone who's already a project member

## Tech stack

- **FastAPI** — API framework
- **PostgreSQL** — primary database
- **SQLAlchemy 2.0** — ORM with eager loading to avoid N+1 queries
- **Alembic** — database migrations
- **python-jose** — JWT encoding/decoding
- **Passlib + bcrypt** — password hashing
- **pydantic-settings** — environment-based config
- **slowapi** — rate limiting on auth endpoints
- **pytest** — 35 integration tests using in-memory SQLite

## Project structure

```
app/
├── api/v1/          # route handlers (auth, users, projects, tasks)
├── core/            # config and security utilities
├── db/              # database session and base class
├── models/          # SQLAlchemy models
├── schemas/         # Pydantic schemas
├── crud/            # database operations
└── services/        # business logic layer
tests/
├── api/             # integration tests for all endpoints
└── test_security.py # unit tests for JWT and password hashing
```

## Running locally

**Prerequisites:** Python 3.12+, PostgreSQL

```bash
# Clone the repo
git clone https://github.com/Kushagra-Garg-kash/smart-task-manager.git
cd smart_task_manager

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Fill in DATABASE_URL and SECRET_KEY in .env

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

API docs will be available at **http://127.0.0.1:8000/docs**

## Running with Docker

```bash
docker-compose up --build
```

This spins up the API and a PostgreSQL container together. Migrations run automatically on startup.

## Running tests

```bash
pytest tests/ -v
```

Tests use an in-memory SQLite database — no PostgreSQL needed.

## API overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/auth/register | Register a new user |
| POST | /api/v1/auth/login | Login and get tokens |
| POST | /api/v1/auth/refresh | Rotate refresh token |
| POST | /api/v1/auth/logout | Revoke refresh token |
| GET | /api/v1/auth/me | Get current user |
| GET/POST | /api/v1/projects | List or create projects |
| GET/PATCH/DELETE | /api/v1/projects/{id} | Manage a project |
| POST | /api/v1/projects/{id}/members | Add a member |
| GET/POST | /api/v1/projects/{id}/tasks | List or create tasks |
| GET/PATCH/DELETE | /api/v1/projects/{id}/tasks/{id} | Manage a task |

## Environment variables

```
DATABASE_URL=postgresql://user:password@localhost:5432/smart_task_db
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALLOWED_ORIGINS=["http://localhost:3000"]
```