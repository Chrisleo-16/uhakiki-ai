#!/usr/bin/env python3
"""
Milvus Database Explorer
Shows current storage, tables, fields, and datasets in the Uhakiki-AI system.
"""

import os
import sys
import logging
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from pymilvus import connections, utility, Collection
from app.db.milvus_client import _connect, COLLECTION_NAME, get_collection

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def explore_milvus():
    """Explore Milvus database contents"""
    print("=" * 60)
    print("🔍 UHAKIKI-AI MILVUS DATABASE EXPLORER")
    print("=" * 60)
    
    try:
        # Connect to Milvus
        print("\n📡 Connecting to Milvus...")
        _connect()
        print("✅ Connected successfully")
        
        # List all collections
        print("\n📚 Available Collections:")
        collections = utility.list_collections()
        if not collections:
            print("   No collections found")
        else:
            for i, collection_name in enumerate(collections, 1):
                print(f"   {i}. {collection_name}")
        
        # Focus on the main collection
        if COLLECTION_NAME in collections:
            print(f"\n🎯 Detailed View: '{COLLECTION_NAME}' Collection")
            print("-" * 50)
            
            collection = Collection(COLLECTION_NAME)
            collection.load()
            
            # Basic info
            print(f"📊 Collection Info:")
            print(f"   • Name: {collection.name}")
            print(f"   • Description: {collection.description}")
            print(f"   • Number of entities: {collection.num_entities}")
            
            # Schema details
            print(f"\n🏗️  Schema Fields:")
            schema = collection.schema
            for field in schema.fields:
                field_type = "PRIMARY KEY" if field.is_primary else ""
                field_type += " AUTO_ID" if field.auto_id else ""
                if field.dtype.name == 'FLOAT_VECTOR':
                    field_type += f" (dim={field.dim})"
                print(f"   • {field.name}: {field.dtype.name} {field_type}")
            
            # Index info
            print(f"\n🔍 Index Information:")
            indexes = collection.indexes
            for index in indexes:
                print(f"   • Field: {index.field_name}")
                print(f"     Type: {index.index_type}")
                print(f"     Metric: {index.metric_type}")
                print(f"     Params: {index.params}")
            
            # Sample data exploration
            if collection.num_entities > 0:
                print(f"\n📋 Sample Data (First 5 records):")
                try:
                    # Query first 5 records
                    results = collection.query(
                        expr="pk >= 0",
                        output_fields=["*"],
                        limit=5
                    )
                    
                    for i, record in enumerate(results, 1):
                        print(f"\n   Record {i}:")
                        for key, value in record.items():
                            if key == 'vector':
                                print(f"     • {key}: [{len(value)}D vector] (first 3: {value[:3]}...)")
                            elif key == 'pk':
                                print(f"     • {key}: {value}")
                            else:
                                print(f"     • {key}: {value}")
                
                except Exception as e:
                    print(f"   Error querying sample data: {e}")
                
                # Show dynamic fields (metadata)
                print(f"\n🏷️  Dynamic Fields (Metadata) Found:")
                try:
                    results = collection.query(
                        expr="pk >= 0",
                        output_fields=["*"],
                        limit=10
                    )
                    
                    all_fields = set()
                    for record in results:
                        all_fields.update(record.keys())
                    
                    # Exclude standard fields
                    standard_fields = {'pk', 'text', 'vector'}
                    dynamic_fields = all_fields - standard_fields
                    
                    if dynamic_fields:
                        for field in sorted(dynamic_fields):
                            print(f"   • {field}")
                    else:
                        print("   No dynamic fields found")
                        
                except Exception as e:
                    print(f"   Error analyzing dynamic fields: {e}")
            
            # Search statistics
            print(f"\n🔎 Search Statistics:")
            try:
                from app.db.milvus_client import search_vault
                
                # Test searches
                searches = [
                    ("user registration", "User registrations"),
                    ("verification", "Verification records"),
                    ("face_encoding", "Face encodings"),
                    ("student", "Student records")
                ]
                
                for query, description in searches:
                    results = search_vault(query, limit=10)
                    print(f"   • {description}: {len(results)} results")
                    
            except Exception as e:
                print(f"   Error performing test searches: {e}")
        
        else:
            print(f"\n❌ Collection '{COLLECTION_NAME}' not found")
        
        # Database file info
        db_file = "./sovereign_vault.db"
        if os.path.exists(db_file):
            file_size = os.path.getsize(db_file)
            modified_time = datetime.fromtimestamp(os.path.getmtime(db_file))
            print(f"\n💾 Database File Info:")
            print(f"   • Path: {db_file}")
            print(f"   • Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
            print(f"   • Last Modified: {modified_time}")
        
    except Exception as e:
        print(f"\n❌ Error exploring Milvus: {e}")
        logger.exception("Full error details:")
    
    print("\n" + "=" * 60)
    print("🏁 EXPLORATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    explore_milvus()
