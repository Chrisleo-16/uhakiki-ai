# Digital Inspector for our code
import hashlib
import os
import sys

# Path setup
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
VAULT_DIR = os.path.join(BASE_DIR, "backend/data/konza_vault")

def verify_log(filename):
    # Construct absolute path to the specific log file
    log_path = os.path.join(VAULT_DIR, filename)
    
    if not os.path.exists(log_path):
        print(f"❌ Error: Could not find file at: {log_path}")
        print(f"Current Vault directory being checked: {VAULT_DIR}")
        return

    with open(log_path, "r") as f:
        lines = f.readlines()

    # Extract the stored hash and the actual content
    stored_hash = ""
    decision_content = ""
    capture_content = False

    for line in lines:
        if line.startswith("HASH:") or line.startswith("SEAL_HASH:"):
            stored_hash = line.split(":")[1].strip()
        if line.startswith("--- DECISION CHAIN ---") or line.startswith("DECISION_LOG:"):
            capture_content = True
            continue
        if capture_content:
            decision_content += line

    # Re-calculate the hash from the content
    # Note: Ensure the strip() matches the logic used in generate_konza_hash
    recalculated_hash = hashlib.sha256(decision_content.strip().encode()).hexdigest()

    print(f"\n--- 🛡️  KONZA INTEGRITY CHECK ---")
    print(f"Log File: {filename}")
    print(f"Stored Seal: {stored_hash}")
    print(f"Current Hash: {recalculated_hash}")
    print("-" * 35)

    if stored_hash == recalculated_hash:
        print("✅ INTEGRITY VERIFIED: This decision has NOT been tampered with.")
    else:
        print("🚨 ALERT: INTEGRITY BREACH! The decision content has been modified.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 verify_seal.py <log_filename>")
        # List files in vault to help the user
        logs = [f for f in os.listdir(VAULT_DIR) if f.endswith(".txt") or f.endswith(".log")]
        if logs:
            print(f"\nAvailable logs in Vault: {logs}")
    else:
        verify_log(sys.argv[1])