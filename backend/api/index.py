"""
Vercel Serverless Function Handler for FastAPI Backend
This file serves as the entry point for Vercel's Python runtime.
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import the FastAPI app
from app.main import app

# Vercel looks for this handler function
def handler(event, context):
    """
    Vercel serverless function handler.
    Forwards requests to the FastAPI application.
    """
    from mangum import Mangum

    # Create an ASGI handler for FastAPI
    asgi_handler = Mangum(app, lifespan="off")

    return asgi_handler(event, context)

# Alternative: Use Mangum directly
# This is the recommended approach for FastAPI on Vercel
try:
    from mangum import Mangum
    lambda_handler = Mangum(app, lifespan="off")
except ImportError:
    # Fallback if mangum is not installed
    lambda_handler = handler
