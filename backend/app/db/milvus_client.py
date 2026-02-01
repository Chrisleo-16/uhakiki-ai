from langchain_milvus import Milvus
from langchain_huggingface import HuggingFaceEmbeddings
import os
import time

# 1. Initialize the Neural "Translator" (Embeddings)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 2. Configure the Vault Connection
# Standard Docker service name; fallback to localhost if running outside container
MILVUS_URI = os.getenv("MILVUS_URI", "http://127.0.0.1:19530")

def store_in_vault(shards, collection_name="student_records"):
    """
    Takes neural shards and commits them to the National Identity Vault.
    """
    if not shards:
        print("[VAULT] No shards to store.")
        return None

    # Extract text and metadata
    texts = [s['content'] for s in shards]
    metadatas = [s['metadata'] for s in shards]
    
    print(f"[VAULT] Embedding {len(texts)} shards into vector space...")

    # PREPARE CONNECTION: Strip http:// for address-based connection args
    connection_host = MILVUS_URI.replace("http://", "").replace("/", "")
    
    try:
        # This creates the collection and builds the HNSW index automatically
        vector_db = Milvus.from_texts(
            texts=texts,
            embedding=embeddings,
            metadatas=metadatas,
            collection_name=collection_name,
            connection_args={"address": MILVUS_URI.replace("http://", "").replace("/", "")},
            index_params={
                "metric_type": "L2", 
                "index_type": "HNSW", 
                "params": {"M": 8, "efConstruction": 64}
            },
            drop_old=False # Important: Set to True ONLY if you want to wipe the vault on every run
        )
        print(f"[SUCCESS] {len(texts)} shards secured in the Sovereign Vault.")
        return vector_db
        
    except Exception as e:
        print(f"[CRITICAL ERROR] Vault connection failed at {connection_host}: {e}")
        
        # Fallback for local development (if Docker DNS is acting up)
        if "infra-milvus-1" in connection_host:
            print("[RETRY] Connection to Docker service failed. Falling back to localhost...")
            try:
                return Milvus.from_texts(
                    texts=texts,
                    embedding=embeddings,
                    metadatas=metadatas,
                    collection_name=collection_name,
                    connection_args={"address": "127.0.0.1:19530"},
                    index_params={"metric_type": "L2", "index_type": "HNSW", "params": {"M": 8, "efConstruction": 64}}
                )
            except Exception as e_inner:
                print(f"[FATAL] Localhost fallback also failed: {e_inner}")
        raise e