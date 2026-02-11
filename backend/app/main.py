import os
import uuid
import datetime
from typing import Optional, List

from fastapi import *
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.logic.liveness_detector import verify_liveness
from app.logic.forgery_detector import detect_pixel_anomalies
from app.logic.qr_system import generate_student_qr
# from app.logic.qr_system import generate_dynamic_qr
from app.logic.council import SecurityCouncil
from app.logic.xai import generate_audit_report

# 1. PRE-START: Ensure infrastructure is ready
if not os.path.exists("static"):
    os.makedirs("static")

# 2. IMPORTS: Clean and unique
from app.api.v1 import secure_ingest 
from app.db.milvus_client import store_in_vault, search_vault

app = FastAPI(
    title="Uhakiki-AI: Sovereign Identity Engine",
    description="Agentic Fraud Detection System backed by Milvus & Neural Embeddings.",
    version="Phase-2.0"
)
council = SecurityCouncil()
# 3. MOUNTING
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(secure_ingest.router, prefix="/api/v1")

# --- DATA MODELS ---
class IdentityRecord(BaseModel):
    national_id: str
    full_name: str
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
    return RedirectResponse(url="/docs")

@app.get("/api/v1/health")
def health_check():
    return {"status": "ONLINE", "phase": "2 - Agentic Intelligence"}

@app.post("/api/v1/ingest", response_model=IngestResponse)
async def ingest_identity(record: IdentityRecord):
    # 1. SEARCH
    search_query_text = f"{record.full_name} {record.biometric_text}"
    existing_matches = search_vault(search_query_text, limit=1)

    # 2. JUDGE
    risk_score = 1.0 
    is_fraudulent = False
    nearest_match_id = None

    if existing_matches:
        # Check if the result is a tuple (doc, distance) or an object
        best_match_doc, distance = existing_matches[0]
        risk_score = float(distance)
        if risk_score < 0.4:
            is_fraudulent = True
            nearest_match_id = getattr(best_match_doc, 'metadata', {}).get("national_id", "Unknown")

    # 3. ACT
    tracking_id = str(uuid.uuid4())
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

    # CRITICAL: Ensure store_in_vault can handle this dictionary
    success = store_in_vault([new_shard])
    if not success:
        raise HTTPException(status_code=500, detail="Vault Storage Failed - Check Milvus Connection")

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
@app.post("/verify-student")
async def verify_student(
    national_id: str = Form(...), 
    id_card: UploadFile = File(...),
    liveness_video: UploadFile = File(...)
):
    # 1. RUN FORENSICS (The 'Observe' Phase)
    forgery_data = await detect_pixel_anomalies(id_card)
    liveness_data = await verify_liveness(liveness_video)
    
    # 2. COUNCIL DECISION (The 'Decide' Phase)
    council_result = await council.run_security_audit(national_id, forgery_data, liveness_data)
    
    # 3. GENERATE AUDIT LOG (The 'Accountability' Phase)
    audit_report = generate_audit_report(
        national_id, 
        forgery_data, 
        liveness_data, 
        council_result['reasoning']
    )
    
    # 4. FINAL ACT
    return {
        "status": "PROCESSED",
        "verdict": "APPROVED" if council_result['approved'] else "FLAGGED",
        "explanation": audit_report['human_readable_explanation'],
        "tracking_id": audit_report['metadata']['student_id']
    }

@app.post("/api/v1/verify/liveness")
async def liveness_endpoint(video: UploadFile = File(...)):
    # Real-time Blink Detection using EAR math
    return await verify_liveness(video)

@app.post("/api/v1/verify/document")
async def document_endpoint(document: UploadFile = File(...)):
    # Real Math: Pixel-by-Pixel Error Level Analysis
    return await detect_pixel_anomalies(document)

@app.get("/api/v1/identity/qr/{student_id}")
async def get_qr(student_id: str):
    # Generates a Sovereign QR with SHA-256 Identity Hash
    return generate_student_qr(student_id)