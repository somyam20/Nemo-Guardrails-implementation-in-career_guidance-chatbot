
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
from src.utils.config_loader import load_yaml
from src.core.database import create_user_profile, get_user_profile
from src.core.pdf_processor import process_pdf_upload
from src.utils.logger import logger
from datetime import datetime

router = APIRouter(prefix="/user")


class UserProfileCreate(BaseModel):
    """Schema for creating user profile"""
    user_id: str
    session_id: str
    answers: dict


class UserProfileResponse(BaseModel):
    """Schema for user profile response"""
    user_id: str
    answers: dict
    created_at: str
    updated_at: str


class UploadResponse(BaseModel):
    """Schema for upload response"""
    user_id: str
    session_id: str
    filename: str
    chunks_created: int
    vectors_inserted: int
    message: str


@router.get("/questions")
def get_questions():
    """
    Get the questionnaire for career assessment.
    
    Returns:
        Dictionary containing questions from YAML config
    """
    try:
        questions = load_yaml("questions.yaml")
        logger.info("Questions retrieved successfully")
        return questions
    except Exception as e:
        logger.error(f"Error loading questions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load questions")


@router.post("/profile", response_model=UserProfileResponse)
def create_or_update_profile(profile_data: UserProfileCreate):
    """
    Create or update user profile with questionnaire answers.
    
    Args:
        profile_data: User profile data with user_id, session_id, and answers
        
    Returns:
        Created or updated user profile
    """
    try:
        success = create_user_profile(
            user_id=profile_data.user_id,
            answers=profile_data.answers
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save user profile")
        
        # Get the created/updated profile
        profile = get_user_profile(profile_data.user_id)
        
        if not profile:
            raise HTTPException(status_code=500, detail="Profile created but could not retrieve it")
        
        logger.info(f"Profile saved for user: {profile_data.user_id}")
        
        return UserProfileResponse(
            user_id=profile['user_id'],
            answers=profile['answers'],
            created_at=profile['created_at'].isoformat() if isinstance(profile['created_at'], datetime) else profile['created_at'],
            updated_at=profile['updated_at'].isoformat() if isinstance(profile['updated_at'], datetime) else profile['updated_at']
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating/updating user profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save user profile: {str(e)}")


@router.get("/profile/{user_id}", response_model=UserProfileResponse)
def get_profile(user_id: str):
    """
    Retrieve user profile by user ID.
    
    Args:
        user_id: User identifier
        
    Returns:
        User profile data
    """
    try:
        profile = get_user_profile(user_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        logger.info(f"Retrieved profile for user: {user_id}")
        
        return UserProfileResponse(
            user_id=profile['user_id'],
            answers=profile['answers'],
            created_at=profile['created_at'].isoformat() if isinstance(profile['created_at'], datetime) else profile['created_at'],
            updated_at=profile['updated_at'].isoformat() if isinstance(profile['updated_at'], datetime) else profile['updated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user profile")


@router.post("/upload-knowledge", response_model=UploadResponse)
async def upload_knowledge_base(
    user_id: str,
    session_id: str,
    file: UploadFile = File(...)
):
    """
    Upload PDF to create/update user's career knowledge base.
    PDF will be chunked and stored in Milvus for RAG.
    
    Args:
        user_id: User identifier (form parameter)
        session_id: Session identifier (form parameter)
        file: PDF file upload
        
    Returns:
        Upload status and statistics
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        logger.info(f"Processing PDF upload for user: {user_id}, session: {session_id}, file: {file.filename}")
        
        # Read file content
        content = await file.read()
        
        # Process PDF and create embeddings
        result = await process_pdf_upload(
            user_id=user_id,
            session_id=session_id,
            filename=file.filename,
            pdf_content=content
        )
        
        logger.info(f"Successfully processed {file.filename} - {result['chunks_created']} chunks created")
        
        return UploadResponse(
            user_id=user_id,
            session_id=session_id,
            filename=file.filename,
            chunks_created=result['chunks_created'],
            vectors_inserted=result['vectors_inserted'],
            message=f"Successfully processed {file.filename}. Created {result['chunks_created']} knowledge chunks."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing PDF upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process PDF: {str(e)}"
        )


@router.get("/knowledge-base/{user_id}/{session_id}/stats")
def get_knowledge_base_stats(user_id: str, session_id: str):
    """
    Get statistics about user's knowledge base.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        
    Returns:
        Knowledge base statistics
    """
    try:
        from src.core.career_engine import get_knowledge_base_stats
        
        stats = get_knowledge_base_stats(user_id, session_id)
        
        return {
            "user_id": user_id,
            "session_id": session_id,
            "total_chunks": stats.get('total_chunks', 0),
            "total_documents": stats.get('total_documents', 0),
            "last_updated": stats.get('last_updated')
        }
        
    except Exception as e:
        logger.error(f"Error retrieving knowledge base stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve knowledge base statistics"
        )