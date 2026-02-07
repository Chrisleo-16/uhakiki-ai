from backend.app.logic.council import SecurityCouncil
import os

# Set your API Key if using OpenAI/Groq (Or configure Ollama)
# os.environ["OPENAI_API_KEY"] = "sk-..." 

def main():
    print("🏛️ CONVENING THE SECURITY COUNCIL...")
    
    # Inputs (Simulating an upload)
    test_image = "sample_id.jpg"
    test_id = "12345678" # The ID on our synthetic card
    
    council = SecurityCouncil()
    decision, log_path = council.run_council(test_image, test_id)
    
    print("\n🏁 COUNCIL ADJOURNED.")
    print(f"📜 Final Verdict: {decision}")
    print(f"🗄️ Logic Log Saved: {log_path}")

if __name__ == "__main__":
    main()