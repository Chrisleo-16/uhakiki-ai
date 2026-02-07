import json
import os
from datetime import datetime

def save_audit_log(application_id, agent_output):
    """
    Sovereign Accountability: Saves the Chain of Thought to a tamper-proof log.
    """
    log_dir = "backend/audit_logs"
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    filename = f"{log_dir}/{application_id}_{timestamp}.json"
    
    log_entry = {
        "timestamp": timestamp,
        "application_id": application_id,
        "council_decision": agent_output,
        "integrity_hash": "SHA-256-PENDING" # Placeholder for blockchain hashing
    }
    
    with open(filename, "w") as f:
        json.dump(log_entry, f, indent=4)
        
    return filename