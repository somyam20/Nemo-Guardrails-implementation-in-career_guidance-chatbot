import os
import requests
from typing import List
from dotenv import load_dotenv
from src.utils.logger import logger

# Load environment variables
load_dotenv()

# Get Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

# Gemini API endpoint for embeddings
EMBEDDING_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent"


def embed_text(text: str) -> List[float]:
    """
    Generate embeddings for given text using Google Gemini's embedding model.
    Uses gemini-embedding-001 with output dimension reduced to 768.
    
    Args:
        text: Input text to embed
        
    Returns:
        List of floats representing the embedding vector (768 dimensions)
        
    Raises:
        Exception: If embedding generation fails
    """
    try:
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "models/gemini-embedding-001",
            "content": {
                "parts": [{"text": text}]
            },
            "outputDimensionality": 768  # Reduce from 3072 to 768
        }
        
        response = requests.post(
            f"{EMBEDDING_URL}?key={GEMINI_API_KEY}",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            embedding = result['embedding']['values']
            logger.info(f"Generated embedding for text of length {len(text)} (dimension: {len(embedding)})")
            return embedding
        else:
            error_msg = f"API returned status {response.status_code}: {response.text}"
            logger.error(f"Error generating embedding: {error_msg}")
            raise Exception(error_msg)
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error generating embedding: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        raise


def embed_texts_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts.
    Calls the API once per text with 768-dimensional output.
    
    Args:
        texts: List of text strings to generate embeddings for
        
    Returns:
        List of embedding vectors (one per input text)
        
    Raises:
        Exception: If any embedding generation fails
    """
    if not texts:
        return []
    
    embeddings = []
    for i, text in enumerate(texts):
        try:
            embedding = embed_text(text)
            embeddings.append(embedding)
            logger.info(f"Generated embedding {i+1}/{len(texts)}")
        except Exception as e:
            logger.error(f"Failed to generate embedding for text {i+1}: {str(e)}")
            raise
    
    logger.info(f"Successfully generated {len(embeddings)} embeddings")
    return embeddings