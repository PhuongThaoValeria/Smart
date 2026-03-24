"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
from datetime import datetime

from app.database import check_db_connection
from app.models.api.responses import HealthResponse

router = APIRouter()


@router.get("", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint.

    Returns API status and database connectivity.
    """
    db_connected = await check_db_connection()

    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        database_connected=db_connected,
        timestamp=datetime.now()
    )


@router.get("/detailed")
async def detailed_health():
    """
    Detailed health check with system information.
    """
    from app.config import get_config

    config = get_config()
    db_connected = await check_db_connection()

    return {
        "status": "healthy" if db_connected else "degraded",
        "timestamp": datetime.now().isoformat(),
        "application": {
            "name": config.app.name,
            "version": config.app.version,
            "environment": config.app.environment
        },
        "database": {
            "connected": db_connected,
            "host": config.db.host,
            "port": config.db.port,
            "name": config.db.name
        },
        "features": {
            "daily_tests": True,
            "mega_tests": True,
            "feedback_engine": True,
            "counseling": True,
            "adaptive_learning": True
        }
    }


@router.get("/ping")
async def ping():
    """
    Simple ping endpoint for monitoring.
    """
    return {"ping": "pong", "timestamp": datetime.now().isoformat()}
