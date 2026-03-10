"""
Document API Routes
Handles document upload, processing, and verification
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body
from typing import Dict, Optional
import base64
import logging
import io
import cv2
import numpy as np
from PIL import Image
import pytesseract
from app.services.document_service import document_service

router = APIRouter()
logger = logging.getLogger(__name__)


def _normalize_fields(raw_fields: dict) -> dict:
    """
    Normalize extracted_fields from the backend service into a consistent
    shape that the frontend always expects.

    Frontend expects these keys:
        name, id_number, date_of_birth, sex, nationality, district, expiry_date

    The service may return varying key names — this bridges any gaps.
    """
    f = raw_fields or {}
    return {
        # Name — try several possible keys
        "name": (
            f.get("name") or
            f.get("full_name") or
            f.get("surname") or
            ""
        ),
        # ID number
        "id_number": (
            f.get("id_number") or
            f.get("idNumber") or
            f.get("serial_no") or
            f.get("serial") or
            ""
        ),
        # Passport number (returned separately for passports)
        "passport_number": f.get("passport_number") or "",
        # Date of birth
        "date_of_birth": (
            f.get("date_of_birth") or
            f.get("dob") or
            f.get("dateOfBirth") or
            ""
        ),
        # Sex / Gender
        "sex": f.get("sex") or f.get("gender") or "",
        # Nationality
        "nationality": f.get("nationality") or "",
        # District / Place of issue / County
        "district": (
            f.get("district") or
            f.get("place_of_issue") or
            f.get("county") or
            f.get("place_of_birth") or
            ""
        ),
        # Expiry date
        "expiry_date": f.get("expiry_date") or f.get("expiry") or "",
    }


@router.post("/scan/upload")
async def upload_document(
    document: UploadFile = File(...),
    document_type: Optional[str] = Form(None),
    student_id: Optional[str] = Form(None),
):
    """
    Upload and process a document for verification.
    Accepts the file under the field name 'document'.
    """
    try:
        contents    = await document.read()
        base64_image = base64.b64encode(contents).decode("utf-8")

        result = document_service.process_document(base64_image, document_type)

        if not result.get("success", False):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Document processing failed"),
            )

        # Normalise extracted fields before returning
        result["extracted_fields"] = _normalize_fields(result.get("extracted_fields", {}))

        result["upload_info"] = {
            "filename":     document.filename,
            "file_size":    len(contents),
            "content_type": document.content_type,
            "student_id":   student_id,
            "uploaded_at":  result.get("processing_timestamp"),
        }

        # Log what was extracted (helpful for debugging)
        logger.info(
            f"Document processed — type: {result.get('document_type')} | "
            f"score: {result.get('overall_score', 0):.2f} | "
            f"fields: {result['extracted_fields']}"
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Document upload failed")


@router.post("/scan/analyze")
async def analyze_document(image_data: dict = Body(...)):
    """
    Analyze a document from base64 image data.
    Body: { "image": "<base64>", "document_type": "national_id" }
    """
    try:
        base64_image = image_data.get("image")
        if not base64_image:
            raise HTTPException(status_code=400, detail="No image data provided")

        document_type = image_data.get("document_type")
        result        = document_service.process_document(base64_image, document_type)

        if not result.get("success", False):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Document analysis failed"),
            )

        result["extracted_fields"] = _normalize_fields(result.get("extracted_fields", {}))
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Document analysis failed")


@router.post("/verify/document")
async def verify_document_integrity(
    document: UploadFile = File(...),
    reference_data: Optional[str] = Form(None),
):
    """
    Verify document integrity, optionally against reference data.
    """
    try:
        contents     = await document.read()
        base64_image = base64.b64encode(contents).decode("utf-8")

        result = document_service.process_document(base64_image)

        if not result.get("success", False):
            raise HTTPException(status_code=400, detail="Document processing failed")

        result["extracted_fields"]  = _normalize_fields(result.get("extracted_fields", {}))
        result["document_verified"] = True
        result["verification_score"] = result.get("overall_score", 0)
        result["reference_match"]   = True

        if reference_data:
            try:
                import json
                ref_data        = json.loads(reference_data)
                extracted       = result["extracted_fields"]
                matches, total  = 0, 0
                for key, value in ref_data.items():
                    if key in extracted and extracted[key]:
                        total += 1
                        if str(extracted[key]).lower() == str(value).lower():
                            matches += 1
                if total > 0:
                    match_ratio = matches / total
                    result["reference_match"] = match_ratio > 0.8
                    result["field_matches"]   = f"{matches}/{total}"
            except Exception as e:
                logger.warning(f"Reference data comparison failed: {e}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document verification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Document verification failed")


@router.post("/debug/ocr")
async def debug_ocr(document: UploadFile = File(...)):
    """
    DEBUG ONLY — remove before production.
    Returns raw Tesseract output for every preprocessing config so you can
    see exactly what text the OCR is producing.
    """
    try:
        contents = await document.read()
        nparr    = np.frombuffer(contents, np.uint8)
        image    = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise HTTPException(status_code=400, detail="Could not decode image")

        h, w  = image.shape[:2]
        gray  = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Scale up
        if w < 1400:
            scale = 1400 / w
            gray  = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        clahe    = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        _, otsu  = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        adapt    = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 13, 6)
        inv      = cv2.bitwise_not(otsu)

        results = {}
        for name, (arr, cfg) in {
            "enhanced_psm6": (enhanced, "--oem 3 --psm 6"),
            "otsu_psm6":     (otsu,     "--oem 3 --psm 6"),
            "adapt_psm6":    (adapt,    "--oem 3 --psm 6"),
            "enhanced_psm3": (enhanced, "--oem 3 --psm 3"),
            "otsu_psm11":    (otsu,     "--oem 3 --psm 11"),
            "inv_psm6":      (inv,      "--oem 3 --psm 6"),
        }.items():
            try:
                text = pytesseract.image_to_string(Image.fromarray(arr), config=cfg + " -l eng").strip()
                results[name] = {"text": text, "length": len(text), "lines": text.split("\n")}
            except Exception as e:
                results[name] = {"error": str(e)}

        # Original no-preprocessing
        try:
            orig_pil  = Image.open(io.BytesIO(contents))
            orig_text = pytesseract.image_to_string(orig_pil, config="--oem 3 --psm 6 -l eng").strip()
            results["original"] = {"text": orig_text, "length": len(orig_text), "lines": orig_text.split("\n")}
        except Exception as e:
            results["original"] = {"error": str(e)}

        best = max(results.items(), key=lambda x: x[1].get("length", 0))
        return {
            "image_size": {"w": w, "h": h},
            "best_config": best[0],
            "best_text":   best[1].get("text", ""),
            "all_results": results,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scan/types")
async def get_supported_document_types():
    """Return list of supported document types and their requirements."""
    return {
        "supported_types": {
            "national_id": {
                "name":             "Kenyan National ID Card",
                "required_fields":  ["id_number", "name", "date_of_birth"],
                "supported_formats": ["jpg", "jpeg", "png"],
                "min_quality_score": 0.6,
            },
            "passport": {
                "name":             "Kenyan Passport",
                "required_fields":  ["passport_number", "name", "nationality"],
                "supported_formats": ["jpg", "jpeg", "png"],
                "min_quality_score": 0.7,
            },
            "birth_certificate": {
                "name":             "Birth Certificate",
                "required_fields":  ["name", "date_of_birth", "place_of_birth"],
                "supported_formats": ["jpg", "jpeg", "png"],
                "min_quality_score": 0.5,
            },
        },
        "general_requirements": {
            "min_resolution":   "300dpi",
            "max_file_size":    "10MB",
            "accepted_formats": ["jpg", "jpeg", "png"],
            "quality_threshold": 0.6,
        },
    }


@router.post("/scan/batch")
async def batch_process_documents(
    documents: list[UploadFile] = File(...),
    document_type: Optional[str] = Form(None),
):
    """Process multiple documents in batch."""
    results = []
    for doc in documents:
        try:
            contents     = await doc.read()
            base64_image = base64.b64encode(contents).decode("utf-8")
            result       = document_service.process_document(base64_image, document_type)
            result["extracted_fields"] = _normalize_fields(result.get("extracted_fields", {}))
            result["filename"]  = doc.filename
            result["file_size"] = len(contents)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process {doc.filename}: {e}")
            results.append({"success": False, "filename": doc.filename, "error": str(e)})

    successful = sum(1 for r in results if r.get("success", False))
    return {
        "batch_results": results,
        "summary": {
            "total_documents": len(results),
            "successful":      successful,
            "failed":          len(results) - successful,
            "success_rate":    successful / len(results) if results else 0,
        },
    }


@router.get("/scan/quality/{document_id}")
async def get_document_quality(document_id: str):
    """Get quality analysis for a processed document (stub — hook to DB in production)."""
    return {
        "document_id": document_id,
        "quality_metrics": {
            "sharpness":      85.2,
            "noise_level":    12.5,
            "brightness":     128.3,
            "contrast":       45.7,
            "edge_density":   0.12,
            "color_variance": 156.8,
        },
        "quality_score":      0.78,
        "quality_assessment": "good",
        "recommendations": [
            "Image quality is acceptable for verification",
            "All text regions are clearly visible",
            "No significant compression artifacts detected",
        ],
        "processed_at": "2024-06-15T14:30:00Z",
    }