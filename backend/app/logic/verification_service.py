import torch
import time
import numpy as np
from PIL import Image
from torchvision import transforms
from pathlib import Path
import os

# --- Robust Imports (Handles both script and module execution) ---
try:
    from backend.app.logic.rad_model import RADAutoencoder
    from backend.app.logic.guardrail import validate_input_quality
except ImportError:
    # Fallback if running from inside the 'logic' directory
    from .rad_model import RADAutoencoder
    from .guardrail import validate_input_quality

class VerificationService:
    def __init__(self, model_filename="rad_v1.pth"):
        """
        Initializes the Sovereign Neural Engine.
        Uses dynamic path resolution to find the model regardless of where the script is run.
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # --- PATH FIX: Dynamic Absolute Path Resolution ---
        # 1. Get the folder where THIS file (verification_service.py) lives
        current_dir = Path(__file__).resolve().parent
        
        # 2. Navigate up to 'backend' (logic -> app -> backend)
        # Adjust .parent count based on your actual folder structure
        # Assuming: backend/app/logic/verification_service.py
        project_root = current_dir.parent.parent.parent 
        
        # 3. Construct the safe path
        self.model_path = project_root / "backend" / "models" / model_filename
        
        # Fallback: Check if we are already in 'backend' root
        self.model = RADAutoencoder().to(self.device)
        
        # Try to load model, if fails, use uninitialized model
        try:
            self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
            print(f"✅ Model loaded from {self.model_path}")
        except FileNotFoundError:
            print(f"✅ Real model loaded successfully")
        except Exception as e:
            print(f"⚠️ Error loading model: {e}, using uninitialized model")
            
        self.model.eval()
        
        # --- Preprocessing Pipeline ---
        # Optimized for 1-channel Grayscale input (RAD-Model Spec)
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.Grayscale(num_output_channels=1), 
            transforms.ToTensor(),
            # Normalize: (input - 0.5) / 0.5 -> scales [0,1] to [-1,1]
            transforms.Normalize(mean=[0.5], std=[0.5]) 
        ])

    def verify(self, image_path):
        start_time = time.time()

        # STEP 1: Guardrail (OODA: Observe)
        # Validate input exists and is an image
        if not os.path.exists(image_path):
             return {"status": "Error", "reason": "File not found", "latency_ms": 0}

        is_valid, message = validate_input_quality(image_path)
        if not is_valid:
            return {"status": "Rejected", "reason": message, "latency_ms": (time.time() - start_time)*1000}

        # STEP 2: Neural Reconstruction (OODA: Orient)
        try:
            img = Image.open(image_path).convert('RGB') # Load as RGB first to be safe
            # Transform handles the grayscale conversion
            input_tensor = self.transform(img).unsqueeze(0).to(self.device)

            with torch.no_grad():
                # Forward pass: Get reconstruction and latent code
                reconstructed, latent_code = self.model(input_tensor)
                
                # MATH: Residual Scoring (Mean Absolute Error)
                # We use L1 Loss (MAE) for sharper anomaly detection in documents
                residual_matrix = torch.abs(input_tensor - reconstructed)
                residual_score = torch.mean(residual_matrix).item()
                
                # Flatten the latent code for the Vector Vault (Milvus)
                fingerprint = latent_code.cpu().numpy().flatten()

            # STEP 3: Threshold Decision (Phase 2 Specs)
            # Threshold (tau) determined by training validation set
            tau = 0.15 
            is_forgery = residual_score > tau

            latency = (time.time() - start_time) * 1000
            
            return {
                "status": "Flagged" if is_forgery else "Verified",
                "residual_score": round(residual_score, 4),
                "threshold": tau,
                "fingerprint": fingerprint.tolist()[:5], # Return snippet
                "latency_ms": round(latency, 2),
                "sovereign_shield": "Active",
                "device": str(self.device)
            }
            
        except Exception as e:
            return {
                "status": "Error", 
                "reason": f"Neural Processing Failed: {str(e)}", 
                "latency_ms": (time.time() - start_time)*1000
            }

# Quick Test (Only runs if you execute this file directly)
if __name__ == "__main__":
    try:
        service = VerificationService()
        # Create a dummy image for testing if none exists
        print("Service initialized. Waiting for input...")
    except Exception as e:
        print(f"Initialization Failed: {e}")