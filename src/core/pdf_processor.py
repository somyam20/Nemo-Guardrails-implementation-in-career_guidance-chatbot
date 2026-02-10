
import io
from typing import List, Dict, Any
from PyPDF2 import PdfReader
from src.core.embeddings import embed_texts_batch
from src.core.career_engine import insert_knowledge_chunks
from src.core.database import save_knowledge_upload
from src.utils.logger import logger


def extract_text_from_pdf(pdf_content: bytes) -> str:
    """
    Extract text from PDF content.
    
    Args:
        pdf_content: PDF file content as bytes
        
    Returns:
        Extracted text from all pages
    """
    try:
        pdf_file = io.BytesIO(pdf_content)
        reader = PdfReader(pdf_file)
        
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        logger.info(f"Extracted {len(text)} characters from PDF ({len(reader.pages)} pages)")
        return text
        
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Input text to chunk
        chunk_size: Maximum size of each chunk in characters
        overlap: Number of overlapping characters between chunks
        
    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        # Calculate end position
        end = start + chunk_size
        
        # If this is not the last chunk, try to break at a sentence or word boundary
        if end < text_length:
            # Look for sentence ending
            sentence_end = text.rfind('.', start, end)
            if sentence_end > start:
                end = sentence_end + 1
            else:
                # Look for word boundary
                space = text.rfind(' ', start, end)
                if space > start:
                    end = space
        
        # Extract chunk
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start position with overlap
        start = end - overlap if end < text_length else text_length
    
    logger.info(f"Created {len(chunks)} chunks from text")
    return chunks


async def process_pdf_upload(
    user_id: str,
    session_id: str,
    filename: str,
    pdf_content: bytes
) -> Dict[str, Any]:
    """
    Process uploaded PDF: extract text, chunk, create embeddings, and store in Milvus.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        filename: Name of the PDF file
        pdf_content: PDF file content as bytes
        
    Returns:
        Dictionary with processing statistics
    """
    try:
        logger.info(f"Processing PDF upload: {filename} for user {user_id}, session {session_id}")
        
        # Extract text from PDF
        text = extract_text_from_pdf(pdf_content)
        
        if not text or len(text.strip()) < 100:
            raise ValueError("PDF appears to be empty or contains insufficient text")
        
        # Chunk the text
        chunks = chunk_text(text, chunk_size=1000, overlap=200)
        
        if not chunks:
            raise ValueError("No valid chunks created from PDF")
        
        logger.info(f"Created {len(chunks)} chunks from {filename}")
        
        # Generate embeddings for all chunks
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        embeddings = embed_texts_batch(chunks)
        
        # Prepare metadata for each chunk
        metadata_list = []
        for i, chunk in enumerate(chunks):
            metadata_list.append({
                "user_id": user_id,
                "session_id": session_id,
                "filename": filename,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "text": chunk
            })
        
        # Insert into Milvus
        logger.info(f"Inserting {len(embeddings)} vectors into Milvus...")
        vectors_inserted = await insert_knowledge_chunks(
            user_id=user_id,
            session_id=session_id,
            embeddings=embeddings,
            chunks=chunks,
            metadata_list=metadata_list
        )
        
        # Track upload in database
        save_knowledge_upload(
            user_id=user_id,
            session_id=session_id,
            filename=filename,
            chunks_created=len(chunks),
            vectors_inserted=vectors_inserted
        )
        
        logger.info(f"Successfully processed {filename}: {len(chunks)} chunks, {vectors_inserted} vectors inserted")
        
        return {
            "filename": filename,
            "chunks_created": len(chunks),
            "vectors_inserted": vectors_inserted,
            "text_length": len(text)
        }
        
    except Exception as e:
        logger.error(f"Error processing PDF upload: {str(e)}")
        raise


def clean_text(text: str) -> str:
    """
    Clean and normalize text.
    
    Args:
        text: Raw text
        
    Returns:
        Cleaned text
    """
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Remove special characters that might cause issues
    # Keep basic punctuation
    
    return text.strip()