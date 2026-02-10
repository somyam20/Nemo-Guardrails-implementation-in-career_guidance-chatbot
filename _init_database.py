
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.database import init_db, get_conn


def test_connection():
    """Test database connection"""
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        print("✓ Database connection successful")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {str(e)}")
        print("\nPlease check your .env file contains:")
        print("  DB_HOST=your-supabase-host")
        print("  DB_NAME=postgres")
        print("  DB_USER=postgres")
        print("  DB_PASSWORD=your-password")
        print("  DB_PORT=5432")
        return False


def create_tables():
    """Create all database tables"""
    try:
        print("Creating database tables...")
        init_db()
        print("✓ Database tables created successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to create tables: {str(e)}")
        return False


def verify_tables():
    """Verify that tables were created"""
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        # Check for tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
        """)
        
        tables = [row[0] for row in cur.fetchall()]
        
        expected_tables = [
            'user_profiles',
            'conversation_history',
            'career_recommendations',
            'knowledge_uploads'
        ]
        
        print(f"\nFound tables: {tables}")
        
        all_exist = True
        for table in expected_tables:
            if table in tables:
                print(f"✓ Table '{table}' exists")
            else:
                print(f"✗ Table '{table}' not found")
                all_exist = False
        
        cur.close()
        conn.close()
        
        return all_exist
        
    except Exception as e:
        print(f"Error verifying tables: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Career Guidance Chatbot - Database Initialization")
    print("=" * 60)
    print()
    
    # Test connection
    if not test_connection():
        print("\n❌ Cannot proceed without database connection")
        sys.exit(1)
    
    print()
    
    # Create tables
    if not create_tables():
        print("\n❌ Failed to create tables")
        sys.exit(1)
    
    print()
    
    # Verify tables
    if verify_tables():
        print("\n" + "=" * 60)
        print("✅ Database initialization completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Test the /user/questions endpoint to get questions")
        print("2. Submit user answers via /user/profile")
        print("3. Upload PDF knowledge base via /user/upload-knowledge")
        print("4. Start chatting via /chat/query")
    else:
        print("\n" + "=" * 60)
        print("⚠️  Some tables may not have been created properly")
        print("=" * 60)
        sys.exit(1)