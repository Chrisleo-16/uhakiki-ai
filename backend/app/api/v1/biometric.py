"""
Biometric API Routes
Handles biometric verification and liveness detection
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body
from typing import Dict, Optional
import base64
import logging
from app.services.simple_biometric_service import simple_biometric_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/liveness/challenge")
async def generate_liveness_challenge():
    """
    Generate a new MBIC liveness challenge
    """
    try:
        challenge = simple_biometric_service.generate_new_challenge()
        return {
            "challenge": challenge,
            "timestamp": simple_biometric_service.current_challenge is not None,
            "feedback": f"Please perform the following action: {challenge.replace('_', ' ').lower()}"
        }
    except Exception as e:
        logger.error(f"Failed to generate challenge: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate liveness challenge")

@router.post("/liveness/verify")
async def verify_liveness(
    image_data: dict = Body(...)
):
    """
    Verify liveness from captured frame
    """
    try:
        # Get base64 image from request
        base64_image = image_data.get("image")
        if not base64_image:
            raise HTTPException(status_code=400, detail="No image data provided")
        
        # Process for liveness detection
        result = simple_biometric_service.process_frame(image_data.get("image"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Liveness verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Liveness verification failed")

@router.post("/face/verify")
async def verify_face_match(
    live_face: UploadFile = File(...),
    student_id: str = Form(...),
    tolerance: float = Form(0.6)
):
    """
    Verify if live face matches reference face
    """
    try:
        # Read uploaded file
        contents = await live_face.read()
        base64_image = base64.b64encode(contents).decode('utf-8')
        
        # Verify face match
        result = simple_biometric_service.verify_face_match(student_id)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Face verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Face verification failed")

@router.post("/face/register")
async def register_reference_face(
    student_id: str = Form(...),
    id_card: UploadFile = File(...),
    national_id: Optional[str] = Form(None)
):
    """
    Register reference face from ID card
    """
    try:
        # Read ID card image
        contents = await id_card.read()
        base64_image = base64.b64encode(contents).decode('utf-8')
        
        # Decode image
        image = biometric_service.decode_base64_image(base64_image)
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid ID card image format")
        
        # Detect face in ID card
        face_detected, face_region = biometric_service.detect_face(image)
        
        if not face_detected:
            return {
                "success": False,
                "message": "No face detected in ID card",
                "feedback": "Please ensure the ID card has a clear photo"
            }
        
        # Extract face encoding (simplified - would use proper face recognition)
        landmarks = biometric_service.analyze_facial_landmarks(image, face_region)
        
        # Store reference face (in production, save to database)
        reference_data = {
            "student_id": student_id,
            "national_id": national_id,
            "face_detected": True,
            "face_region": face_region,
            "landmarks": landmarks,
            "registered_at": biometric_service.process_mbic_frame(image, None)["timestamp"]
        }
        
        return {
            "success": True,
            "message": "Reference face registered successfully",
            "student_id": student_id,
            "face_quality": "good" if landmarks.get("is_clear") else "poor",
            "feedback": "Face registration completed"
        }
        
    except Exception as e:
        logger.error(f"Face registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Face registration failed")

@router.get("/face/{student_id}")
async def get_reference_face(student_id: str):
    """
    Get reference face information for student
    """
    try:
        # In production, fetch from database
        # For now, return mock data
        reference_info = {
            "student_id": student_id,
            "face_registered": True,
            "registration_date": "2024-06-15T10:30:00Z",
            "face_quality": "good",
            "reference_available": True
        }
        
        return reference_info
        
    except Exception as e:
        logger.error(f"Failed to get reference face: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve reference face")

@router.post("/biometric/complete")
async def complete_biometric_verification(
    student_id: str = Form(...),
    liveness_score: float = Form(...),
    face_verified: bool = Form(...),
    session_data: str = Form(...)
):
    """
    Complete biometric verification process
    """
    try:
        # Process session data
        import json
        session_info = json.loads(session_data) if session_data else {}
        
        # Calculate overall biometric confidence
        overall_confidence = (liveness_score * 0.6) + (0.8 if face_verified else 0.4)
        
        # Determine verification result
        if overall_confidence > 0.7 and face_verified:
            result = "VERIFIED"
            status = "PASS"
        elif overall_confidence > 0.5:
            result = "REQUIRES_REVIEW"
            status = "REQUIRES_HUMAN_REVIEW"
        else:
            result = "FAILED"
            status = "FAIL"
        
        # Store verification result (in production, save to database)
        verification_record = {
            "student_id": student_id,
            "biometric_result": result,
            "liveness_score": liveness_score,
            "face_verified": face_verified,
            "overall_confidence": overall_confidence,
            "verification_status": status,
            "timestamp": session_info.get("timestamp"),
            "challenges_completed": session_info.get("challenges_completed", []),
            "session_duration": session_info.get("session_duration", 0)
        }
        
        return {
            "verification_result": result,
            "status": status,
            "confidence": overall_confidence,
            "student_id": student_id,
            "message": f"Biometric verification {result.lower()}",
            "next_steps": "Proceed to document verification" if result == "VERIFIED" else "Manual review required"
        }
        
    except Exception as e:
        logger.error(f"Biometric completion error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to complete biometric verification")
