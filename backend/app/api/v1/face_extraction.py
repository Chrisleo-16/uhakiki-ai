"""
Face Extraction API Routes
Handles extraction and storage of reference faces from ID cards
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import Optional
import logging
import numpy as np
from app.logic.face_extractor import face_extractor
from app.logic.vision_processing import check_input_quality
import cv2

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/extract-reference-face")
async def extract_reference_face(
    student_id: str = Form(...),
    id_card: UploadFile = File(...),
    national_id: Optional[str] = Form(None)
):
    try:
        # ... (file type validation and read) ...
        image_data = await id_card.read()
        
        # 1. Check initial quality
        quality_valid, quality_message = check_input_quality(image_data)
        
        processed_image_bytes = image_data
        
        if not quality_valid:
            logger.info(f"Low quality detected ({quality_message}). Attempting enhancement...")
            
            # Convert to CV2 to process
            nparr = np.frombuffer(image_data, np.uint8)
            cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Handle grayscale images
            if cv_img is not None and (len(cv_img.shape) == 2 or (len(cv_img.shape) == 3 and cv_img.shape[2] == 1)):
                cv_img = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2BGR)
            
            if cv_img is not None:
                # APPLY THE "WONDER" (Enhancement)
                enhanced_img = face_extractor.enhance_image(cv_img)
                
                # Convert back to bytes for the extractor
                _, buffer = cv2.imencode('.jpg', enhanced_img)
                processed_image_bytes = buffer.tobytes()
                
                # Re-check quality after enhancement
                new_valid, new_message = check_input_quality(processed_image_bytes)
                if not new_valid:
                    # If it's STILL too blurry even after enhancement, then we reject
                    raise HTTPException(
                        status_code=400,
                        detail=f"Image too blurry even after enhancement. Score: {new_message}"
                    )

        # 2. Extract face from the (potentially enhanced) image
        extraction_result = face_extractor.extract_face_from_id_card(
            processed_image_bytes, 
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
        
        # Handle grayscale images - convert to BGR
        if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1):
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        
        # Convert to RGB and extract face encoding
        if len(image.shape) == 3 and image.shape[2] == 3:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            rgb_image = image  # Already RGB (grayscale)
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
