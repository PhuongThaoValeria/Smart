"""
Smart English Test-Prep Agent - FastAPI Main Application
REST API endpoints for the English learning system
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from app.config import get_config, logging_config
from app.database import get_db_connection, init_db
from app.routes import (
    daily_tests,
    feedback,
    assessment,
    counseling,
    students,
    health
)


# Configure logging
logging.basicConfig(
    level=getattr(logging, logging_config.level),
    format=logging_config.format,
    handlers=[
        logging.FileHandler(logging_config.log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Smart English Test-Prep Agent API...")
    logger.info(f"Environment: {get_config().app.environment}")
    logger.info(f"Version: {get_config().app.version}")

    # Initialize database (optional for demo)
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization failed (continuing without DB): {e}")
        logger.info("API running in DEMO mode - database features disabled")

    yield

    # Shutdown
    logger.info("Shutting down Smart English Test-Prep Agent API...")


# Create FastAPI application
app = FastAPI(
    title="Smart English Test-Prep Agent",
    description="AI-powered adaptive learning system for Vietnamese high school students",
    version=get_config().app.version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# GZip middleware for response compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning(f"Validation error on {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle global exceptions."""
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": str(exc) if get_config().app.environment == "development" else "An error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    start_time = datetime.now()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = (datetime.now() - start_time).total_seconds()

    # Log request
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration:.3f}s"
    )

    # Add timing header
    response.headers["X-Process-Time"] = str(duration)

    return response


# Include routers
app.include_router(
    health.router,
    prefix="/api/v1/health",
    tags=["Health"]
)

app.include_router(
    students.router,
    prefix="/api/v1/students",
    tags=["Students"]
)

app.include_router(
    daily_tests.router,
    prefix="/api/v1/daily-tests",
    tags=["Daily Tests"]
)

app.include_router(
    feedback.router,
    prefix="/api/v1/feedback",
    tags=["Feedback"]
)

app.include_router(
    assessment.router,
    prefix="/api/v1/assessment",
    tags=["Assessment"]
)

app.include_router(
    counseling.router,
    prefix="/api/v1/counseling",
    tags=["Counseling"]
)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Smart English Test-Prep Agent API",
        "version": get_config().app.version,
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        },
        "endpoints": {
            "health": "/api/v1/health",
            "students": "/api/v1/students",
            "daily_tests": "/api/v1/daily-tests",
            "feedback": "/api/v1/feedback",
            "assessment": "/api/v1/assessment",
            "counseling": "/api/v1/counseling"
        }
    }


# Startup info
@app.get("/info", tags=["Root"])
async def info():
    """API information endpoint."""
    config = get_config()
    return {
        "application": {
            "name": config.app.name,
            "version": config.app.version,
            "environment": config.app.environment
        },
        "features": {
            "daily_tests": {
                "enabled": True,
                "duration_minutes": config.test.daily_test_duration_minutes,
                "question_count": config.test.daily_test_question_count
            },
            "mega_tests": {
                "enabled": True,
                "duration_minutes": config.test.mega_test_duration_minutes,
                "question_count": config.test.mega_test_question_count,
                "interval_days": config.test.mega_test_interval_days
            },
            "adaptive_learning": {
                "enabled": True,
                "weight_increase": "40%",
                "weight_cap": 3.0
            }
        },
        "database": {
            "host": config.db.host,
            "port": config.db.port,
            "name": config.db.name,
            "connected": True  # TODO: Check actual connection
        },
        "llm": {
            "provider": "Anthropic",
            "model": config.llm.model
        }
    }


if __name__ == "__main__":
    import uvicorn

    config = get_config()

    uvicorn.run(
        "app.main:app",
        host=config.api.host,
        port=config.api.port,
        reload=config.api.debug,
        log_level=config.logging.level.lower()
    )
