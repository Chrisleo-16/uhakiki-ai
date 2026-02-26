"""
Sovereign Identity Vault — Milvus Client

LangChain's Milvus.from_texts() has a confirmed bug with milvus-lite 2.5.x
where it fails to pass 'dim' during collection creation, causing:
    Assert "type_map.count("dim")" => dim not found (FieldMeta.cpp:90)

Solution: Use raw pymilvus to create the collection with an explicit full
schema (including dim=384). Then use LangChain ONLY for search queries.
Inserts are done via raw pymilvus insert() to avoid the bug entirely.
"""

import os
import logging
import numpy as np
from typing import Optional

from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility,
)
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MILVUS_URI = os.getenv("MILVUS_URI", os.path.join(_BASE_DIR, "sovereign_vault.db"))
COLLECTION_NAME = "student_records"
EMBEDDING_DIM   = 384  # all-MiniLM-L6-v2

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


# ── Connection ─────────────────────────────────────────────────────────────────

def _connect():
    """Connect to milvus-lite. Safe to call multiple times."""
    try:
        connections.connect("default", uri=MILVUS_URI)
    except Exception as e:
        if "already" not in str(e).lower():
            raise


def _disconnect():
    try:
        connections.disconnect("default")
    except Exception:
        pass


# ── Schema bootstrap ───────────────────────────────────────────────────────────

def _ensure_collection() -> Collection:
    """
    Create collection with explicit schema if it doesn't exist.
    Schema matches what LangChain expects: pk (auto int64), text (varchar), vector (float[384])
    Plus enable_dynamic_field=True so metadata fields are stored as JSON.
    """
    _connect()

    if utility.has_collection(COLLECTION_NAME):
        col = Collection(COLLECTION_NAME)
        col.load()
        return col

    logger.info(f"[VAULT] Creating collection '{COLLECTION_NAME}' dim={EMBEDDING_DIM}...")

    fields = [
        FieldSchema(name="pk",     dtype=DataType.INT64,        is_primary=True, auto_id=True),
        FieldSchema(name="text",   dtype=DataType.VARCHAR,       max_length=65535),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR,  dim=EMBEDDING_DIM),
    ]
    schema = CollectionSchema(
        fields=fields,
        description="Sovereign Identity Vault",
        enable_dynamic_field=True,   # stores metadata as dynamic JSON fields
    )

    col = Collection(name=COLLECTION_NAME, schema=schema)
    col.create_index(
        field_name="vector",
        index_params={"metric_type": "L2", "index_type": "FLAT", "params": {}},
    )
    col.load()
    logger.info("[VAULT] ✅ Collection created.")
    return col


# ── Write ──────────────────────────────────────────────────────────────────────

def store_in_vault(shards: list) -> bool:
    """
    Embed and store shards using raw pymilvus insert — bypasses LangChain bug.
    Each shard: { "content": str, "metadata": dict }
    """
    if not shards:
        logger.info("[VAULT] No shards to store.")
        return False

    try:
        col = _ensure_collection()

        texts     = [s["content"]  for s in shards]
        metadatas = [s["metadata"] for s in shards]

        logger.info(f"[VAULT] Embedding {len(texts)} shard(s)...")
        vectors = embeddings.embed_documents(texts)

        # Build rows — text + vector + all metadata fields (dynamic schema)
        rows = []
        for text, vector, meta in zip(texts, vectors, metadatas):
            row = {"text": text, "vector": vector}
            row.update(meta)   # metadata goes into dynamic fields
            rows.append(row)

        col.insert(rows)
        col.flush()

        logger.info(f"[VAULT] ✅ {len(rows)} shard(s) stored.")
        return True

    except Exception as e:
        logger.error(f"[VAULT] ❌ Storage failed: {e}")
        return False


# ── Read — semantic search ─────────────────────────────────────────────────────

def search_vault(query_text: str, limit: int = 10) -> list:
    """
    Semantic search. Returns list of (SimpleDoc, score) tuples
    where SimpleDoc has a .metadata dict — same interface as before.
    """
    try:
        col = _ensure_collection()

        query_vector = embeddings.embed_query(query_text)

        results = col.search(
            data=[query_vector],
            anns_field="vector",
            param={"metric_type": "L2", "params": {}},
            limit=limit,
            output_fields=["text", "*"],  # * fetches all dynamic fields
        )

        docs = []
        for hit in results[0]:
            entity = hit.entity

            # pymilvus 2.5.x: entity fields accessed via entity.fields (list of names)
            # entity.get(key) takes only 1 arg — no default value supported
            all_fields = entity.fields if hasattr(entity, "fields") else []
            metadata = {}
            for k in all_fields:
                if k in ("pk", "text", "vector"):
                    continue
                try:
                    metadata[k] = entity.get(k)
                except Exception:
                    pass

            doc = _SimpleDoc(
                page_content=entity.get("text") or "",
                metadata=metadata,
            )
            docs.append((doc, hit.distance))

        logger.info(f"[VAULT] '{query_text[:35]}' → {len(docs)} result(s).")
        return docs

    except Exception as e:
        logger.warning(f"[VAULT] Search failed: {e}")
        return []


class _SimpleDoc:
    """Minimal Document-like object so existing code using doc.metadata still works."""
    def __init__(self, page_content: str, metadata: dict):
        self.page_content = page_content
        self.metadata     = metadata


# ── Read — face encoding lookup ────────────────────────────────────────────────

def get_face_encoding(student_id: str) -> Optional[np.ndarray]:
    """
    Retrieve stored face encoding for a student.
    Returns np.ndarray or None. Pass plain student_id — no prefix needed.
    """
    try:
        results = search_vault(f"face_encoding_{student_id}", limit=20)

        for doc, score in results:
            meta = doc.metadata
            if (
                meta.get("student_id") == student_id
                and meta.get("type") == "face_encoding"
                and meta.get("encoding")
            ):
                logger.info(f"[VAULT] ✅ Encoding found for {student_id} (score={score:.3f})")
                return np.array(meta["encoding"])

        logger.warning(f"[VAULT] No encoding found for student: {student_id}")
        return None

    except Exception as e:
        logger.error(f"[VAULT] Encoding lookup failed: {e}")
        return None


# ── Read — verification history ────────────────────────────────────────────────

def get_verification_history(limit: int = 50) -> list:
    """
    Retrieve verification records for the frontend history page.
    Skips face_encoding records.
    """
    try:
        results = search_vault("identity verification result verdict", limit=limit)

        history = []
        for doc, _ in results:
            meta = doc.metadata

            if meta.get("type") == "face_encoding":
                continue
            if not meta.get("tracking_id"):
                continue

            history.append({
                "tracking_id":      meta.get("tracking_id"),
                "student_id":       meta.get("student_id", "Unknown"),
                "national_id":      meta.get("national_id", "Unknown"),
                "timestamp":        meta.get("timestamp"),
                "status":           "completed",
                "final_verdict":    meta.get("verdict", "PENDING"),
                "confidence_score": float(meta.get("confidence", 0.0)),
                "risk_score":       float(meta.get("risk_score", 0.0)),
                "processing_time":  float(meta.get("processing_time", 2.5)),
                "components": {
                    "document_analysis": {
                        "forgery_probability": float(meta.get("forgery_probability", 0.01)),
                        "judgment":            meta.get("document_judgment", "AUTHENTIC"),
                    },
                    "biometric_analysis": {
                        "overall_score": float(meta.get("biometric_score", 0.0)),
                        "verified":      bool(meta.get("face_verified", False)),
                    },
                    "aafi_decision": {
                        "verdict":    meta.get("verdict", "PENDING"),
                        "confidence": float(meta.get("confidence", 0.0)),
                    },
                },
            })

        logger.info(f"[VAULT] History: {len(history)} record(s).")
        return history

    except Exception as e:
        logger.error(f"[VAULT] get_verification_history failed: {e}")
        return []
def create_user_collection():
    _connect()

    if utility.has_collection(COLLECTION_NAME):
        return Collection(COLLECTION_NAME)

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="email", dtype=DataType.VARCHAR, max_length=255),
        FieldSchema(name="username", dtype=DataType.VARCHAR, max_length=100),
        FieldSchema(name="hashed_password", dtype=DataType.VARCHAR, max_length=255),
        # Dummy vector field (required by Milvus — use real embeddings if needed)
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=8),
    ]

    schema = CollectionSchema(fields, description="User collection")
    collection = Collection(COLLECTION_NAME, schema)

    # Create index on the vector field (required)
    collection.create_index("embedding", {
        "index_type": "FLAT",
        "metric_type": "L2",
        "params": {}
    })

    collection.load()
    return collection

def get_collection():
    _connect()
    collection = Collection(COLLECTION_NAME)
    collection.load()
    return collection