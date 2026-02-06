import torch
import time
import numpy as np
from PIL import Image
from torchvision import transforms
from .rad_model import RADAutoencoder
from .guardrail import validate_input_quality
from pymilvus import Collection, connections

class VerificationService:
    def __init__(self, model_path="backend/app/models/rad_v1.pth"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = RADAutoencoder().to(self.device)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()
        
        # Preprocessing for the Neural Engine (224x224 as per specs)
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.Grayscale(num_output_channels=1), # <--- ADD THIS LINE
            transforms.ToTensor(),
            # Normalize for 1 channel instead of 3
            transforms.Normalize(mean=[0.5], std=[0.5]) 
        ])

    def verify(self, image_path):
        start_time = time.time()

        # STEP 1: Guardrail (OODA: Observe)
        is_valid, message = validate_input_quality(image_path)
        if not is_valid:
            return {"status": "Rejected", "reason": message, "latency_ms": (time.time() - start_time)*1000}

        # STEP 2: Neural Reconstruction (OODA: Orient)
        img = Image.open(image_path).convert('L')
        input_tensor = self.transform(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            reconstructed = self.model(input_tensor)
            
            # MATH: Forgery Residual Scoring (x_i - x_hat_i)
            # We calculate Mean Squared Error (MSE) as the 'Residual Score'
            residual_matrix = torch.abs(input_tensor - reconstructed)
            residual_score = torch.mean(residual_matrix).item()
            
            # Generate the 128D Fingerprint for the Vault
            fingerprint = self.model.encoder(input_tensor).cpu().numpy().flatten()

        # STEP 3: Threshold Decision (Phase 2 Specs)
        # Dynamic threshold tau: If residual > 0.15, document is a 'Reconstruction Failure' (Forgery)
        tau = 0.15 
        is_forgery = residual_score > tau

        latency = (time.time() - start_time) * 1000
        
        return {
            "status": "Flagged" if is_forgery else "Verified",
            "residual_score": round(residual_score, 4),
            "threshold": tau,
            "fingerprint": fingerprint.tolist()[:5], # Returning snippet for verification
            "latency_ms": round(latency, 2),
            "sovereign_shield": "Active"
        }