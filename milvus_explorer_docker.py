#!/usr/bin/env python3
"""
Milvus Database Explorer (Docker Version)
Shows current storage, tables, fields, and datasets in Uhakiki-AI system.
Connects to Docker-based Milvus instance.
"""

import os
import sys
import logging
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from pymilvus import connections, utility, Collection

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Docker Milvus configuration
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
COLLECTION_NAME = "student_records"

def connect_to_docker_milvus():
    """Connect to Docker-based Milvus"""
    try:
        connections.connect(
            alias="default",
            host=MILVUS_HOST,
            port=MILVUS_PORT
        )
        print("✅ Connected to Docker Milvus successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Docker Milvus: {e}")
        return False

def explore_milvus():
    """Explore Milvus database contents"""
    print("=" * 60)
    print("🔍 UHAKIKI-AI MILVUS DATABASE EXPLORER (DOCKER)")
    print("=" * 60)
    
    try:
        # Connect to Docker Milvus
        print(f"\n📡 Connecting to Docker Milvus at {MILVUS_HOST}:{MILVUS_PORT}...")
        if not connect_to_docker_milvus():
            print("\n💡 Make sure Docker containers are running:")
            print("   cd /home/cb-fx/uhakiki-ai/frontend/infra")
            print("   docker-compose up -d milvus etcd minio")
            return
        
        # List all collections
        print("\n📚 Available Collections:")
        collections = utility.list_collections()
        if not collections:
            print("   No collections found")
        else:
            for i, collection_name in enumerate(collections, 1):
                print(f"   {i}. {collection_name}")
        
        # Focus on main collection if it exists
        target_collection = COLLECTION_NAME
        if collections and target_collection not in collections:
            target_collection = collections[0]  # Use first available collection
        
        if target_collection in collections:
            print(f"\n🎯 Detailed View: '{target_collection}' Collection")
            print("-" * 50)
            
            collection = Collection(target_collection)
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
                if hasattr(field, 'dim'):
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
                
                # Show all fields found
                print(f"\n🏷️  All Fields Found:")
                try:
                    results = collection.query(
                        expr="pk >= 0",
                        output_fields=["*"],
                        limit=10
                    )
                    
                    all_fields = set()
                    for record in results:
                        all_fields.update(record.keys())
                    
                    for field in sorted(all_fields):
                        print(f"   • {field}")
                        
                except Exception as e:
                    print(f"   Error analyzing fields: {e}")
                
                # Data type analysis
                print(f"\n📊 Data Analysis:")
                try:
                    results = collection.query(
                        expr="pk >= 0",
                        output_fields=["*"],
                        limit=min(100, collection.num_entities)
                    )
                    
                    # Analyze field patterns
                    field_patterns = {}
                    for record in results:
                        for key, value in record.items():
                            if key not in field_patterns:
                                field_patterns[key] = set()
                            field_patterns[key].add(type(value).__name__)
                    
                    for field, types in field_patterns.items():
                        if len(types) > 1:
                            print(f"   • {field}: Mixed types ({', '.join(types)})")
                        else:
                            print(f"   • {field}: {list(types)[0]}")
                        
                except Exception as e:
                    print(f"   Error analyzing data types: {e}")
            
            else:
                print(f"\n📋 Collection is empty (0 entities)")
        
        else:
            print(f"\n❌ No collections found in database")
        
        # Connection info
        print(f"\n🔌 Connection Info:")
        print(f"   • Host: {MILVUS_HOST}")
        print(f"   • Port: {MILVUS_PORT}")
        print(f"   • Status: Connected")
        
    except Exception as e:
        print(f"\n❌ Error exploring Milvus: {e}")
        logger.exception("Full error details:")
    
    print("\n" + "=" * 60)
    print("🏁 EXPLORATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    explore_milvus()
