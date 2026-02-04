"""
UHAKIKIAI NEURAL ENGINE (API GATEWAY)
-------------------------------------
The central nervous system of the application. 
It receives data, consults the Milvus Vault, and makes Agentic decisions on fraud.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
import datetime
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

# 1. Import the New Modular Router
from app.api.v1 import secure_ingest 
import os
# Import Vault Logic
from app.db.milvus_client import store_in_vault, search_vault
from pydantic import BaseModel
from typing import Optional, List


# Import our Vault Logic
from app.db.milvus_client import store_in_vault, search_vault

app = FastAPI(
    title="Uhakiki-AI: Sovereign Identity Engine",
    description="Agentic Fraud Detection System backed by Milvus & Neural Embeddings.",
    version="Phase-2.0"
)
if not os.path.exists("static"):
    os.makedirs("static")

# 2. MOUNT THE STATIC FOLDER
# This makes http://127.0.0.1:8000/static/filename.png work
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(secure_ingest.router, prefix="/api/v1")
# --- DATA MODELS ---


class IdentityRecord(BaseModel):
    national_id: str
    full_name: str
    # A description of the person (e.g., "Male, 30s, scar on left cheek...")
    biometric_text: str
    metadata: Optional[dict] = {}


class IngestResponse(BaseModel):
    status: str
    tracking_id: str
    fraud_check: dict
    timestamp: str

# --- ROUTES ---
@app.get("/")
async def root():
    """Redirects the 404 'front door' to the interactive API docs."""
    return RedirectResponse(url="/docs")

@app.get("/api/v1/health")
def health_check():
    """Confirms the Neural Engine is alive."""
    return {"status": "ONLINE", "phase": "2 - Agentic Intelligence"}


@app.post("/api/v1/ingest", response_model=IngestResponse)
async def ingest_identity(record: IdentityRecord):
    """
    The Core Agentic Workflow:
    1. RECEIVE data.
    2. THINK (Search Vault): "Have I seen this pattern before?"
    3. JUDGE (Fraud Score): Calculate risk based on vector distance.
    4. ACT (Store): Secure the record if it passes (or flag it).
    """

    # 1. SEARCH: Check the vault for existing "Neural Fingerprints"
    search_query_text = f"{record.full_name} {record.biometric_text}"
    existing_matches = search_vault(search_query_text, limit=1)

    # 2. JUDGE: Calculate Risk Score
    risk_score = 1.0  # Default to "Safe" (High distance)
    is_fraudulent = False
    nearest_match_id = None

    if existing_matches:
        best_match_doc, distance = existing_matches[0]
        risk_score = float(distance)

        # AGENTIC LOGIC:
        if risk_score < 0.4:
            is_fraudulent = True
            nearest_match_id = best_match_doc.metadata.get(
                "national_id", "Unknown")
            print(
                f"FRAUD ALERT: High similarity ({risk_score:.4f}) with ID {nearest_match_id}")

    # 3. ACT: Prepare the record for storage
    tracking_id = str(uuid.uuid4())

    # We package the content and metadata into a 'shard' dictionary
    # This prevents the "string indices must be integers" error
    new_shard = {
        "content": search_query_text,
        "metadata": {
            "national_id": record.national_id,
            "full_name": record.full_name,
            "timestamp": str(datetime.datetime.now()),
            "risk_score": risk_score,
            "fraud_flag": str(is_fraudulent)
        }
    }

    # Store the list of shards
    success = store_in_vault([new_shard])

    if not success:
        raise HTTPException(status_code=500, detail="Vault Storage Failed")

    # 4. RESPOND: Return the Agent's Findings
    return {
        "status": "SECURED" if not is_fraudulent else "FLAGGED_FOR_AUDIT",
        "tracking_id": tracking_id,
        "fraud_check": {
            "risk_score": round(risk_score, 4),
            "is_suspicious": is_fraudulent,
            "nearest_neighbor": nearest_match_id
        },
        "timestamp": str(datetime.datetime.now())
    }
