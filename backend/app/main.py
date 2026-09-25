"""
Cogent Backend - Main Application Entrypoint
Initializes FastAPI, sets up CORS middleware, loads database models, and registers routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import engine, Base
from app.api.router import api_router

# Ensure all SQLAlchemy models are imported so Base.metadata knows about them
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Create tables if they do not exist yet (bootstrap development)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Cognitive Evidence-Grounded Reasoning and Research Agent",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(api_router)


@app.get("/", tags=["System"])
def root():
    """Root entrypoint with service metadata and documentation links."""
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "description": "Cognitive Evidence-Grounded Reasoning & Research Agent API",
        "documentation": "/docs",
        "openapi_spec": "/openapi.json",
        "health_check": "/health",
        "frontend_cockpit": "http://localhost:5173",
        "version": "1.0.0",
        "layers": "Layers 1-10 actively registered under /api/v1/"
    }


@app.get("/health", tags=["System"])
def root_health():
    """System-level health check."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0",
    }
