from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.api.v1.router import api_router

# ─── Rate Limiter ─────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Smart Task Management API

A production-grade backend for managing projects and tasks, similar to Jira/Trello.

### Features
- 🔐 JWT Authentication with refresh token rotation
- 👥 Project membership with role-based access (owner / editor / viewer)
- 📋 Task management with filtering, pagination, and soft deletes
- 🛡️ Rate limiting on auth endpoints
- 📖 Full Swagger docs with Authorize button
    """,
    openapi_tags=[
        {"name": "Auth", "description": "Register, login, token refresh, logout"},
        {"name": "Users", "description": "User profile management and admin operations"},
        {"name": "Projects", "description": "Project CRUD and membership management"},
        {"name": "Tasks", "description": "Task CRUD, status updates, filtering and pagination"},
    ],
    # Swagger Authorize button support
    swagger_ui_init_oauth={},
    components={
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
    },
)

# ─── Rate Limiting ────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Validation Error Handler ─────────────────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " → ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": errors},
    )

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(api_router)


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"], summary="Health check")
def health():
    return {"status": "ok", "version": settings.APP_VERSION}


@app.get("/", tags=["Health"], include_in_schema=False)
def root():
    return {"message": f"Welcome to {settings.APP_NAME} API", "docs": "/docs"}
