import os
import psutil
from crewai import Agent, Task, Crew, Process, LLM 
from backend.app.logic.tools import forgery_scan_tool, vault_search_tool

def get_sovereign_brain():
    """
    DYNAMIC ALLOCATION:
    Checks available RAM and selects the best model that won't crash the system.
    """
    # Get available memory in GB
    stats = psutil.virtual_memory()
    available_gb = stats.available / (1024 ** 3)
    
    print(f"📊 [SYSTEM] Available RAM: {available_gb:.2f} GB")

    # Selection Logic
    if available_gb > 4.5:
        model_name = "openai/phi3:mini"
        tier = "GOLD (Phi3)"
    # elif available_gb > 2.2:
    #     model_name = "openai/llama3.2:1b"
    #     tier = "SILVER (Llama3.2)"
    else:
        model_name = "openai/qwen2:0.5b"
        tier = "BRONZE (Qwen2)"

    print(f"🧠 [BRAIN] Resource Tier: {tier} selected.")
    
    return LLM(
        model=model_name,
        base_url="http://localhost:11434/v1",
        api_key="NA"
    )

class SecurityCouncil:
    def __init__(self):
        self.forgery_tool = forgery_scan_tool
        self.vault_tool = vault_search_tool
        # The brain is chosen at the moment the Council is initialized
        self.llm = get_sovereign_brain()

    def run_council(self, image_path, national_id):
        print(f"🏛️  [COUNCIL] Analyzing ID: {national_id}")

        # 1. THE INVESTIGATOR
        investigator = Agent(
            role='Forensic Investigator',
            goal=f'Scan {image_path} for forgery.',
            backstory="Expert in digital image forensics.",
            tools=[self.forgery_tool],
            llm=self.llm,
            allow_delegation=False,
            verbose=True
        )

        # 2. THE AUDITOR
        auditor = Agent(
            role='Sovereign Vault Auditor',
            goal=f'Search for ID {national_id} in the database.',
            backstory="Keeper of historical records.",
            tools=[self.vault_tool],
            llm=self.llm,
            allow_delegation=False,
            verbose=True
        )

        # 3. THE ENFORCER
        enforcer = Agent(
            role='Disbursement Enforcer',
            goal='Output final decision: APPROVED or BLOCKED.',
            backstory="The final authority on transaction legitimacy.",
            llm=self.llm,
            allow_delegation=False,
            verbose=True
        )

        # --- TASKS ---
        task1 = Task(
            description=f"Analyze '{image_path}' using forgery_scan_tool.",
            expected_output="Forensic report with MSE value.",
            agent=investigator
        )

        task2 = Task(
            description=f"Check if ID '{national_id}' exists in vault.",
            expected_output="Status: CLEAN or DUPLICATE.",
            agent=auditor
        )

        task3 = Task(
            description=(
                "CRITICAL: Look at the results from the Investigator (MSE) and Auditor (Status). "
                "1. If MSE is higher than 0.15, you MUST say 'Outcome: BLOCKED'. "
                "2. If status is 'DUPLICATE', you MUST say 'Outcome: BLOCKED'. "
                "3. Otherwise, say 'Outcome: APPROVED'. "
                "Do not explain. Just provide the final outcome."
            ),
            expected_output="Final Verdict: [APPROVED or BLOCKED] based on the specific MSE and Vault values provided.",
            agent=enforcer,
            context=[task1, task2] 
        )

        council_crew = Crew(
            agents=[investigator, auditor, enforcer],
            tasks=[task1, task2, task3],
            process=Process.sequential,
            verbose=True
        )

        result = council_crew.kickoff()
        
        os.makedirs("backend/audit_logs", exist_ok=True)
        return result, "backend/audit_logs/council_verdict.txt"