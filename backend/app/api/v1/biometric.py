"""
Biometric API Routes
Handles biometric verification and liveness detection
Uses BiometricLivenessService for real OpenCV-based liveness
Uses face_extractor for ID card registration and Milvus storage
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body
from typing import Optional
import base64
import json
import logging

from app.services.biometric_service import biometric_service
from app.logic.face_extractor import face_extractor

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/liveness/challenge")
async def generate_liveness_challenge():
    """Generate a new MBIC liveness challenge"""
    try:
        challenge = biometric_service.generate_new_challenge()
        return {
            "challenge": challenge,
            "feedback": f"Please perform the following action: {challenge.replace('_', ' ').lower()}"
        }
    except Exception as e:
        logger.error(f"Failed to generate challenge: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate liveness challenge")


@router.post("/liveness/verify")
async def verify_liveness(image_data: dict = Body(...)):
    """Verify liveness from a captured frame"""
    try:
        base64_image = image_data.get("image")
        if not base64_image:
            raise HTTPException(status_code=400, detail="No image data provided")

        image = biometric_service.decode_base64_image(base64_image)
        if image is None:
            raise HTTPException(status_code=400, detail="Could not decode image")

        result = biometric_service.process_mbic_frame(image)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Liveness verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Liveness verification failed")


@router.post("/face/register")
async def register_reference_face(
    student_id: str = Form(...),
    id_card: UploadFile = File(...),
    national_id: Optional[str] = Form(None)
):
    """
    Register reference face from ID card.
    Stores encoding in Milvus via face_extractor.
    """
    try:
        contents = await id_card.read()

        result = face_extractor.extract_face_from_id_card(contents, student_id)

        if not result["success"]:
            return {
                "success": False,
                "message": result.get("error", "Face extraction failed"),
                "feedback": result.get("suggestion", "Please ensure the ID card has a clear front-facing photo")
            }

        return {
            "success": True,
            "message": "Reference face registered successfully",
            "student_id": student_id,
            "national_id": national_id,
            "face_quality": "good" if result.get("confidence", 0) > 0.5 else "poor",
            "confidence": result.get("confidence"),
            "encoding_length": len(result.get("encoding", [])),
            "feedback": "Face registration completed. You may now proceed to verification."
        }

    except Exception as e:
        logger.error(f"Face registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Face registration failed")


@router.post("/face/verify")
async def verify_face_match(
    live_face: UploadFile = File(...),
    student_id: str = Form(...),
    tolerance: float = Form(0.6)
):
    """
    Verify if a live face matches the reference stored in Milvus.
    Uses face_recognition for encoding, face_extractor for Milvus lookup.
    """
    try:
        import face_recognition
        import numpy as np
        import cv2

        contents = await live_face.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image format")

        # Handle grayscale images
        if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1):
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        if len(image.shape) == 3 and image.shape[2] == 3:
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            rgb = image  # Already RGB (grayscale)
        locations = face_recognition.face_locations(rgb, model="hog", number_of_times_to_upsample=2)

        if not locations:
            return {"verified": False, "confidence": 0.0, "feedback": "No face detected in uploaded image"}

        encodings = face_recognition.face_encodings(rgb, locations)
        if not encodings:
            return {"verified": False, "confidence": 0.0, "feedback": "Could not encode face"}

        result = face_extractor.verify_face_match(student_id, encodings[0], tolerance)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Face verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Face verification failed")


@router.get("/face/{student_id}")
async def get_reference_face(student_id: str):
    """Check if a reference face encoding exists for a student in Milvus"""
    try:
        encoding = face_extractor.get_reference_encoding(student_id)
        face_registered = encoding is not None

        return {
            "student_id": student_id,
            "face_registered": face_registered,
            "reference_available": face_registered,
            "feedback": "Reference face found" if face_registered else "No reference face registered for this student"
        }

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
    """Complete biometric verification and return final result"""
    try:
        session_info = json.loads(session_data) if session_data else {}

        overall_confidence = (liveness_score * 0.6) + (0.8 if face_verified else 0.4)

        if overall_confidence > 0.7 and face_verified:
            result, status = "VERIFIED", "PASS"
        elif overall_confidence > 0.5:
            result, status = "REQUIRES_REVIEW", "REQUIRES_HUMAN_REVIEW"
        else:
            result, status = "FAILED", "FAIL"

        return {
            "verification_result": result,
            "status": status,
            "confidence": overall_confidence,
            "student_id": student_id,
            "message": f"Biometric verification {result.lower()}",
            "challenges_completed": session_info.get("challenges_completed", []),
            "session_duration": session_info.get("session_duration", 0),
            "timestamp": session_info.get("timestamp"),
            "next_steps": "Proceed to document verification" if result == "VERIFIED" else "Manual review required"
        }

    except Exception as e:
        logger.error(f"Biometric completion error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to complete biometric verification")