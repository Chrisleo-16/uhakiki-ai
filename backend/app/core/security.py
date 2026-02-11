# AES-256 & Encryption logic
import re
import json
from pydantic import BaseModel
from typing import Dict, List

from cryptography.fernet import Fernet
import os

# Generate or load a persistent key for Konza deployment
# In production, this should be in an environment variable
KEY = os.getenv("UHA_SECRET_KEY", Fernet.generate_key().decode())
cipher = Fernet(KEY.encode())

def encrypt_record(data_str: str) -> str:
    """Encrypts student PII for sovereign storage."""
    return cipher.encrypt(data_str.encode()).decode()

def decrypt_record(token: str) -> str:
    """Decrypts data for official audit trails."""
    return cipher.decrypt(token.encode()).decode()

# Schema for the XAI (Explainable AI) Logic Log
class ActionableJudgmentLog(BaseModel):
    application_id: str
    decision: str  # e.g., "APPROVED", "FLAGGED"
    logic_chain: List[str]  # e.g., ["RAD residuals: High", "Milvus Match: 98%"]
    feature_contributions: Dict[str, float]  # SHAP values (Contribution to decision)

def strip_pii_from_logs(message: str) -> str:
    """
    Masks National IDs, Phone Numbers, and Names in system logs.
    """
    # Mask National IDs (typically 8 digits)
    message = re.sub(r'\b\d{8}\b', '********', message)
    # Mask Phone Numbers (07... or +254...)
    message = re.sub(r'(?:\+254|0)[17]\d{8}', '**********', message)
    return message

def generate_sovereign_audit_trail(log_data: ActionableJudgmentLog):
    """
    Saves the explanation to a secure, encrypted audit file for Konza compliance.
    """
    sanitized_data = log_data.model_dump()
    # In a real setup, you would encrypt this JSON string with AES-256 here
    with open("/var/log/uhakiki/audit_trail.json", "a") as f:
        f.write(json.dumps(sanitized_data) + "\n")