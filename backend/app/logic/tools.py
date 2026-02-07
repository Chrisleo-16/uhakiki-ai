from crewai.tools.base_tool import BaseTool, tool
from app.logic.verification_service import VerificationService
from pymilvus import Collection, connections

# Initialize the Phase 2 Brain (The RAD Engine)
# We load it here once so it stays in memory for the agents
verifier = VerificationService()

@tool("forgery_scan_tool")
def forgery_scan_tool(image_path: str) -> str:
    """
    Analyzes the pixel structure of a document ID to detect digital manipulation.
    Input should be a string path to the image file.
    """
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
    try:
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
        return f"VAULT ERROR: {str(e)}"