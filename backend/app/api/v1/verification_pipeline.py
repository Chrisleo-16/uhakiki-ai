"""
Unified Verification Pipeline API
Integrates GD-FD, MBIC, and AAFI components into comprehensive verification system
"""

import asyncio
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import base64
import cv2
import numpy as np
from fastapi import APIRouter, File, Form, UploadFile, HTTPException, WebSocket
from fastapi.responses import JSONResponse

from app.agents.master_agent import master_agent, VerificationContext, VerificationPhase
from app.logic.forgery_detector import detect_pixel_anomalies
from app.logic.liveness_detector import MBICSystem
from app.logic.voice_biometrics import voice_biometrics
from app.db.milvus_client import store_in_vault, search_vault
import random

router = APIRouter()


@router.post("/comprehensive-verification")
async def comprehensive_verification(
    national_id: str = Form(...),
    student_id: str = Form(...),
    document_image: UploadFile = File(...),
    face_image: UploadFile = File(None),
    voice_audio: UploadFile = File(None),
    liveness_video: UploadFile = File(None)
):
    """
    Comprehensive verification endpoint integrating all AAFI components
    Implements the full GD-FD → MBIC → AAFI pipeline
    """
    try:
        print(f"🚀 [PIPELINE] Starting comprehensive verification for student {student_id}")
        
        # Generate tracking ID
        tracking_id = str(uuid.uuid4())
        
        # Initialize verification context
        context = VerificationContext(
            student_id=student_id,
            national_id=national_id,
            document_path=document_image.filename,
            biometric_data={},
            verification_history=[],
            current_phase=VerificationPhase.OBSERVE
        )
        
        # Step 1: Document Forgery Detection (GD-FD)
        print("📄 [GD-FD] Performing document forgery detection...")
        forgery_results = await detect_pixel_anomalies(document_image)
        context.agent_outputs["forgery_detection"] = forgery_results
        
        # Step 2: Biometric Data Processing (MBIC)
        print("👤 [MBIC] Processing biometric verification...")
        biometric_results = await process_biometric_verification(
            face_image, voice_audio, liveness_video, student_id
        )
        context.biometric_data = biometric_results
        
        # Step 3: External Data Ingestion
        print("📡 [DATA] Ingesting external verification data...")
        data_ingestion_results = await master_agent.data_agent.ingest_data(context)
        context.agent_outputs["data_ingestion"] = data_ingestion_results
        
        # Step 4: Run AAFI Pipeline
        print("🤖 [AAFI] Running autonomous fraud investigation...")
        aafi_results = await master_agent.run_verification_pipeline(context)
        
        # Step 5: Store results in vault
        await store_verification_results(tracking_id, context, aafi_results)
        
        # Return comprehensive results
        return {
            "tracking_id": tracking_id,
            "timestamp": datetime.now().isoformat(),
            "student_id": student_id,
            "national_id": national_id,
            "verification_results": {
                "document_analysis": forgery_results,
                "biometric_analysis": biometric_results,
                "data_ingestion": data_ingestion_results,
                "aafi_decision": aafi_results
            },
            "final_verdict": aafi_results["verdict"],
            "confidence_score": aafi_results.get("confidence", 0.0),
            "risk_score": aafi_results.get("risk_score", 0.0),
            "compliance_status": "COMPLIANT" if aafi_results.get("confidence", 0) > 0.75 else "REVIEW_REQUIRED"
        }
        
    except Exception as e:
        print(f"❌ [PIPELINE] Verification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Verification pipeline error: {str(e)}")


async def process_biometric_verification(
    face_image: Optional[UploadFile],
    voice_audio: Optional[UploadFile], 
    liveness_video: Optional[UploadFile],
    student_id: str
) -> Dict[str, Any]:
    """
    Process all biometric verification components
    """
    mbic_system = MBICSystem()
    biometric_results = {
        "face_verification": {},
        "voice_verification": {},
        "liveness_verification": {},
        "overall_biometric_score": 0.0
    }
    
    try:
        # Face verification
        if face_image:
            face_content = await face_image.read()
            face_array = np.frombuffer(face_content, np.uint8)
            face_img = cv2.imdecode(face_array, cv2.IMREAD_COLOR)
            
            # Extract face encoding
            import face_recognition
            small_frame = cv2.resize(face_img, (0, 0), fx=0.25, fy=0.25)
            rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            
            if face_locations:
                face_encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]
                
                # For demo, compare against a placeholder encoding
                # In production, would fetch from vault
                known_encoding = face_encoding  # Placeholder
                
                face_match = face_recognition.compare_faces([known_encoding], face_encoding)[0]
                face_distance = face_recognition.face_distance([known_encoding], face_encoding)[0]
                
                biometric_results["face_verification"] = {
                    "face_detected": True,
                    "match_confidence": float(1.0 - face_distance),
                    "verified": bool(face_match),
                    "encoding_quality": "HIGH"
                }
            else:
                biometric_results["face_verification"] = {
                    "face_detected": False,
                    "error": "No face detected in image"
                }
        
        # Voice verification
        if voice_audio:
            voice_content = await voice_audio.read()
            
            # Convert to numpy array (assuming WAV format)
            import librosa
            voice_data, sr = librosa.load(voice_content, sr=16000)
            
            # Verify voice against stored profile
            voice_result = voice_biometrics.verify_voice(student_id, voice_data)
            biometric_results["voice_verification"] = voice_result
        
        # Liveness verification
        if liveness_video:
            liveness_content = await liveness_video.read()
            
            # Process video for liveness detection
            liveness_result = await process_liveness_video(liveness_content, mbic_system)
            biometric_results["liveness_verification"] = liveness_result
        
        # Calculate overall biometric score
        scores = []
        if biometric_results["face_verification"].get("verified"):
            scores.append(biometric_results["face_verification"]["match_confidence"])
        
        if biometric_results["voice_verification"].get("verified"):
            scores.append(biometric_results["voice_verification"]["match_score"])
        
        if biometric_results["liveness_verification"].get("liveness_confirmed"):
            scores.append(biometric_results["liveness_verification"]["confidence"])
        
        if scores:
            biometric_results["overall_biometric_score"] = sum(scores) / len(scores)
        
        return biometric_results
        
    except Exception as e:
        print(f"❌ [BIOMETRIC] Biometric verification failed: {e}")
        biometric_results["error"] = str(e)
        return biometric_results


async def process_liveness_video(video_content: bytes, mbic_system: MBICSystem) -> Dict[str, Any]:
    """
    Process video for liveness detection
    """
    try:
        # Save video temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_file.write(video_content)
            temp_path = temp_file.name
        
        # Process video frames
        import cv2
        cap = cv2.VideoCapture(temp_path)
        
        frame_count = 0
        blink_detected = 0
        challenge_met = False
        
        # Generate challenge
        mbic_system.generate_new_challenge()
        
        while cap.isOpened() and frame_count < 100:  # Process max 100 frames
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process frame for liveness
            result = mbic_system.process_mbic_frame(frame, known_encoding=None)
            
            if result.get("status") == "AUTHENTICATED":
                challenge_met = True
                break
            
            frame_count += 1
        
        cap.release()
        
        # Clean up temp file
        import os
        os.unlink(temp_path)
        
        return {
            "liveness_confirmed": challenge_met,
            "frames_processed": frame_count,
            "challenge_type": mbic_system.current_challenge,
            "confidence": 0.8 if challenge_met else 0.3
        }
        
    except Exception as e:
        return {
            "liveness_confirmed": False,
            "error": str(e),
            "confidence": 0.0
        }


async def store_verification_results(
    tracking_id: str, 
    context: VerificationContext, 
    aafi_results: Dict[str, Any]
):
    """
    Store verification results in Milvus vault for audit trail
    """
    try:
        # Create verification record
        verification_record = {
            "content": f"Verification {tracking_id} for student {context.student_id}",
            "metadata": {
                "tracking_id": tracking_id,
                "student_id": context.student_id,
                "national_id": context.national_id,
                "timestamp": datetime.now().isoformat(),
                "verdict": aafi_results["verdict"],
                "risk_score": aafi_results.get("risk_score", 0.0),
                "confidence": aafi_results.get("confidence", 0.0),
                "cycles_completed": aafi_results.get("cycles_completed", 0)
            }
        }
        
        # Store in vault
        success = store_in_vault([verification_record])
        
        if success:
            print(f"✅ [VAULT] Verification results stored for tracking ID {tracking_id}")
        else:
            print(f"⚠️ [VAULT] Failed to store verification results")
            
    except Exception as e:
        print(f"❌ [VAULT] Error storing verification results: {e}")


@router.websocket("/ws/live-verification/{student_id}")
async def live_verification_websocket(websocket: WebSocket, student_id: str):
    """
    WebSocket endpoint for real-time biometric verification
    """
    await websocket.accept()
    
    mbic_system = MBICSystem()
    mbic_system.generate_new_challenge()
    
    try:
        while True:
            # Receive data (could be frame or audio chunk)
            data = await websocket.receive_text()
            
            try:
                # Parse data type and content
                if data.startswith("FRAME:"):
                    # Process video frame
                    encoded_frame = data[6:]  # Remove "FRAME:" prefix
                    image_bytes = base64.b64decode(encoded_frame)
                    nparr = np.frombuffer(image_bytes, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    # Process frame
                    result = mbic_system.process_mbic_frame(frame, known_encoding=None)
                    
                elif data.startswith("AUDIO:"):
                    # Process audio chunk
                    encoded_audio = data[6:]  # Remove "AUDIO:" prefix
                    audio_bytes = base64.b64decode(encoded_audio)
                    
                    # Convert to numpy array and process
                    import librosa
                    audio_data, _ = librosa.load(audio_bytes, sr=16000)
                    
                    # Verify voice
                    voice_result = voice_biometrics.verify_voice(student_id, audio_data)
                    
                    result = {
                        "type": "voice_verification",
                        "result": voice_result
                    }
                else:
                    result = {"error": "Unknown data type"}
                
                # Send result back
                await websocket.send_json(result)
                
                # Check if verification is complete
                if result.get("status") == "AUTHENTICATED" or result.get("result", {}).get("verified"):
                    await websocket.send_json({
                        "status": "VERIFICATION_COMPLETE",
                        "message": "Biometric verification successful"
                    })
                    break
                    
            except Exception as e:
                await websocket.send_json({
                    "error": f"Processing error: {str(e)}"
                })
                
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()


@router.get("/verification-status/{tracking_id}")
async def get_verification_status(tracking_id: str):
    """
    Get verification status by tracking ID
    """
    try:
        # Search vault for verification record
        results = search_vault(tracking_id, limit=1)
        
        if results:
            doc, distance = results[0]
            metadata = doc.metadata
            
            return {
                "tracking_id": tracking_id,
                "status": "COMPLETED",
                "verdict": metadata.get("verdict"),
                "risk_score": metadata.get("risk_score"),
                "confidence": metadata.get("confidence"),
                "timestamp": metadata.get("timestamp")
            }
        else:
            return {
                "tracking_id": tracking_id,
                "status": "NOT_FOUND",
                "message": "Verification record not found"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.post("/enroll-voice-profile")
async def enroll_voice_profile(
    student_id: str = Form(...),
    audio_samples: list[UploadFile] = File(...)
):
    """
    Enroll voice profile for student
    """
    try:
        if len(audio_samples) < 3:
            raise HTTPException(
                status_code=400, 
                detail="Minimum 3 audio samples required for voice enrollment"
            )
        
        # Process audio samples
        audio_data_list = []
        for audio_file in audio_samples:
            content = await audio_file.read()
            
            # Convert to numpy array
            import librosa
            import io
            
            # Load audio from bytes
            audio_buffer = io.BytesIO(content)
            audio_data, sr = librosa.load(audio_buffer, sr=16000)
            audio_data_list.append(audio_data)
        
        # Create voice profile
        result = voice_biometrics.create_voice_profile(student_id, audio_data_list)
        
        if result["success"]:
            return {
                "status": "VOICE_PROFILE_ENROLLED",
                "student_id": student_id,
                "quality_score": result["quality_score"],
                "samples_used": result["samples_used"],
                "enrollment_timestamp": result["enrollment_timestamp"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice enrollment failed: {str(e)}")
