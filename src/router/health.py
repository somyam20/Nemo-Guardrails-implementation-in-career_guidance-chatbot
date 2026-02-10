from fastapi import APIRouter
from datetime import datetime
from src.utils.logger import logger

router = APIRouter()

@router.get("/health")
def health_check():
    """
    Health check endpoint to verify the API is running.
    
    Returns:
        Dictionary with status and timestamp
    """
    logger.info("Health check endpoint called")
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Career Guidance Bot"
    }


@router.get("/")
def root():
    """
    Root endpoint with API information.
    
    Returns:
        Dictionary with API welcome message
    """
    return {
        "message": "Welcome to Career Guidance Bot API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "questions": "/user/questions",
            "chat": "/chat/"
        }
    }