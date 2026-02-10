
from pymilvus import connections, Collection, utility
import os
from typing import List, Dict, Any
from src.core.embeddings import embed_text
from src.core.llm import generate_response
from src.utils.logger import logger
from src.utils.config_loader import load_yaml

# Connect to Milvus (Zilliz Cloud)
try:
    connections.connect(
        alias="default",
        uri=os.getenv("MILVUS_URI"),
        token=os.getenv("MILVUS_API_KEY")
    )
    logger.info("Successfully connected to Milvus")
except Exception as e:
    logger.error(f"Failed to connect to Milvus: {str(e)}")
    raise

# Collection name for user knowledge base
COLLECTION_NAME = "user_career_knowledge"


def get_collection():
    """Get or create the Milvus collection"""
    try:
        if utility.has_collection(COLLECTION_NAME):
            collection = Collection(COLLECTION_NAME)
            logger.info(f"Loaded existing collection: {COLLECTION_NAME}")
        else:
            logger.info(f"Creating new collection: {COLLECTION_NAME}")
            collection = create_collection()
        
        collection.load()
        return collection
    except Exception as e:
        logger.error(f"Error accessing collection: {str(e)}")
        raise


def create_collection():
    """Create Milvus collection for user knowledge base"""
    from pymilvus import FieldSchema, CollectionSchema, DataType, Collection
    
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=255),
        FieldSchema(name="session_id", dtype=DataType.VARCHAR, max_length=255),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="filename", dtype=DataType.VARCHAR, max_length=500),
        FieldSchema(name="chunk_index", dtype=DataType.INT64),
    ]
    
    schema = CollectionSchema(fields, description="User career knowledge base from uploaded PDFs")
    collection = Collection(name=COLLECTION_NAME, schema=schema)
    
    # Create index for vector search
    index_params = {
        "metric_type": "IP",  # Inner Product
        "index_type": "IVF_FLAT",
        "params": {"nlist": 1024}
    }
    collection.create_index(field_name="embedding", index_params=index_params)
    
    logger.info(f"Collection '{COLLECTION_NAME}' created successfully")
    return collection


async def insert_knowledge_chunks(
    user_id: str,
    session_id: str,
    embeddings: List[List[float]],
    chunks: List[str],
    metadata_list: List[Dict[str, Any]]
) -> int:
    """
    Insert knowledge chunks into Milvus.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        embeddings: List of embedding vectors
        chunks: List of text chunks
        metadata_list: List of metadata dictionaries
        
    Returns:
        Number of vectors inserted
    """
    try:
        collection = get_collection()
        
        # Prepare data for insertion
        user_ids = [user_id] * len(chunks)
        session_ids = [session_id] * len(chunks)
        filenames = [meta.get('filename', '') for meta in metadata_list]
        chunk_indices = [meta.get('chunk_index', i) for i, meta in enumerate(metadata_list)]
        
        entities = [
            user_ids,
            session_ids,
            embeddings,
            chunks,
            filenames,
            chunk_indices
        ]
        
        insert_result = collection.insert(entities)
        collection.flush()
        
        logger.info(f"Inserted {len(insert_result.primary_keys)} knowledge chunks for user {user_id}")
        return len(insert_result.primary_keys)
        
    except Exception as e:
        logger.error(f"Error inserting knowledge chunks: {str(e)}")
        raise


async def search_user_knowledge(
    user_id: str,
    session_id: str,
    query: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Search user's knowledge base using semantic search.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        query: Search query
        limit: Maximum number of results
        
    Returns:
        List of relevant knowledge chunks
    """
    try:
        # Generate query embedding
        query_vector = embed_text(query)
        
        collection = get_collection()
        
        # Search with user_id and session_id filter
        search_params = {
            "metric_type": "IP",
            "params": {"nprobe": 10}
        }
        
        # Filter by user_id and session_id
        expr = f'user_id == "{user_id}" && session_id == "{session_id}"'
        
        results = collection.search(
            data=[query_vector],
            anns_field="embedding",
            param=search_params,
            limit=limit,
            expr=expr,
            output_fields=["text", "filename", "chunk_index", "user_id", "session_id"]
        )
        
        knowledge_chunks = []
        if results and len(results[0]) > 0:
            for hit in results[0]:
                knowledge_chunks.append({
                    "text": hit.entity.get("text", ""),
                    "filename": hit.entity.get("filename", ""),
                    "chunk_index": hit.entity.get("chunk_index", 0),
                    "relevance_score": hit.score
                })
                logger.info(f"Found relevant chunk with score: {hit.score}")
        
        return knowledge_chunks
        
    except Exception as e:
        logger.error(f"Error searching user knowledge: {str(e)}")
        raise


async def career_guidance_rag(
    user_id: str,
    session_id: str,
    query: str,
    user_profile: Dict[str, Any],
    conversation_history: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate career guidance using RAG (Retrieval-Augmented Generation).
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        query: User's question/query
        user_profile: User's questionnaire answers
        conversation_history: Previous conversations in this session
        
    Returns:
        Dictionary containing response and metadata
    """
    try:
        logger.info(f"Generating RAG response for user: {user_id}, session: {session_id}")
        
        # Load prompt template
        prompts = load_yaml("prompts_template.yaml")
        
        # Search user's knowledge base
        knowledge_chunks = await search_user_knowledge(
            user_id=user_id,
            session_id=session_id,
            query=query,
            limit=5
        )
        
        # Build context from retrieved knowledge
        if knowledge_chunks:
            context = "\n\n".join([
                f"[From {chunk['filename']}, Chunk {chunk['chunk_index']}]:\n{chunk['text']}"
                for chunk in knowledge_chunks
            ])
        else:
            context = "No specific career knowledge found in your uploaded documents. I'll provide general career guidance."
        
        # Build user profile text
        profile_parts = []
        for key, value in user_profile.items():
            if isinstance(value, list):
                profile_parts.append(f"{key}: {', '.join(value)}")
            else:
                profile_parts.append(f"{key}: {value}")
        profile_text = "\n".join(profile_parts)
        
        # Build conversation context
        history_text = ""
        if conversation_history:
            recent_history = conversation_history[:3]  # Last 3 conversations
            history_parts = []
            for conv in reversed(recent_history):  # Show oldest first
                history_parts.append(f"User: {conv.get('question', '')}")
                history_parts.append(f"Assistant: {conv.get('answer', '')[:200]}...")  # Truncate long answers
            history_text = "\n".join(history_parts)
        
        # Build the complete prompt
        career_prompt_template = prompts.get("career_guidance_prompt", "")
        
        # Create enhanced prompt with all context
        full_prompt = f"""You are an expert career counselor providing personalized guidance.

## User Profile:
{profile_text}

## Previous Conversation Context:
{history_text if history_text else "This is the start of the conversation."}

## Relevant Knowledge from User's Documents:
{context}

## User's Current Question:
{query}

Based on all the above information, provide a comprehensive, personalized response that:
1. Directly answers the user's question
2. References specific information from their uploaded documents when relevant
3. Considers their profile and previous discussions
4. Provides actionable advice and next steps
5. Maintains continuity with the ongoing conversation

Your response:"""
        
        # Generate response
        response = await generate_response(full_prompt, temperature=0.7)
        
        # Extract career paths mentioned in knowledge chunks
        matched_careers = []
        for chunk in knowledge_chunks:
            # Simple extraction - could be enhanced with NLP
            text = chunk['text'].lower()
            if 'career' in text or 'job' in text or 'role' in text:
                # Extract potential career names (this is simplified)
                matched_careers.append(chunk['filename'])
        
        matched_careers = list(set(matched_careers))  # Remove duplicates
        
        # Calculate average relevance score
        avg_score = sum(chunk['relevance_score'] for chunk in knowledge_chunks) / len(knowledge_chunks) if knowledge_chunks else 0.0
        
        logger.info(f"Successfully generated RAG response with {len(knowledge_chunks)} knowledge chunks")
        
        return {
            "response": response,
            "matched_careers": matched_careers,
            "confidence_score": avg_score,
            "knowledge_chunks_used": len(knowledge_chunks)
        }
        
    except Exception as e:
        logger.error(f"Error in career guidance RAG: {str(e)}")
        raise


async def search_career_paths(
    user_id: str,
    session_id: str,
    query: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Search for career-related content in user's knowledge base.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        query: Search query
        limit: Maximum number of results
        
    Returns:
        List of matching career information
    """
    try:
        knowledge_chunks = await search_user_knowledge(
            user_id=user_id,
            session_id=session_id,
            query=query,
            limit=limit
        )
        
        careers = []
        for chunk in knowledge_chunks:
            careers.append({
                "source": chunk['filename'],
                "content": chunk['text'],
                "chunk_index": chunk['chunk_index'],
                "relevance_score": chunk['relevance_score']
            })
        
        return careers
        
    except Exception as e:
        logger.error(f"Error searching career paths: {str(e)}")
        raise


def get_knowledge_base_stats(user_id: str, session_id: str) -> Dict[str, Any]:
    """
    Get statistics about user's knowledge base.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        
    Returns:
        Statistics about the knowledge base
    """
    try:
        from src.core.database import get_knowledge_uploads
        
        uploads = get_knowledge_uploads(user_id, session_id)
        
        total_chunks = sum(upload['chunks_created'] for upload in uploads)
        total_docs = len(uploads)
        last_updated = uploads[0]['uploaded_at'] if uploads else None
        
        return {
            "total_chunks": total_chunks,
            "total_documents": total_docs,
            "last_updated": last_updated.isoformat() if last_updated else None,
            "uploads": uploads
        }
        
    except Exception as e:
        logger.error(f"Error getting knowledge base stats: {str(e)}")
        return {
            "total_chunks": 0,
            "total_documents": 0,
            "last_updated": None
        }