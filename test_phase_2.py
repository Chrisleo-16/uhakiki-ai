from backend.app.logic.verification_service import VerificationService
import os

# Initialize Service
verifier = VerificationService()

# Simulate a Test Upload
test_image = "sample_id.jpg" # Ensure a sample exists
if os.path.exists(test_image):
    result = verifier.verify(test_image)
    
    print("--- UHAKIKI PHASE 2 AUDIT ---")
    print(f"Status: {result['status']}")
    print(f"Residual Score (MSE): {result['residual_score']}")
    print(f"Inference Latency: {result['latency_ms']}ms")
    
    # Audit Success Criteria
    if result['latency_ms'] < 500:
        print("✅ LATENCY CRITERIA: PASSED")
    else:
        print("❌ LATENCY CRITERIA: FAILED (System too slow)")
else:
    print("⚠️ Please place a 'sample_id.jpg' in the directory to run the audit.")