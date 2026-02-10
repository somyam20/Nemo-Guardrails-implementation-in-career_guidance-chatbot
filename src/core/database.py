
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import Optional, Dict, Any, Generator, List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "5432")


def get_conn():
    """Create a database connection"""
    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT]):
        raise RuntimeError(
            "Database configuration incomplete. Please set DB_HOST, DB_NAME, "
            "DB_USER, DB_PASSWORD, and DB_PORT in your .env file"
        )

    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )


# def init_db():
#     """Initialize database tables for career guidance chatbot"""
#     conn = get_conn()
#     cur = conn.cursor()
    
#     try:
#         # Create user_profiles table
#         cur.execute(
#             """
#             CREATE TABLE IF NOT EXISTS user_profiles (
#                 id SERIAL PRIMARY KEY,
#                 user_id VARCHAR(255) UNIQUE NOT NULL,
#                 answers JSONB NOT NULL,
#                 created_at TIMESTAMP DEFAULT now(),
#                 updated_at TIMESTAMP DEFAULT now()
#             )
#             """
#         )
        
#         # Create index on user_id for faster lookups
#         cur.execute(
#             """
#             CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id 
#             ON user_profiles(user_id)
#             """
#         )
        
#         # Create conversation_history table with session_id
#         cur.execute(
#             """
#             CREATE TABLE IF NOT EXISTS conversation_history (
#                 id SERIAL PRIMARY KEY,
#                 user_id VARCHAR(255) NOT NULL,
#                 session_id VARCHAR(255) NOT NULL,
#                 question TEXT NOT NULL,
#                 answer TEXT NOT NULL,
#                 created_at TIMESTAMP DEFAULT now()
#             )
#             """
#         )
        
#         # Create indexes for conversation history
#         cur.execute(
#             """
#             CREATE INDEX IF NOT EXISTS idx_conversation_history_user_session 
#             ON conversation_history(user_id, session_id)
#             """
#         )
        
#         cur.execute(
#             """
#             CREATE INDEX IF NOT EXISTS idx_conversation_history_user_id 
#             ON conversation_history(user_id)
#             """
#         )
        
#         # Create career_recommendations table with session_id
#         cur.execute(
#             """
#             CREATE TABLE IF NOT EXISTS career_recommendations (
#                 id SERIAL PRIMARY KEY,
#                 user_id VARCHAR(255) NOT NULL,
#                 session_id VARCHAR(255) NOT NULL,
#                 recommendation TEXT NOT NULL,
#                 metadata JSONB,
#                 created_at TIMESTAMP DEFAULT now()
#             )
#             """
#         )
        
#         # Create indexes for recommendations
#         cur.execute(
#             """
#             CREATE INDEX IF NOT EXISTS idx_career_recommendations_user_session 
#             ON career_recommendations(user_id, session_id)
#             """
#         )
        
#         cur.execute(
#             """
#             CREATE INDEX IF NOT EXISTS idx_career_recommendations_user_id 
#             ON career_recommendations(user_id)
#             """
#         )
        
#         # Create knowledge_uploads table to track PDF uploads
#         cur.execute(
#             """
#             CREATE TABLE IF NOT EXISTS knowledge_uploads (
#                 id SERIAL PRIMARY KEY,
#                 user_id VARCHAR(255) NOT NULL,
#                 session_id VARCHAR(255) NOT NULL,
#                 filename VARCHAR(500) NOT NULL,
#                 chunks_created INTEGER DEFAULT 0,
#                 vectors_inserted INTEGER DEFAULT 0,
#                 uploaded_at TIMESTAMP DEFAULT now()
#             )
#             """
#         )
        
#         cur.execute(
#             """
#             CREATE INDEX IF NOT EXISTS idx_knowledge_uploads_user_session 
#             ON knowledge_uploads(user_id, session_id)
#             """
#         )
        
#         conn.commit()
#         print("✓ Database tables created successfully")
        
#     except Exception as e:
#         conn.rollback()
#         print(f"✗ Error creating tables: {e}")
#         raise
#     finally:
#         cur.close()
#         conn.close()
def init_db():
    """Hard reset and initialize database tables for career guidance chatbot"""
    conn = get_conn()
    cur = conn.cursor()

    try:
        # --------------------------------
        # DROP EXISTING TABLES (HARD RESET)
        # --------------------------------
        cur.execute("""
            DROP TABLE IF EXISTS knowledge_uploads;
            DROP TABLE IF EXISTS career_recommendations;
            DROP TABLE IF EXISTS conversation_history;
            DROP TABLE IF EXISTS user_profiles;
        """)

        # --------------------------------
        # USER PROFILES
        # --------------------------------
        cur.execute("""
            CREATE TABLE user_profiles (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) UNIQUE NOT NULL,
                answers JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT now(),
                updated_at TIMESTAMP DEFAULT now()
            );
        """)

        cur.execute("""
            CREATE INDEX idx_user_profiles_user_id 
            ON user_profiles(user_id);
        """)

        # --------------------------------
        # CONVERSATION HISTORY
        # --------------------------------
        cur.execute("""
            CREATE TABLE conversation_history (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                session_id VARCHAR(255) NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT now()
            );
        """)

        cur.execute("""
            CREATE INDEX idx_conversation_history_user_session
            ON conversation_history(user_id, session_id);
        """)

        cur.execute("""
            CREATE INDEX idx_conversation_history_user_id
            ON conversation_history(user_id);
        """)

        # --------------------------------
        # CAREER RECOMMENDATIONS
        # --------------------------------
        cur.execute("""
            CREATE TABLE career_recommendations (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                session_id VARCHAR(255) NOT NULL,
                recommendation TEXT NOT NULL,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT now()
            );
        """)

        cur.execute("""
            CREATE INDEX idx_career_recommendations_user_session
            ON career_recommendations(user_id, session_id);
        """)

        cur.execute("""
            CREATE INDEX idx_career_recommendations_user_id
            ON career_recommendations(user_id);
        """)

        # --------------------------------
        # KNOWLEDGE UPLOADS
        # --------------------------------
        cur.execute("""
            CREATE TABLE knowledge_uploads (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                session_id VARCHAR(255) NOT NULL,
                filename VARCHAR(500) NOT NULL,
                chunks_created INTEGER DEFAULT 0,
                vectors_inserted INTEGER DEFAULT 0,
                uploaded_at TIMESTAMP DEFAULT now()
            );
        """)

        cur.execute("""
            CREATE INDEX idx_knowledge_uploads_user_session
            ON knowledge_uploads(user_id, session_id);
        """)

        conn.commit()
        print("✓ Database tables dropped and recreated successfully")

    except Exception as e:
        conn.rollback()
        print(f"✗ Error creating tables: {e}")
        raise

    finally:
        cur.close()
        conn.close()



def get_db() -> Generator:
    """
    Database connection generator for dependency injection.
    
    Yields:
        psycopg2 connection object
    """
    conn = get_conn()
    try:
        yield conn
    finally:
        conn.close()


# -------------------------
# USER PROFILE OPERATIONS
# -------------------------

def create_user_profile(user_id: str, answers: Dict[str, Any]) -> bool:
    """Create or update user profile"""
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        cur.execute(
            """
            INSERT INTO user_profiles (user_id, answers, created_at, updated_at)
            VALUES (%s, %s, now(), now())
            ON CONFLICT (user_id) 
            DO UPDATE SET answers = EXCLUDED.answers, updated_at = now()
            """,
            (user_id, psycopg2.extras.Json(answers))
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error creating user profile: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user profile by user_id"""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        cur.execute(
            "SELECT * FROM user_profiles WHERE user_id = %s",
            (user_id,)
        )
        result = cur.fetchone()
        return dict(result) if result else None
    finally:
        cur.close()
        conn.close()


# -------------------------
# CONVERSATION HISTORY OPERATIONS (with session_id)
# -------------------------

def save_conversation(user_id: str, session_id: str, question: str, answer: str) -> bool:
    """Save conversation to history with session_id"""
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        cur.execute(
            """
            INSERT INTO conversation_history (user_id, session_id, question, answer, created_at)
            VALUES (%s, %s, %s, %s, now())
            """,
            (user_id, session_id, question, answer)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error saving conversation: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def get_conversation_history(user_id: str, session_id: str, limit: int = 10) -> List[Dict]:
    """Get conversation history for a user session"""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        cur.execute(
            """
            SELECT * FROM conversation_history 
            WHERE user_id = %s AND session_id = %s
            ORDER BY created_at DESC 
            LIMIT %s
            """,
            (user_id, session_id, limit)
        )
        results = cur.fetchall()
        return [dict(row) for row in results]
    finally:
        cur.close()
        conn.close()


def get_all_user_conversations(user_id: str, limit: int = 50) -> List[Dict]:
    """Get all conversation history for a user across all sessions"""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        cur.execute(
            """
            SELECT * FROM conversation_history 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT %s
            """,
            (user_id, limit)
        )
        results = cur.fetchall()
        return [dict(row) for row in results]
    finally:
        cur.close()
        conn.close()


# -------------------------
# CAREER RECOMMENDATION OPERATIONS (with session_id)
# -------------------------

def save_career_recommendation(
    user_id: str,
    session_id: str,
    recommendation: str, 
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """Save career recommendation with session_id"""
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        cur.execute(
            """
            INSERT INTO career_recommendations (user_id, session_id, recommendation, metadata, created_at)
            VALUES (%s, %s, %s, %s, now())
            """,
            (user_id, session_id, recommendation, psycopg2.extras.Json(metadata) if metadata else None)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error saving career recommendation: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def get_career_recommendations(user_id: str, session_id: str, limit: int = 5) -> List[Dict]:
    """Get career recommendations for a user session"""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        cur.execute(
            """
            SELECT * FROM career_recommendations 
            WHERE user_id = %s AND session_id = %s
            ORDER BY created_at DESC 
            LIMIT %s
            """,
            (user_id, session_id, limit)
        )
        results = cur.fetchall()
        return [dict(row) for row in results]
    finally:
        cur.close()
        conn.close()


def get_all_user_recommendations(user_id: str, limit: int = 20) -> List[Dict]:
    """Get all career recommendations for a user across all sessions"""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        cur.execute(
            """
            SELECT * FROM career_recommendations 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT %s
            """,
            (user_id, limit)
        )
        results = cur.fetchall()
        return [dict(row) for row in results]
    finally:
        cur.close()
        conn.close()


# -------------------------
# KNOWLEDGE UPLOAD TRACKING
# -------------------------

def save_knowledge_upload(
    user_id: str,
    session_id: str,
    filename: str,
    chunks_created: int,
    vectors_inserted: int
) -> bool:
    """Track PDF knowledge upload"""
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        cur.execute(
            """
            INSERT INTO knowledge_uploads 
            (user_id, session_id, filename, chunks_created, vectors_inserted, uploaded_at)
            VALUES (%s, %s, %s, %s, %s, now())
            """,
            (user_id, session_id, filename, chunks_created, vectors_inserted)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error saving knowledge upload: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def get_knowledge_uploads(user_id: str, session_id: str) -> List[Dict]:
    """Get all knowledge uploads for a user session"""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        cur.execute(
            """
            SELECT * FROM knowledge_uploads 
            WHERE user_id = %s AND session_id = %s
            ORDER BY uploaded_at DESC
            """,
            (user_id, session_id)
        )
        results = cur.fetchall()
        return [dict(row) for row in results]
    finally:
        cur.close()
        conn.close()


# Legacy class-based interface for compatibility with existing code
class ConversationHistory:
    """Legacy class for conversation history (for compatibility)"""
    
    @staticmethod
    def create(user_id: str, session_id: str, question: str, answer: str):
        return save_conversation(user_id, session_id, question, answer)
    
    @staticmethod
    def get_history(user_id: str, session_id: str, limit: int = 10):
        return get_conversation_history(user_id, session_id, limit)


class CareerRecommendation:
    """Legacy class for career recommendations (for compatibility)"""
    
    @staticmethod
    def create(user_id: str, session_id: str, recommendation: str, metadata: Optional[Dict] = None):
        return save_career_recommendation(user_id, session_id, recommendation, metadata)
    
    @staticmethod
    def get_recommendations(user_id: str, session_id: str, limit: int = 5):
        return get_career_recommendations(user_id, session_id, limit)


class UserProfile:
    """Legacy class for user profiles (for compatibility)"""
    
    @staticmethod
    def create(user_id: str, answers: Dict[str, Any]):
        return create_user_profile(user_id, answers)
    
    @staticmethod
    def get(user_id: str):
        return get_user_profile(user_id)