import json
import hashlib
import sys
import os
from .forgery_detector import perform_ela, get_forgery_judgment
# --- CRITICAL FIX: Use CrewAI's native tool decorator ---
from crewai.tools import tool 

# Optional: Handle Milvus import gracefully if not installed/running
try:
    from pymilvus import Collection, connections
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False

# Path injection to find VerificationService
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Try to load the "Real" Brain (VerificationService)
try:
    from app.logic.verification_service import VerificationService
    verifier = VerificationService()
except (ImportError, ModuleNotFoundError):
    verifier = None
    print("⚠️  [WARNING] VerificationService not found. Running in MOCK mode.")

@tool("forgery_scan_tool")
def forgery_scan_tool(image_path: str) -> str:
    """
    Analyzes the pixel structure of a document ID to detect digital manipulation.
    Input should be a string path to the image file.
    """
    if not verifier:
        return "SCAN ERROR: Verification engine not loaded."
        
    try:
        result = verifier.verify(image_path)
        return f"SCAN RESULT: {result}"
    except Exception as e:
        return f"SCAN ERROR: {str(e)}"

@tool("vault_search_tool")
def vault_search_tool(national_id: str) -> str:
    """
    Checks the Sovereign Milvus Vault for the 14-digit Maisha Namba (UPI).
    Input: 8-digit Legacy ID or 14-digit Maisha UPI string.
    """
    # 1. Kenya Maisha Namba Validation Logic
    is_valid_format = re.match(r"^\d{8}$|^\d{14}$", national_id)
    if not is_valid_format:
        return "VAULT ERROR: ID must be 8 (Legacy) or 14 digits (Maisha UPI)."

    if not MILVUS_AVAILABLE:
        return "VAULT ERROR: Database drivers missing on this node."

    try:
        # High Availability Connection (Konza Node 01)
        connections.connect(alias="default", host="localhost", port="19530")
        collection = Collection("sovereign_vault")
        collection.load()
        
        # Search for UPI
        res = collection.query(
            expr=f"national_id == '{national_id}'",
            output_fields=["national_id", "status"],
            limit=1
        )
        
        if res:
            return f"VAULT ALERT: UPI {national_id} is already registered. Potential 'Identity Farming' attempt."
        
        return f"VAULT CLEAN: {national_id} is a new unique applicant."
    except Exception as e:
        # Resilience: Fallback to a 'Safe-Insecure' mode for demo if DB is offline
        return f"VAULT OFFLINE: Proceeding with local verification only. Error: {str(e)}"

@tool("forensic_shap_scanner")
def forensic_shap_scanner(image_path: str) -> str:
    """
    Simulates a SHAP-enhanced forgery detection model.
    Returns JSON string with MSE score and pixel-level feature attribution.
    """
    # SIMULATION: In production, this would calculate real SHAP values.
    response = {
        "forensic_metric": "MSE",
        "score": 0.45,  # High error = Forgery
        "threshold": 0.15,
        "xai_explanation": {
            "method": "SHAP (SHapley Additive exPlanations)",
            "primary_contributor": "region_header_text",
            "contribution_weight": "87%", 
            "secondary_contributor": "photo_edge_pixels",
            "contribution_weight": "12%"
        },
        "verdict": "SUSPICIOUS"
    }
    return json.dumps(response)

@tool("generate_konza_hash")
def generate_konza_hash(data: str) -> str:
    """
    Generates a SHA-256 cryptographic seal for the audit log.
    Accepts string or object input.
    """
    # Ensure data is a string before encoding
    secure_string = str(data) 
    return hashlib.sha256(secure_string.encode()).hexdigest()

@tool("document_forgery_analyzer")
def analyze_document_integrity(image_path: str):
    """
    Analyzes a document using ELA math to detect digital tampering 
    or 'photoshopped' sections like names, dates, or signatures.
    """
    score, _ = perform_ela(image_path)
    status, reason = get_forgery_judgment(score)
    
    return {
        "forgery_score": score,
        "integrity_status": status,
        "evidence": reason
    }