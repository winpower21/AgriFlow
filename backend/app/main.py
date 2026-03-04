from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .config import settings
from .database import SessionLocal, engine
from .models.user import Role
from .routers import auth, expense, general, personnel, plantation, users, weather_google
from .routers import settings as settings_route


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Logic to run on startup
    print("Application starting up...")
    db = SessionLocal()

    # Create base roles if they don't exist
    print("Creating base roles if necessary...")
    try:
        # Check if roles table is empty (replace with your actual DB query)
        roles_exist = db.query(Role).count() > 0  # Example query
        if not roles_exist:
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

    # Logic to run on shutdown (optional)
    print("Application shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="FastAPI backend with PostgreSQL",
    docs_url="/api/docs",  # Swagger UI
    redoc_url="/api/redoc",  # ReDoc
    lifespan=lifespan,
)

# Configure CORS for Vue frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # List of allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(personnel.router)
app.include_router(plantation.router)
app.include_router(expense.router)
app.include_router(settings_route.router)
app.include_router(general.router)
app.include_router(weather_google.router)


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
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(result.scalar())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
    )
