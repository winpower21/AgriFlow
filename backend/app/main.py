"""
AgriFlow Application Entry Point
=================================

This module defines the FastAPI application factory, including:

- **Lifespan handler**: Seeds the database with default roles (admin, manager, user)
  on first startup if the roles table is empty.
- **CORS middleware**: Configured from environment-based allowed origins so the
  Vue frontend can communicate with the API during development and production.
- **Router mounting**: All domain routers (auth, users, personnel, plantation,
  expense, settings, general, weather) are registered here.
- **Health/diagnostic endpoints**: Root (/), health (/health), and database
  connection check (/connection) endpoints for monitoring and debugging.

Run directly with ``python -m app.main`` for local development, or use
``uvicorn app.main:app --reload`` via the CLI.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from .config import settings
from .database import SessionLocal, engine
from .models.user import Role
from .routers import approval, auth, consumable, expense, general, personnel, plantation, users, vehicle, weather_google
from .routers.weather_google import location_weather_router
from .routers.plantation import locations_router
# Aliased to avoid collision with the stdlib/app-level `settings` object
from .routers import settings as settings_route


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager (replaces deprecated on_event hooks).

    **Startup phase** (before ``yield``):
      - Opens a synchronous DB session and seeds three default roles
        (admin, manager, user) when the roles table is empty.  This ensures
        a freshly-migrated database has usable roles for the first-user
        auto-admin registration flow.

    **Shutdown phase** (after ``yield``):
      - Currently only logs a shutdown message; add cleanup logic here
        (e.g., closing connection pools) if needed in the future.
    """
    # --- Startup ---
    print("Application starting up...")

    # Ensure upload directories exist
    upload_root = Path(settings.UPLOAD_DIR)
    (upload_root / "personnel").mkdir(parents=True, exist_ok=True)
    print(f"Upload directory ready: {upload_root.resolve()}")

    # Use a short-lived session purely for the seeding operation
    db = SessionLocal()

    # Create base roles if they don't exist
    print("Creating base roles if necessary...")
    try:
        roles_exist = db.query(Role).count() > 0
        if not roles_exist:
            # Seed the three default roles used by the RBAC system
            db.add(Role(name="admin", description="Administrator with full access"))
            db.add(Role(name="manager", description="Manager with limited access"))
            db.add(Role(name="user", description="Regular user with basic access"))
            db.commit()
            print("Base roles created.")
        else:
            print("Base roles already exist, skipping creation.")
    except Exception as e:
        print(f"Error during role creation: {e}")
    yield

    # --- Shutdown ---
    print("Application shutting down...")


# ---------------------------------------------------------------------------
# FastAPI application instance
# ---------------------------------------------------------------------------
# The ``lifespan`` parameter replaces the older @app.on_event decorators and
# ensures startup/shutdown logic is handled via a single async context manager.
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="FastAPI backend with PostgreSQL",
    docs_url="/api/docs",  # Swagger UI available at /api/docs
    redoc_url="/api/redoc",  # ReDoc alternative docs at /api/redoc
    lifespan=lifespan,
)

# Serve uploaded files as static assets
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# ---------------------------------------------------------------------------
# CORS middleware — allows the Vue 3 frontend (default localhost:5173) to
# make cross-origin requests.  Origins are read from the ALLOWED_ORIGINS
# env var (comma-separated string) and parsed by ``settings.cors_origins``.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Parsed list from ALLOWED_ORIGINS env var
    allow_credentials=True,               # Allow cookies / Authorization headers
    allow_methods=["*"],                  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],                  # Allow all request headers
)

# ---------------------------------------------------------------------------
# Router registration — each router handles a distinct domain area.
# Routers define their own URL prefixes and tags internally.
# ---------------------------------------------------------------------------
app.include_router(approval.router)         # /approvals — approval workflow
app.include_router(auth.router)             # /auth — login, registration, token refresh
app.include_router(users.router)            # /users — user management
app.include_router(personnel.router)        # /personnel — farm worker records
app.include_router(plantation.router)       # /plantations — plantation/crop tracking
app.include_router(locations_router)        # /locations — location search and resolve
app.include_router(expense.router)          # /expenses — expense tracking
app.include_router(settings_route.router)   # /settings — application settings
app.include_router(consumable.router)       # /consumables — consumable items and purchases
app.include_router(vehicle.router)          # /vehicles — vehicle management
app.include_router(general.router)          # /general — shared/utility endpoints
app.include_router(weather_google.router)       # /api/weather — pass-through to Google API
app.include_router(location_weather_router)    # /api/weather — location-centric cached weather


# Root endpoint
@app.get("/")
def read_root():
    """Root endpoint - API health check."""
    return {
        "message": "Welcome to FastAPI Backend",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/api/docs",
    }


# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}


@app.get("/connection")
def root():
    """Database connectivity check — executes ``SELECT 1`` to verify the
    PostgreSQL connection is alive.  Useful during deployment debugging."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(result.scalar())


if __name__ == "__main__":
    # Convenience entry point: ``python -m app.main``
    # Hot-reload is enabled automatically when ENVIRONMENT=development.
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
    )
