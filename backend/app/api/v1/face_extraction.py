"""
Face Extraction API Routes
Handles extraction and storage of reference faces from ID cards
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from app.logic.face_extractor import face_extractor
from app.logic.vision_processing import check_input_quality

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/extract-reference-face")
async def extract_reference_face(
    student_id: str = Form(...),
    id_card: UploadFile = File(...),
    national_id: Optional[str] = Form(None)
):
    """
    Extract and store reference face from ID card
    
    Args:
        student_id: Unique student identifier
        id_card: ID card image file
        national_id: National ID number (optional)
    
    Returns:
        Face extraction results with encoding data
    """
    try:
        # Validate file type
        if not id_card.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400, 
                detail="File must be an image (JPEG, PNG, etc.)"
            )
        
        # Read image data
        image_data = await id_card.read()
        
        # Check image quality
        quality_valid, quality_message = check_input_quality(image_data)
        if not quality_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Image quality check failed: {quality_message}"
            )
        
        # Extract face
        extraction_result = face_extractor.extract_face_from_id_card(
            image_data, 
            student_id
        )
        
        if not extraction_result["success"]:
            raise HTTPException(
                status_code=400,
                detail=extraction_result["error"]
            )
        
        # Return success response
        return {
            "status": "SUCCESS",
            "student_id": student_id,
            "national_id": national_id,
            "face_extraction": {
                "face_detected": True,
                "confidence": extraction_result["confidence"],
                "encoding_length": len(extraction_result["encoding"]),
                "face_crop": extraction_result["face_crop"][:100] + "..." if extraction_result["face_crop"] else None
            },
            "storage": extraction_result["storage_result"],
            "message": "Reference face extracted and stored successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Face extraction API error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Face extraction failed: {str(e)}"
        )

@router.get("/get-reference-face/{student_id}")
async def get_reference_face(student_id: str):
    """
    Retrieve stored reference face information for a student
    
    Args:
        student_id: Student identifier
    
    Returns:
        Reference face data if found
    """
    try:
        from app.db.milvus_client import search_vault
        
        # Search for face encoding
        search_query = f"face_encoding_{student_id}"
        results = search_vault(search_query, limit=1)
        
        if not results or len(results) == 0:
            raise HTTPException(
                status_code=404,
                detail="No reference face found for this student"
            )
        
        doc, distance = results[0]
        metadata = doc.metadata
        
        return {
            "status": "FOUND",
            "student_id": student_id,
            "reference_face": {
                "encoding_length": metadata.get("encoding_length", 0),
                "face_crop": metadata.get("face_crop", ""),
                "image_shape": metadata.get("image_shape", []),
                "timestamp": metadata.get("timestamp", ""),
                "type": metadata.get("type", "face_encoding")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get reference face API error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve reference face: {str(e)}"
        )

@router.post("/verify-face-match")
async def verify_face_match(
    student_id: str = Form(...),
    live_face: UploadFile = File(...),
    tolerance: float = Form(0.6)
):
    """
    Verify live face against stored reference
    
    Args:
        student_id: Student identifier
        live_face: Live face image file
        tolerance: Face matching tolerance (default: 0.6)
    
    Returns:
        Face verification results
    """
    try:
        import face_recognition
        import numpy as np
        import cv2
        
        # Validate file type
        if not live_face.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400, 
                detail="File must be an image (JPEG, PNG, etc.)"
            )
        
        # Read and process live face
        image_data = await live_face.read()
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(
                status_code=400,
                detail="Invalid image format"
            )
        
        # Convert to RGB and extract face encoding
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_image)
        
        if not face_locations:
            raise HTTPException(
                status_code=400,
                detail="No face detected in live image"
            )
        
        # Use the largest face
        largest_face = face_extractor._get_largest_face(face_locations)
        face_encodings = face_recognition.face_encodings(rgb_image, [largest_face])
        
        if not face_encodings:
            raise HTTPException(
                status_code=400,
                detail="Could not generate face encoding from live image"
            )
        
        live_encoding = face_encodings[0]
        
        # Verify against reference
        verification_result = face_extractor.verify_face_match(
            student_id, 
            live_encoding, 
            tolerance
        )
        
        if not verification_result["success"]:
            raise HTTPException(
                status_code=400,
                detail=verification_result["error"]
            )
        
        return {
            "status": "PROCESSED",
            "student_id": student_id,
            "verification": {
                "verified": verification_result["verified"],
                "distance": verification_result["distance"],
                "tolerance": verification_result["tolerance"],
                "confidence": verification_result["confidence"]
            },
            "message": "Identity verified successfully" if verification_result["verified"] else "Identity verification failed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Face verification API error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Face verification failed: {str(e)}"
        )
