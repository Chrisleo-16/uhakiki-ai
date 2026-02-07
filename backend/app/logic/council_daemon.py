import os
import sys
import time
import shutil
import json

# --- 1. SYSTEM PATH SETUP (CRITICAL) ---
# We calculate the root directory so we can import 'app' modules reliably
current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up two levels: backend/app/logic -> backend
root_dir = os.path.abspath(os.path.join(current_dir, '../../'))

if root_dir not in sys.path:
    sys.path.append(root_dir)

# --- 2. IMPORTS ---
from crewai import Agent, Task, Crew, Process, LLM
# Now we can import reliably because of the sys.path fix above
from app.logic.tools import forensic_shap_scanner, generate_konza_hash, vault_search_tool

# --- 3. CONFIGURATION ---
BASE_DATA_DIR = os.path.join(root_dir, "data/queue")
INBOX_DIR = os.path.join(BASE_DATA_DIR, "1_inbox")
PROCESSING_DIR = os.path.join(BASE_DATA_DIR, "2_processing")
APPROVED_DIR = os.path.join(BASE_DATA_DIR, "3_approved")
REJECTED_DIR = os.path.join(BASE_DATA_DIR, "3_rejected")
VAULT_DIR = os.path.join(root_dir, "data/konza_vault")

# Create directories if they don't exist
for d in [INBOX_DIR, PROCESSING_DIR, APPROVED_DIR, REJECTED_DIR, VAULT_DIR]:
    os.makedirs(d, exist_ok=True)

# --- 4. AGENT DEFINITIONS ---
# Using the lightweight model for speed
llm = LLM(model="ollama/qwen2:0.5b", base_url="http://localhost:11434")

investigator = Agent(
    role='Forensic SHAP Analyst',
    goal='Quantify forgery probability using pixel attribution.',
    backstory='You provide mathematical proof of tampering.',
    tools=[forensic_shap_scanner], 
    llm=llm,
    verbose=True,
    allow_delegation=False
)

auditor = Agent(
    role='Sovereign Auditor',
    goal='Cross-reference ID with the National Vault.',
    backstory='You ensure the ID exists and is not a duplicate.',
    tools=[vault_search_tool],
    llm=llm,
    verbose=True,
    allow_delegation=False
)

enforcer = Agent(
    role='DPA Compliance Officer',
    goal='Issue final verdict and generate the Explanation Letter.',
    backstory='You ensure Section 35 compliance by explaining the decision.',
    llm=llm,
    verbose=True,
    allow_delegation=False
)

# --- 5. OODA LOOP ENGINE ---
def process_application(filename):
    print(f"\n[OBSERVE] New signal detected: {filename}")
    
    # --- ORIENT PHASE ---
    src = os.path.join(INBOX_DIR, filename)
    processing_path = os.path.join(PROCESSING_DIR, filename)
    
    try:
        shutil.move(src, processing_path)
    except FileNotFoundError:
        print(f"⚠️  File {filename} vanished before processing.")
        return

    print(f"🔄 [ORIENT] Moved to processing queue.")

    # --- DECIDE PHASE ---
    task1 = Task(
        description=f"Analyze {filename}. Use 'forensic_shap_scanner'. Return the JSON.",
        expected_output="JSON details of forgery.",
        agent=investigator
    )

    task2 = Task(
        description=f"Check if ID in {filename} is valid. Use 'vault_search_tool'.",
        expected_output="Vault Status string.",
        agent=auditor
    )

    task3 = Task(
        description=(
            "Review SHAP score. If > 0.15, write Rejection Letter. Else, Approve. "
            "Output MUST end with: STATUS: APPROVED or STATUS: BLOCKED"
        ),
        expected_output="Letter + Final Status.",
        agent=enforcer,
        context=[task1, task2]
    )

    council = Crew(
        agents=[investigator, auditor, enforcer],
        tasks=[task1, task2, task3],
        process=Process.sequential
    )
    
    # Run the Crew
    result = council.kickoff()
    final_output = str(result)

    # --- ACT PHASE (Persistence) ---
    # 1. Konza Seal
    log_hash = generate_konza_hash.run(data=final_output)
    
    # 2. Save Log
    log_filename = f"{filename}_logic_log.txt"
    with open(os.path.join(VAULT_DIR, log_filename), "w") as f:
        f.write(f"--- KONZA SECURE LEDGER ---\n")
        f.write(f"HASH: {log_hash}\n")
        f.write(f"TIMESTAMP: {time.ctime()}\n")
        f.write(f"--- DECISION CHAIN ---\n")
        f.write(final_output)

    # 3. Final Move
    if "STATUS: BLOCKED" in final_output:
        shutil.move(processing_path, os.path.join(REJECTED_DIR, filename))
        print(f"🛑 [ACT] BLOCKED. Log sealed in Vault.")
    else:
        shutil.move(processing_path, os.path.join(APPROVED_DIR, filename))
        print(f"✅ [ACT] APPROVED. Log sealed in Vault.")

# --- 6. DAEMON MAIN LOOP ---
if __name__ == "__main__":
    print(f"🏛️  SECURITY COUNCIL DAEMON ONLINE")
    print(f"   - Inbox: {INBOX_DIR}")
    print(f"   - Vault: {VAULT_DIR}")
    print("👀 Waiting for applications...")

    try:
        while True:
            # Filter for files (ignore hidden system files)
            files = [f for f in os.listdir(INBOX_DIR) if not f.startswith('.')]
            
            if files:
                for file in files:
                    process_application(file)
            else:
                # Idle wait
                time.sleep(2)
    except KeyboardInterrupt:
        print("\n👋 Shutting down Security Council.")