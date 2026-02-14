import os
import psutil
import json
from datetime import datetime
from crewai import Agent, Task, Crew, Process, LLM
from .tools import forgery_scan_tool, vault_search_tool
from .qr_system import generate_student_qr

def get_sovereign_brain():
    stats = psutil.virtual_memory()
    available_gb = stats.available / (1024 ** 3)
    
    # Selection Logic for Konza Cloud efficiency
    if available_gb > 4.5:
        model_name, tier = "openai/phi3:mini", "GOLD (Phi3)"
    else:
        model_name, tier = "openai/qwen2:0.5b", "BRONZE (Qwen2)"

    return LLM(
        model=model_name,
        base_url="http://localhost:11434/v1",
        api_key="NA"
    )

class SecurityCouncil:
    def __init__(self):
        self.llm = get_sovereign_brain()
        self.audit_dir = "backend/data/logs"
        os.makedirs(self.audit_dir, exist_ok=True)

    def _generate_xai_log(self, student_id, result_raw):
        """Internal helper to save the XAI Audit Log (DPA 2019 Compliance)"""
        log_path = os.path.join(self.audit_dir, f"audit_{student_id}.json")
        
        log_data = {
            "metadata": {
                "student_id": student_id,
                "timestamp": datetime.now().isoformat(),
                "node": "KNDC-SEC-COUNCIL-01"
            },
            "decision_engine_output": str(result_raw),
            "status": "APPROVED" if "APPROVED" in str(result_raw).upper() else "BLOCKED"
        }
        
        with open(log_path, "w") as f:
            json.dump(log_data, f, indent=4)
        return log_data

    def run_council(self, image_path, national_id):
        print(f"🏛️  [COUNCIL] Sovereign Audit Initiated for: {national_id}")

        # 1. THE AGENTS (Investigator, Auditor, Enforcer)
        investigator = Agent(
            role='Forensic Investigator',
            goal='Analyze document for pixel-level anomalies.',
            backstory="Specialized in ELA and Neural Reconstruction math.",
            tools=[forgery_scan_tool],
            llm=self.llm,
            verbose=True
        )

        auditor = Agent(
            role='Vault Auditor',
            goal='Ensure ID uniqueness in the Sovereign Vault.',
            backstory="Enforces 'One Person, One Grant' policy.",
            tools=[vault_search_tool],
            llm=self.llm,
            verbose=True
        )

        enforcer = Agent(
            role='Disbursement Enforcer',
            goal='Issue final verdict based on forensic and vault data.',
            backstory="The final gatekeeper for KNDC digital assets.",
            llm=self.llm,
            verbose=True
        )

        # 2. THE TASKS (Context-Aware Pipeline)
        task_scan = Task(
            description=f"Scan {image_path} using forgery_scan_tool.",
            expected_output="Forensic report (MSE/ELA values).",
            agent=investigator
        )

        task_vault = Task(
            description=f"Check {national_id} in vault_search_tool.",
            expected_output="Vault Status (CLEAN/DUPLICATE).",
            agent=auditor
        )

        task_verdict = Task(
            description=(
                "Final Decision Protocol:\n"
                "1. If Investigator MSE > 0.15 or Auditor Status is DUPLICATE -> 'Outcome: BLOCKED'.\n"
                "2. Else -> 'Outcome: APPROVED'.\n"
                "State only the Outcome and a 1-sentence reason."
            ),
            expected_output="Final Verdict: [APPROVED/BLOCKED] with 1-sentence reasoning.",
            agent=enforcer,
            context=[task_scan, task_vault]
        )

        # 3. THE KICKOFF
        council_crew = Crew(
            agents=[investigator, auditor, enforcer],
            tasks=[task_scan, task_vault, task_verdict],
            process=Process.sequential,
            output_log_file=os.path.join(self.audit_dir, f"raw_log_{national_id}.txt"),
            verbose=True
        )

        final_output = council_crew.kickoff()
        
        # 4. POST-PROCESSING (The 'Action' Phase)
        audit_log = self._generate_xai_log(national_id, final_output)
        
        qr_path = None
        if audit_log["status"] == "APPROVED":
            # Issue the Sovereign QR for the student's mobile app
            qr_path = generate_student_qr(national_id)

        return {
            "verdict": audit_log["status"],
            "log": audit_log,
            "qr_path": qr_path,
            "raw_reasoning": final_output.raw
        }
    