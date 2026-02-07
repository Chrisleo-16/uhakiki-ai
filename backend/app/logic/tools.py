import json
import hashlib
import sys
import os

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
    Checks the Sovereign Milvus Vault to see if this National ID has been used before.
    Input should be the 8-digit National ID string.
    """
    if not MILVUS_AVAILABLE:
        return "VAULT ERROR: Milvus library not installed."

    try:
        # Connect to Milvus (Ensure Docker container is running)
        connections.connect(host="localhost", port="19530")
        collection = Collection("sovereign_vault")
        collection.load()
        
        # Scalar search for the ID
        res = collection.query(
            expr=f"national_id == '{national_id}'",
            output_fields=["national_id"],
            limit=1
        )
        
        if res:
            return f"VAULT ALERT: Identity {national_id} already exists. Potential DUPLICATE."
        return f"VAULT CLEAN: No records found for {national_id}. New applicant."
    except Exception as e:
        # Graceful failure - allows the agent to continue even if DB is down
        return f"VAULT ERROR: Could not connect to Sovereign Vault. {str(e)}"

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