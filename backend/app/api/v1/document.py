"""
Document API Routes  —  app/api/v1/document.py
Wired to document_scanning_service.py (v3 consolidated)
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body
from typing import Optional
import base64, logging, io, json
import cv2, numpy as np
from PIL import Image
import pytesseract

# ── Single import source — the v3 consolidated service ───────────────────────
from app.services.document_service import (
    document_service,
    extract_kenyan_id_fields,
    detect_pixel_anomalies,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
#  FIELD NORMALISER
#  Converts whatever the service returns into the exact shape the
#  frontend expects every single time.
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_fields(raw_fields: dict) -> dict:
    """
    Bridge between service field names and frontend expected keys.
    Frontend always expects:
        name, id_number, date_of_birth, sex, nationality, district, expiry_date
    """
    f = raw_fields or {}
    return {
        "name": (
            f.get("name") or f.get("full_name") or
            f.get("surname") or ""
        ),
        "id_number": (
            f.get("id_number") or f.get("idNumber") or
            f.get("serial_no") or f.get("serial") or ""
        ),
        "passport_number": f.get("passport_number") or "",
        "date_of_birth": (
            f.get("date_of_birth") or f.get("dob") or
            f.get("dateOfBirth") or ""
        ),
        "sex":         f.get("sex")         or f.get("gender")        or "",
        "nationality": f.get("nationality") or "",
        "district": (
            f.get("district")       or f.get("place_of_issue") or
            f.get("county")         or f.get("place_of_birth") or ""
        ),
        "expiry_date": f.get("expiry_date") or f.get("expiry") or "",
    }


# ─────────────────────────────────────────────────────────────────────────────
#  ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/scan/upload")
async def upload_document(
    document: UploadFile = File(...),
    document_type: Optional[str] = Form(None),
    student_id: Optional[str] = Form(None),
):
    """
    Primary upload endpoint.
    Accepts multipart/form-data with field name 'document'.
    Returns structured extraction + quality + forgery analysis.
    """
    try:
        contents     = await document.read()
        base64_image = base64.b64encode(contents).decode("utf-8")

        result = document_service.process_document(base64_image, document_type)

        if not result.get("success", False):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Document processing failed"),
            )

        result["extracted_fields"] = _normalize_fields(
            result.get("extracted_fields", {})
        )
        result["upload_info"] = {
            "filename":     document.filename,
            "file_size":    len(contents),
            "content_type": document.content_type,
            "student_id":   student_id,
            "uploaded_at":  result.get("processing_timestamp"),
        }

        logger.info(
            f"[UPLOAD] type={result.get('document_type')} | "
            f"score={result.get('overall_score', 0):.2f} | "
            f"status={result.get('verification_status')} | "
            f"fields={result['extracted_fields']}"
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
    Analyze a document from base64 image data (JSON body).
    Body: { "image": "<base64>", "document_type": "national_id" }
    """
    try:
        base64_image = image_data.get("image")
        if not base64_image:
            raise HTTPException(status_code=400, detail="No image data provided")

        result = document_service.process_document(
            base64_image, image_data.get("document_type")
        )

        if not result.get("success", False):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Document analysis failed"),
            )

        result["extracted_fields"] = _normalize_fields(
            result.get("extracted_fields", {})
        )
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
    Verify document integrity, optionally cross-checking against
    reference_data (JSON string of expected field values).
    """
    try:
        contents     = await document.read()
        base64_image = base64.b64encode(contents).decode("utf-8")

        result = document_service.process_document(base64_image)

        if not result.get("success", False):
            raise HTTPException(status_code=400, detail="Document processing failed")

        result["extracted_fields"]   = _normalize_fields(
            result.get("extracted_fields", {})
        )
        result["document_verified"]  = True
        result["verification_score"] = result.get("overall_score", 0)
        result["reference_match"]    = True

        if reference_data:
            try:
                ref      = json.loads(reference_data)
                extracted = result["extracted_fields"]
                matches, total = 0, 0
                for key, value in ref.items():
                    if key in extracted and extracted[key]:
                        total += 1
                        if str(extracted[key]).lower() == str(value).lower():
                            matches += 1
                if total > 0:
                    result["reference_match"] = (matches / total) > 0.8
                    result["field_matches"]   = f"{matches}/{total}"
            except Exception as e:
                logger.warning(f"Reference data comparison failed: {e}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document verification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Document verification failed")


@router.post("/verify")
async def verify_document_shorthand(
    file: UploadFile = File(...),
):
    """
    Shorthand verify endpoint used by main.py (/api/v1/document/verify).
    Accepts field name 'file' instead of 'document'.
    """
    try:
        contents     = await file.read()
        base64_image = base64.b64encode(contents).decode("utf-8")

        result = document_service.process_document(base64_image)

        if not result.get("success", False):
            return {"authentic": False, "error": result.get("error", "Failed")}

        fields     = _normalize_fields(result.get("extracted_fields", {}))
        forgery    = result.get("forgery_analysis", {})
        is_forged  = forgery.get("risk_level") == "high"
        confidence = result.get("overall_score", 0) * 100

        return {
            "authentic":         not is_forged,
            "confidence":        round(confidence, 2),
            "mse_score":         forgery.get("risk_score", 0),
            "message":           (
                "Document verified successfully"
                if not is_forged
                else "Document appears to be forged"
            ),
            "extracted_fields":  fields,
            "verification_status": result.get("verification_status"),
            "document_type":     result.get("document_type"),
        }

    except Exception as e:
        logger.error(f"Verify error: {e}", exc_info=True)
        return {"authentic": False, "error": "Verification failed"}


@router.post("/debug/ocr")
async def debug_ocr(document: UploadFile = File(...)):
    """
    DEBUG endpoint — shows raw Tesseract output for every preprocessing
    config so you can diagnose OCR issues.
    Remove or restrict before going to production.
    """
    try:
        contents = await document.read()
        nparr    = np.frombuffer(contents, np.uint8)
        image    = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise HTTPException(status_code=400, detail="Could not decode image")

        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        if w < 1400:
            scale = 1400 / w
            gray  = cv2.resize(gray, None, fx=scale, fy=scale,
                               interpolation=cv2.INTER_CUBIC)

        clahe    = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        _, otsu  = cv2.threshold(enhanced, 0, 255,
                                  cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        adapt    = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 13, 6
        )
        inv   = cv2.bitwise_not(otsu)
        sharp = cv2.filter2D(
            enhanced, -1, np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
        )

        combos = {
            "enhanced_psm6": (enhanced, "--oem 3 --psm 6 -l eng"),
            "otsu_psm6":     (otsu,     "--oem 3 --psm 6 -l eng"),
            "adapt_psm6":    (adapt,    "--oem 3 --psm 6 -l eng"),
            "enhanced_psm3": (enhanced, "--oem 3 --psm 3 -l eng"),
            "otsu_psm11":    (otsu,     "--oem 3 --psm 11 -l eng"),
            "inv_psm6":      (inv,      "--oem 3 --psm 6 -l eng"),
            "sharp_psm6":    (sharp,    "--oem 3 --psm 6 -l eng"),
            "enhanced_swa":  (enhanced, "--oem 3 --psm 6 -l eng+swa"),
        }

        results = {}
        for name, (arr, cfg) in combos.items():
            try:
                text = pytesseract.image_to_string(
                    Image.fromarray(arr), config=cfg
                ).strip()
                results[name] = {
                    "text": text, "length": len(text),
                    "lines": text.split("\n")
                }
            except Exception as e:
                results[name] = {"error": str(e)}

        # No-preprocessing pass
        try:
            orig_text = pytesseract.image_to_string(
                Image.open(io.BytesIO(contents)),
                config="--oem 3 --psm 6 -l eng"
            ).strip()
            results["original"] = {
                "text": orig_text, "length": len(orig_text),
                "lines": orig_text.split("\n")
            }
        except Exception as e:
            results["original"] = {"error": str(e)}

        # Also run through the full service pipeline
        try:
            b64    = base64.b64encode(contents).decode()
            svc_r  = document_service.process_document(b64)
            results["service_pipeline"] = {
                "extracted_fields": _normalize_fields(
                    svc_r.get("extracted_fields", {})
                ),
                "document_type":    svc_r.get("document_type"),
                "overall_score":    svc_r.get("overall_score"),
                "raw_text_preview": svc_r.get("extracted_text", "")[:300],
            }
        except Exception as e:
            results["service_pipeline"] = {"error": str(e)}

        best = max(
            {k: v for k, v in results.items() if k != "service_pipeline"}.items(),
            key=lambda x: x[1].get("length", 0)
        )

        return {
            "image_size":  {"w": w, "h": h},
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
    """Return supported document types and their field requirements."""
    return {
        "supported_types": {
            "national_id": {
                "name":              "Kenyan National ID Card",
                "required_fields":   ["id_number", "name", "date_of_birth"],
                "supported_formats": ["jpg", "jpeg", "png"],
                "min_quality_score": 0.6,
            },
            "passport": {
                "name":              "Kenyan Passport",
                "required_fields":   ["passport_number", "name", "nationality"],
                "supported_formats": ["jpg", "jpeg", "png"],
                "min_quality_score": 0.7,
            },
            "birth_certificate": {
                "name":              "Birth Certificate",
                "required_fields":   ["name", "date_of_birth", "place_of_birth"],
                "supported_formats": ["jpg", "jpeg", "png"],
                "min_quality_score": 0.5,
            },
        },
        "general_requirements": {
            "min_resolution":    "300dpi",
            "max_file_size":     "10MB",
            "accepted_formats":  ["jpg", "jpeg", "png"],
            "quality_threshold": 0.6,
        },
    }


@router.post("/scan/batch")
async def batch_process_documents(
    documents: list[UploadFile] = File(...),
    document_type: Optional[str] = Form(None),
):
    """Process multiple documents in one request."""
    results = []
    for doc in documents:
        try:
            contents     = await doc.read()
            base64_image = base64.b64encode(contents).decode("utf-8")
            result       = document_service.process_document(
                base64_image, document_type
            )
            result["extracted_fields"] = _normalize_fields(
                result.get("extracted_fields", {})
            )
            result["filename"]  = doc.filename
            result["file_size"] = len(contents)
            results.append(result)
        except Exception as e:
            logger.error(f"Batch: failed {doc.filename}: {e}")
            results.append({
                "success": False,
                "filename": doc.filename,
                "error": str(e),
            })

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
    """
    Quality stub — replace with real DB lookup in production.
    """
    return {
        "document_id":      document_id,
        "quality_metrics":  {
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