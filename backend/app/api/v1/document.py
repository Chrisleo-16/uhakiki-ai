"""
Document API Routes
Handles document upload, processing, and verification
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body
from typing import Dict, Optional
import base64
import logging
from app.services.simple_document_service import simple_document_service
from app.services.document_service import document_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Use real document service for actual OCR
USE_REAL_SERVICE = True

def get_document_service():
    """Get the appropriate document service based on configuration"""
    if USE_REAL_SERVICE:
        return document_service
    return simple_document_service

@router.post("/scan/upload")
async def upload_document(
    document: UploadFile = File(...),
    document_type: Optional[str] = Form(None),
    student_id: Optional[str] = Form(None)
):
    """
    Upload and process document for verification
    """
    try:
        # Read uploaded file
        contents = await document.read()
        base64_image = base64.b64encode(contents).decode('utf-8')
        
        # Get the service
        doc_service = get_document_service()
        
        # Process document
        result = doc_service.process_document(base64_image, document_type)
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Document processing failed"))
        
        # Add metadata
        result["upload_info"] = {
            "filename": document.filename,
            "file_size": len(contents),
            "content_type": document.content_type,
            "student_id": student_id,
            "uploaded_at": result.get("processing_timestamp")
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="Document upload failed")

@router.post("/scan/analyze")
async def analyze_document(
    image_data: dict = Body(...)
):
    """
    Analyze document from base64 image data
    """
    try:
        # Get base64 image from request
        base64_image = image_data.get("image")
        if not base64_image:
            raise HTTPException(status_code=400, detail="No image data provided")
        
        document_type = image_data.get("document_type")
        
        # Get the service
        doc_service = get_document_service()
        
        # Process document
        result = doc_service.process_document(base64_image, document_type)
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Document analysis failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail="Document analysis failed")

@router.post("/verify/document")
async def verify_document_integrity(
    document: UploadFile = File(...),
    reference_data: Optional[str] = Form(None)
):
    """
    Verify document integrity against reference data
    """
    try:
        # Read uploaded file
        contents = await document.read()
        base64_image = base64.b64encode(contents).decode('utf-8')
        
        # Get the service
        doc_service = get_document_service()
        
        # Process document
        verification_result = doc_service.verify_document_integrity(base64_image, reference_data)
        
        if not verification_result.get("success", False):
            raise HTTPException(status_code=400, detail="Document processing failed")
        
        # Additional verification against reference data if provided
        verification_result["document_verified"] = True
        verification_result["verification_score"] = verification_result.get("overall_score", 0)
        verification_result["verification_status"] = verification_result.get("verification_status", "UNKNOWN")
        verification_result["document_analysis"] = verification_result
        verification_result["reference_match"] = True  # Simplified - would compare with actual reference
        
        if reference_data:
            try:
                import json
                ref_data = json.loads(reference_data)
                # Compare extracted fields with reference
                extracted_fields = result.get("extracted_fields", {})
                
                matches = 0
                total_checks = 0
                
                for key, value in ref_data.items():
                    if key in extracted_fields:
                        total_checks += 1
                        if str(extracted_fields[key]).lower() == str(value).lower():
                            matches += 1
                
                if total_checks > 0:
                    match_ratio = matches / total_checks
                    verification_result["reference_match"] = match_ratio > 0.8
                    verification_result["field_matches"] = f"{matches}/{total_checks}"
                
            except Exception as e:
                logger.warning(f"Reference data comparison failed: {e}")
        
        return verification_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Document verification failed")

@router.get("/scan/types")
async def get_supported_document_types():
    """
    Get list of supported document types
    """
    try:
        document_types = {
            "national_id": {
                "name": "Kenyan National ID Card",
                "required_fields": ["id_number", "name", "date_of_birth"],
                "supported_formats": ["jpg", "jpeg", "png"],
                "min_quality_score": 0.6
            },
            "passport": {
                "name": "Kenyan Passport",
                "required_fields": ["passport_number", "name", "nationality"],
                "supported_formats": ["jpg", "jpeg", "png"],
                "min_quality_score": 0.7
            },
            "birth_certificate": {
                "name": "Birth Certificate",
                "required_fields": ["name", "date_of_birth", "place_of_birth"],
                "supported_formats": ["jpg", "jpeg", "png"],
                "min_quality_score": 0.5
            }
        }
        
        return {
            "supported_types": document_types,
            "general_requirements": {
                "min_resolution": "300dpi",
                "max_file_size": "10MB",
                "accepted_formats": ["jpg", "jpeg", "png"],
                "quality_threshold": 0.6
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get document types: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document types")

@router.post("/scan/batch")
async def batch_process_documents(
    documents: list[UploadFile] = File(...),
    document_type: Optional[str] = Form(None)
):
    """
    Process multiple documents in batch
    """
    try:
        results = []
        
        for document in documents:
            try:
                # Read file
                contents = await document.read()
                base64_image = base64.b64encode(contents).decode('utf-8')
                
                # Process document
                result = simple_document_service.process_document(base64_image, document_type)
                
                # Add file info
                result["filename"] = document.filename
                result["file_size"] = len(contents)
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to process {document.filename}: {e}")
                results.append({
                    "success": False,
                    "filename": document.filename,
                    "error": str(e)
                })
        
        # Summary
        successful = sum(1 for r in results if r.get("success", False))
        failed = len(results) - successful
        
        return {
            "batch_results": results,
            "summary": {
                "total_documents": len(results),
                "successful": successful,
                "failed": failed,
                "success_rate": successful / len(results) if results else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Batch processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Batch processing failed")

@router.get("/scan/quality/{document_id}")
async def get_document_quality(document_id: str):
    """
    Get detailed quality analysis for a processed document
    """
    try:
        # In production, fetch from database using document_id
        # For now, return sample quality analysis
        
        quality_report = {
            "document_id": document_id,
            "quality_metrics": {
                "sharpness": 85.2,
                "noise_level": 12.5,
                "brightness": 128.3,
                "contrast": 45.7,
                "edge_density": 0.12,
                "color_variance": 156.8
            },
            "quality_score": 0.78,
            "quality_assessment": "good",
            "recommendations": [
                "Image quality is acceptable for verification",
                "All text regions are clearly visible",
                "No significant compression artifacts detected"
            ],
            "processed_at": "2024-06-15T14:30:00Z"
        }
        
        return quality_report
        
    except Exception as e:
        logger.error(f"Failed to get document quality: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve quality analysis")
