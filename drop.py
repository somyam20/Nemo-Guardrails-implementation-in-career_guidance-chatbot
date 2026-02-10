"""
Script to drop the existing Milvus collection with wrong dimensions.
Run this before running populate_milvus.py again.
"""
from pymilvus import connections, utility
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    # Connect to Milvus
    print("Connecting to Milvus...")
    connections.connect(
        alias="default",
        uri=os.getenv("MILVUS_URI"),
        token=os.getenv("MILVUS_API_KEY")
    )
    print("✓ Connected successfully")
    
    collection_name = "career_vectors"
    
    # Check if collection exists
    if utility.has_collection(collection_name):
        print(f"\nFound collection: '{collection_name}'")
        
        # Get collection info
        from pymilvus import Collection
        collection = Collection(collection_name)
        print(f"Current entities: {collection.num_entities}")
        
        # Drop the collection
        print(f"\nDropping collection '{collection_name}'...")
        utility.drop_collection(collection_name)
        print("✓ Collection dropped successfully!")
        print("\nYou can now run populate_milvus.py to create a new collection with correct dimensions (768)")
    else:
        print(f"\nCollection '{collection_name}' does not exist.")
        print("You can proceed directly to run populate_milvus.py")
        
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()