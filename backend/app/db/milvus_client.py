from langchain_milvus import Milvus
from langchain_huggingface import HuggingFaceEmbeddings
import os
import time

# --- CONFIGURATION ---
# 1. Initialize the Neural "Translator" (Embeddings)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 2. Configure the Vault Connection
# Standard Docker service name; fallback to localhost if running outside container
MILVUS_URI = os.getenv("MILVUS_URI", "./sovereign_vault.db")
COLLECTION_NAME = "student_records"  # Moved global so both functions can see it


def store_in_vault(shards):
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

    try:
        # This creates the collection and builds the HNSW index automatically
        vector_db = Milvus.from_texts(
            texts=texts,
            embedding=embeddings,
            metadatas=metadatas,
            collection_name=COLLECTION_NAME,
            # Fixed: Use 'uri' directly, don't strip http
            connection_args={"uri": MILVUS_URI},
            index_params={
                "metric_type": "L2",
                "index_type": "FLAT",
                "params": {"M": 8, "efConstruction": 64}
            },
            drop_old=False
        )
        print(f"[SUCCESS] {len(texts)} shards secured in the Sovereign Vault.")
        return vector_db

    except Exception as e:
        print(f"[CRITICAL ERROR] Vault connection failed at {MILVUS_URI}: {e}")

        # Fallback for local development (if Docker DNS is acting up)
        if "milvus" in MILVUS_URI:
            print(
                "[RETRY] Connection to Docker service failed. Falling back to localhost...")
            try:
                return Milvus.from_texts(
                    texts=texts,
                    embedding=embeddings,
                    metadatas=metadatas,
                    collection_name=COLLECTION_NAME,
                    connection_args={"uri": "http://127.0.0.1:19530"},
                    index_params={"metric_type": "L2", "index_type": "HNSW", "params": {
                        "M": 8, "efConstruction": 64}}
                )
            except Exception as e_inner:
                print(f"[FATAL] Localhost fallback also failed: {e_inner}")
        raise e


def search_vault(query_text: str, limit: int = 3):
    """
    Recall Phase: The 'Memory' of the Agent.
    """
    try:
        print(f"🔍 Agent is scanning the vault for: '{query_text[:30]}...'")

        # Connect to the existing vault
        vector_db = Milvus(
            embedding_function=embeddings,
            connection_args={"uri": MILVUS_URI},
            collection_name=COLLECTION_NAME
        )

        # Perform the Semantic Search
        results = vector_db.similarity_search_with_score(query_text, k=limit)

        print(f" Scan complete. Found {len(results)} potential matches.")
        return results

    except Exception as e:
        print(f" Memory Recall Error: {e}")
        return []
