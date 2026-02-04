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
    # READ IMAGE
    content = await document_image.read()
    
    # 1. INPUT QUALITY GUARDRAIL
    passed, message = check_input_quality(content)
    if not passed:
        raise HTTPException(status_code=400, detail=message)

    # 2. NEURAL PRE-PROCESSING
    img = Image.open(io.BytesIO(content)).convert('L').resize((224, 224))
    img_tensor = transforms.ToTensor()(img).unsqueeze(0)
    
    # Run forgery detection
    residual_score, is_forgery = calculate_forgery_score(img_tensor)
    
    # --- GENERATE EVIDENCE FIRST (So it's ready for the response) ---
    with torch.no_grad():
        reconstruction_tensor = model(img_tensor)
    
    # Save to the STATIC folder so it's accessible via URL
    heatmap_filename = f"evidence_{national_id}.png"
    heatmap_path = os.path.join("static", heatmap_filename)
    generate_residual_heatmap(img_tensor, reconstruction_tensor, output_path=heatmap_path)

    # 3. VAULT SEARCH (Deduplication)
    search_query = f"{full_name} {national_id}"
    existing_matches = search_vault(search_query, limit=1)
    is_duplicate = False
    if existing_matches:
        _, distance = existing_matches[0]
        if distance < 0.4:
            is_duplicate = True

    # 4. AGENTIC JUDGMENT
    # Fixed variable name: used is_forgery instead of is_neural_forgery
    if is_forgery or is_duplicate:
        reason = "Neural Anomaly" if is_forgery else "Duplicate Identity Detected"
        return {
            "status": "FLAGGED_FOR_REVIEW",
            "risk_level": "CRITICAL",
            "reason": reason,
            "residual_mse": round(residual_score, 4),
            "evidence_url": f"/static/{heatmap_filename}"
        }

    # 5. FINAL COMMIT
    new_shard = {
        "content": f"{full_name} Authentic Document {national_id}",
        "metadata": {
            "national_id": national_id,
            "full_name": full_name,
            "timestamp": str(datetime.datetime.now()),
            "risk_score": round(residual_score, 4),
            "fraud_flag": "False"
        }
    }

    if not store_in_vault([new_shard]):
        raise HTTPException(status_code=500, detail="Vault Storage Failed")
    
    return {
        "status": "NATIONAL_RECORD_SECURED",
        "forgery_score": round(residual_score, 4),
        "identity_verification": "SUCCESS",
        "evidence_url": f"/static/{heatmap_filename}"
    }