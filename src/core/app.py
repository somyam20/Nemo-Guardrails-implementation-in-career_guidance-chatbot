from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.router import chat, health, user
from src.utils.logger import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title="Career Guidance Bot",
        description="AI-powered career guidance and learning path recommendations",
        version="1.0.0"
    )
    
    # CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure this based on your requirements
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(user.router, tags=["User"])
    app.include_router(chat.router, tags=["Chat"])
    
    logger.info("Career Guidance Bot API initialized successfully")
    
    return app