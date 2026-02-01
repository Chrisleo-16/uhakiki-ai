# Identity sharding routes
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.neural.sharding import sharder
# from app.db.milvus_client import milvus_client # Uncomment when DB is ready
from app.db.milvus_client import store_in_vault

router = APIRouter()

class StudentRecord(BaseModel):
    national_id: str
    full_text: str # The raw text from HELB/KNEC documents

@router.post("/ingest")
async def ingest_identity(record: StudentRecord):
    try:
        # 1. Shard the data (Already built)
        shards = sharder.process_document(record.full_text, record.national_id)
        
        # 2. COMMIT TO THE VAULT (New Step!)
        store_in_vault(shards)

        return {
            "status": "NATIONAL_RECORD_SECURED",
            "shards_vaulted": len(shards),
            "latency_tier": "Sub-100ms",
            "location": "Local Sovereign Vault"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))