import os
import uuid
import datetime
from typing import Optional, List
import base64
import cv2
import numpy as np
from fastapi import *
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from app.logic.liveness_detector import MBICSystem
from app.logic.forgery_detector import detect_pixel_anomalies
from app.logic.qr_system import generate_student_qr
# from app.logic.qr_system import generate_dynamic_qr
from app.logic.council import SecurityCouncil
from app.logic.xai import generate_audit_report
from app.logic.face_extractor import face_extractor

# 1. PRE-START: Ensure infrastructure is ready
if not os.path.exists("static"):
    os.makedirs("static")

# 2. IMPORTS: Clean and unique
from app.api.v1 import secure_ingest 
from app.db.milvus_client import store_in_vault, search_vault

app = FastAPI(
    title="Uhakiki-AI: Sovereign Identity Engine",
    description="Agentic Fraud Detection System backed by Milvus & Neural Embeddings.",
    version="Phase-2.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Your Next.js URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
council = SecurityCouncil()
mbic_engine = MBICSystem() # Real-time engine

# 2. MOUNTING & ROUTERS
app.mount("/static", StaticFiles(directory="static"), name="static")
# If you have external router files, keep them here:
from app.api.v1 import secure_ingest, verification_pipeline, face_extraction, analytics, review, biometric, document
# from app.api.v1 import model_training  # Commented out for testing
app.include_router(secure_ingest.router, prefix="/api/v1")
app.include_router(verification_pipeline.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(review.router, prefix="/api/v1/review")
app.include_router(biometric.router, prefix="/api/v1/biometric")
app.include_router(document.router, prefix="/api/v1/document")
# app.include_router(model_training.router, prefix="/api/v1")  # Commented out for testing

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




# --- REAL-TIME BIOMETRIC "CAM LINK" (WEBSOCKET) ---

@app.websocket("/ws/mbic/{student_id}")
async def mbic_cam_link(websocket: WebSocket, student_id: str):
    """
    Enhanced MBIC WebSocket with Reference Face Integration
    Streams video frames and executes real-time biometric verification
    """
    await websocket.accept()
    
    # 1. FETCH REFERENCE FACE ENCODING from vault
    known_encoding = face_extractor.get_reference_encoding(student_id)
    
    if known_encoding is None:
        await websocket.send_json({
            "status": "ERROR",
            "message": "No reference face found. Please complete ID card registration first.",
            "action_required": "REGISTER_FACE"
        })
        await websocket.close()
        return
    
    # Reset engine for new session
    mbic_engine.generate_new_challenge()
    
    # Session tracking
    frame_count = 0
    session_start_time = datetime.datetime.now()
    
    try:
        while True:
            # Receive frame as Base64 string from Browser/App
            data = await websocket.receive_text()
            
            # Decode Base64 to CV2 Image
            header, encoded = data.split(",", 1)
            image_bytes = base64.b64decode(encoded)
            nparr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # 2. PROCESS MBIC with Reference Face
            result = mbic_engine.process_mbic_frame(frame, known_encoding)
            
            # Add session metadata
            result.update({
                "student_id": student_id,
                "frame_count": frame_count,
                "session_duration": (datetime.datetime.now() - session_start_time).total_seconds(),
                "current_challenge": mbic_engine.current_challenge
            })
            
            # 3. RESPOND INSTANTLY
            await websocket.send_json(result)
            
            # 4. SECURITY COUNCIL INTEGRATION
            if result.get("status") == "AUTHENTICATED":
                # Trigger Security Council audit
                council_result = await council.run_security_audit(
                    student_id, 
                    {"mbic_result": result, "verification_type": "REAL_TIME"}
                )
                
                # Send final verdict
                await websocket.send_json({
                    "status": "FINAL_VERDICT",
                    "verdict": "APPROVED" if council_result['approved'] else "FLAGGED",
                    "council_reasoning": council_result['reasoning'],
                    "session_summary": {
                        "total_frames": frame_count,
                        "session_duration": (datetime.datetime.now() - session_start_time).total_seconds(),
                        "challenges_completed": mbic_engine.challenge_met
                    }
                })
                
                print(f"✅ Student {student_id} Fully Verified via MBIC + Security Council.")
                break
            
            # Anti-spoofing: Check for suspicious patterns
            if frame_count > 100 and result.get("status") == "POSITIONING":
                # Too many frames without face detection - possible spoofing attempt
                await websocket.send_json({
                    "status": "SUSPICIOUS_ACTIVITY",
                    "message": "Please position your face clearly in the camera",
                    "security_flag": "EXCESSIVE_POSITIONING_ATTEMPTS"
                })
            
            frame_count += 1

    except WebSocketDisconnect:
        print(f"❌ MBIC Session Disconnected for {student_id}")
    except Exception as e:
        print(f"❌ MBIC Session Error for {student_id}: {str(e)}")
        await websocket.send_json({
            "status": "ERROR",
            "message": "Session error occurred",
            "error": str(e)
        })

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
    # liveness_data = await verify_liveness(liveness_video)
    
    # 2. COUNCIL DECISION (The 'Decide' Phase)
    council_result = await council.run_security_audit(national_id, forgery_data)
    
    # 3. GENERATE AUDIT LOG (The 'Accountability' Phase)
    audit_report = generate_audit_report(
        national_id, 
        forgery_data, 
        # liveness_data, 
        council_result['reasoning']
    )
    
    # 4. FINAL ACT
    return {
        "status": "PROCESSED",
        "verdict": "APPROVED" if council_result['approved'] else "FLAGGED",
        "explanation": audit_report['human_readable_explanation'],
        "tracking_id": audit_report['metadata']['student_id']
    }

# @app.post("/api/v1/verify/liveness")
# async def liveness_endpoint(video: UploadFile = File(...)):
#     # Real-time Blink Detection using EAR math
#     return await verify_liveness(video)

@app.post("/api/v1/verify/document")
async def document_endpoint(document: UploadFile = File(...)):
    # Real Math: Pixel-by-Pixel Error Level Analysis
    return await detect_pixel_anomalies(document)

@app.get("/api/v1/identity/qr/{student_id}")
async def get_qr(student_id: str):
    # Generates a Sovereign QR with SHA-256 Identity Hash
    return generate_student_qr(student_id)