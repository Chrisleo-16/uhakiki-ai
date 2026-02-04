from fastapi import *
from app.logic.vision_processing import check_input_quality
from app.logic.forgery_detector import calculate_forgery_score, model # Imported model for heatmap
from app.logic.visualiser import generate_residual_heatmap # New import
from app.db.milvus_client import store_in_vault, search_vault
import torch
from torchvision import transforms
from PIL import Image
import io
import datetime

# Define the router
router = APIRouter()

@router.post("/secure-ingest")
async def secure_ingest(
    national_id: str = Form(...), 
    full_name: str = Form(...), 
    document_image: UploadFile = File(...)
):
    """
    Modular Secure Ingest:
    Performs Quality Checks, Neural Forgery Analysis, and Vaulting.
    Now includes automated Residual Heatmap generation.
    """
    # READ IMAGE
    content = await document_image.read()
    
    # 1. INPUT QUALITY GUARDRAIL
    passed, message = check_input_quality(content)
    if not passed:
        raise HTTPException(status_code=400, detail=message)

    # 2. NEURAL FORGERY DETECTION (The RAD Engine)
    img = Image.open(io.BytesIO(content)).convert('L').resize((224, 224))
    img_tensor = transforms.ToTensor()(img).unsqueeze(0)
    
    # Get the score and forgery status
    residual_score, is_forgery = calculate_forgery_score(img_tensor)
    search_query = f"{full_name} {national_id}"
    existing_matches = search_vault(search_query, limit=1)
    is_duplicate = False
    if existing_matches:
        _, distance = existing_matches[0]
        if distance < 0.4: # Distance below 0.4 means "Too similar to someone else"
            is_duplicate = True

    # 3. COMBINED AGENTIC JUDGMENT
    if is_neural_forgery or is_duplicate:
        reason = "Neural Anomaly" if is_neural_forgery else "Duplicate Identity Detected"
        return {
            "status": "FLAGGED_FOR_REVIEW",
            "risk_level": "CRITICAL",
            "reason": reason,
            "evidence_url": f"http://127.0.0.1:8000/static/evidence_{national_id}.png"
        }
        # --- NEW: GENERATE RESIDUAL HEATMAP ---
    # We run the model one more time to get the reconstruction tensor for the visualizer
    with torch.no_grad():
        reconstruction_tensor = model(img_tensor)
    
    # Save the heatmap as 'evidence_{id}.png'
    heatmap_filename = f"evidence_{national_id}.png"
    generate_residual_heatmap(img_tensor, reconstruction_tensor, output_path=heatmap_filename)
    # 2. Check for Duplicates (Milvus Vault)
    
    
    if is_forgery:
        return {
            "status": "FLAGGED_FOR_REVIEW",
            "reason": "Neural Residual Alert (Possible Forgery)",
            "residual_mse": round(residual_score, 4),
            "evidence_map": heatmap_filename, # <--- Link to the visual evidence
            "action": "Write Waiting - Paused for Agentic Council Audit"
        }

    # 3. IDENTITY VAULTING (Check for duplicates before final save)
    search_query_text = f"{full_name} Authentic Document {national_id}"
    
    new_shard = {
        "content": search_query_text,
        "metadata": {
            "national_id": national_id,
            "full_name": full_name,
            "timestamp": str(datetime.datetime.now()),
            "risk_score": round(residual_score, 4),
            "fraud_flag": "False"
        }
    }

    success = store_in_vault([new_shard])
    if not success:
        raise HTTPException(status_code=500, detail="Vault Storage Failed")
    
    return {
        "status": "NATIONAL_RECORD_SECURED",
        "forgery_score": round(residual_score, 4),
        "identity_verification": "SUCCESS",
        "vault_status": "COMMITTED",
        "evidence_map": heatmap_filename # Also returned for successful audits
    }