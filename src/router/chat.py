
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
from src.core.career_engine import career_guidance_rag, search_career_paths
from src.core.database import (
    save_conversation, 
    get_conversation_history,
    save_career_recommendation,
    get_user_profile
)
from src.utils.logger import logger
from datetime import datetime

router = APIRouter(prefix="/chat")


class ChatRequest(BaseModel):
    """Schema for chat request"""
    user_id: str
    session_id: str
    query: str


class ChatResponse(BaseModel):
    """Schema for chat response"""
    user_id: str
    session_id: str
    query: str
    response: str
    matched_careers: List[str]
    confidence_score: float
    timestamp: str


class CareerSearchRequest(BaseModel):
    """Schema for career search request"""
    user_id: str
    session_id: str
    query: str
    limit: Optional[int] = 5


@router.post("/query", response_model=ChatResponse)
async def chat_query(req: ChatRequest):
    """
    Main chat endpoint for career guidance using RAG.
    
    Args:
        req: Chat request with user_id, session_id, and query
        
    Returns:
        Career guidance response with recommendations based on user's knowledge base
    """
    try:
        logger.info(f"Processing chat query for user: {req.user_id}, session: {req.session_id}")
        
        # Get user profile (answers to questions)
        user_profile = get_user_profile(req.user_id)
        
        if not user_profile:
            raise HTTPException(
                status_code=404,
                detail=f"User profile not found. Please complete the questionnaire first."
            )
        
        # Get conversation history for context
        history = get_conversation_history(req.user_id, req.session_id, limit=5)
        
        # Generate career guidance using RAG
        guidance = await career_guidance_rag(
            user_id=req.user_id,
            session_id=req.session_id,
            query=req.query,
            user_profile=user_profile.get('answers', {}),
            conversation_history=history
        )
        
        # Save conversation
        save_conversation(
            user_id=req.user_id,
            session_id=req.session_id,
            question=req.query,
            answer=guidance["response"]
        )
        
        # Save recommendation if careers were matched
        if guidance.get("matched_careers"):
            save_career_recommendation(
                user_id=req.user_id,
                session_id=req.session_id,
                recommendation=guidance["response"],
                metadata={
                    "matched_careers": guidance["matched_careers"],
                    "confidence_score": guidance["confidence_score"],
                    "query": req.query
                }
            )
        
        logger.info(f"Successfully processed query for user: {req.user_id}")
        
        return ChatResponse(
            user_id=req.user_id,
            session_id=req.session_id,
            query=req.query,
            response=guidance["response"],
            matched_careers=guidance.get("matched_careers", []),
            confidence_score=guidance.get("confidence_score", 0.0),
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat query endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate career guidance: {str(e)}"
        )


@router.post("/search-careers")
async def search_careers(req: CareerSearchRequest):
    """
    Search for career paths in user's knowledge base based on query.
    
    Args:
        req: Search request with user_id, session_id, and query
        
    Returns:
        List of matching career paths from user's uploaded documents
    """
    try:
        logger.info(f"Searching careers for user: {req.user_id}, session: {req.session_id}")
        
        careers = await search_career_paths(
            user_id=req.user_id,
            session_id=req.session_id,
            query=req.query,
            limit=req.limit
        )
        
        return {
            "user_id": req.user_id,
            "session_id": req.session_id,
            "query": req.query,
            "results": careers,
            "count": len(careers)
        }
        
    except Exception as e:
        logger.error(f"Error in career search: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search careers: {str(e)}"
        )


@router.get("/history/{user_id}/{session_id}")
def get_chat_history(user_id: str, session_id: str, limit: int = 10):
    """
    Get conversation history for a user session.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        limit: Maximum number of conversations to retrieve
        
    Returns:
        List of past conversations for this session
    """
    try:
        conversations = get_conversation_history(user_id, session_id, limit)
        
        logger.info(f"Retrieved {len(conversations)} conversations for user: {user_id}, session: {session_id}")
        
        return {
            "user_id": user_id,
            "session_id": session_id,
            "conversations": conversations
        }
        
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve conversation history"
        )


@router.get("/recommendations/{user_id}/{session_id}")
def get_user_recommendations_by_session(user_id: str, session_id: str, limit: int = 5):
    """
    Get career recommendations for a user session.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        limit: Maximum number of recommendations to retrieve
        
    Returns:
        List of career recommendations for this session
    """
    try:
        recommendations = get_career_recommendations(user_id, session_id, limit)
        
        logger.info(f"Retrieved {len(recommendations)} recommendations for user: {user_id}, session: {session_id}")
        
        return {
            "user_id": user_id,
            "session_id": session_id,
            "recommendations": recommendations
        }
        
    except Exception as e:
        logger.error(f"Error retrieving recommendations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve recommendations"
        )