import os
import io
import datetime
import torch
import cv2
import numpy as np
from PIL import Image
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from torchvision import transforms


# Internal Logic Imports
from app.logic.vision_processing import check_input_quality
from app.db.milvus_client import store_in_vault, search_vault
from app.logic.forgery_detector import calculate_forgery_score, get_reconstruction
from app.logic.visualiser import generate_residual_heatmap
from app.logic.retracer import AdaptiveRetracer
from app.logic.ocr_engine import OCRModel

router = APIRouter()

@router.post("/secure-ingest")
async def secure_ingest(
    national_id: str = Form(...), 
    document_image: UploadFile = File(...)
):
    content = await document_image.read()
    
    # --- 1. OBSERVE & ORIENT (Adaptive Retracing) ---
    nparr = np.frombuffer(content, np.uint8)
    cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    retracer = AdaptiveRetracer()
    blur_score = retracer.detect_blur(cv_img)
    
    adjustment = "None"
    if blur_score < 100:  # If blurry, retrace/sharpen
        cv_img = retracer.sharpen_document(cv_img)
        adjustment = "Sharpened"
        # Update content for the OCR and Forgery models
        _, encoded_img = cv2.imencode('.png', cv_img)
        content = encoded_img.tobytes()

    # --- 2. DATA FILLING (OCR Extraction) ---
    # We extract data to see if the ID provided matches the ID on the paper
    ocr_result = OCRModel.extract(content)
    
    if not ocr_result.get("index_number"):
        # If we can't find an ID even after sharpening, it's a Trust Gap/Capacity Mismatch
        return {
            "status": "RETRY_REQUIRED",
            "reason": "Document illegible. Please provide a clearer scan.",
            "blur_score": round(blur_score, 2)
        }

    # 3. NEURAL FORGERY DETECTION (RAD)
    # Convert OpenCV image (BGR) to PIL Grayscale for the Autoencoder
    processed_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    pil_img = Image.fromarray(processed_img).resize((224, 224))
    img_tensor = transforms.ToTensor()(pil_img).unsqueeze(0)
    
    residual_score, is_forgery = calculate_forgery_score(img_tensor)
    
    # --- GENERATE EVIDENCE HEATMAP ---
    with torch.no_grad():
        reconstruction_tensor = get_reconstruction(img_tensor)
    
    heatmap_filename = f"evidence_{national_id}.png"
    # Ensure static directory exists
    os.makedirs("static", exist_ok=True)
    heatmap_path = os.path.join("static", heatmap_filename)
    generate_residual_heatmap(img_tensor, reconstruction_tensor, output_path=heatmap_path)

    # 4. VAULT SEARCH (Deduplication)
    search_query = f"{full_name} {national_id}"
    existing_matches = search_vault(search_query, limit=1)
    is_duplicate = False
    if existing_matches:
        _, distance = existing_matches[0]
        # If vector distance is very low, it's a duplicate
        if distance < 0.4:
            is_duplicate = True

    # 5. AGENTIC JUDGMENT
    if is_forgery or is_duplicate:
        reason = "Neural Anomaly" if is_forgery else "Duplicate Identity Detected"
        return {
            "status": "FLAGGED_FOR_REVIEW",
            "risk_level": "CRITICAL",
            "reason": reason,
            "blur_score": round(blur_score, 2),
            "adjustment": adjustment,
            "residual_mse": round(residual_score, 4),
            "evidence_url": f"/static/{heatmap_filename}"
        }

    # 6. FINAL COMMIT TO SOVEREIGN VAULT
    new_shard = {
        "content": f"{full_name} Authentic Document {national_id}",
        "metadata": {
            "national_id": national_id,
            "full_name": full_name,
            "timestamp": str(datetime.datetime.now()),
            "risk_score": round(residual_score, 4),
            "adjustment_applied": adjustment
        }
    }

    if not store_in_vault([new_shard]):
        raise HTTPException(status_code=500, detail="Vault Storage Failed")
    
    return {
        "status": "NATIONAL_RECORD_SECURED",
        "identity_verification": "SUCCESS",
        "forgery_score": round(residual_score, 4),
        "blur_score": round(blur_score, 2),
        "evidence_url": f"/static/{heatmap_filename}"
    }