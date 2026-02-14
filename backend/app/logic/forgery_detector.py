import torch
import torch.nn as nn
import numpy as np
import os
from PIL import Image, ImageChops
from torchvision import transforms
from .rad_model import RADAutoencoder
from ..models.model_loader import model_manager

# 1. SETUP & MODEL LOADING
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Use centralized model manager
def get_model():
    """Get RAD model from centralized model manager"""
    return model_manager.load_rad_autoencoder()

# Standardize image for the Neural Network (RAD)
preprocess = transforms.Compose([
    transforms.Resize((224, 224)),  # Match RAD input size
    transforms.ToTensor(),
])

# 2. MASTER API FUNCTIONS
# Define the Forensic Vault directories
BASE_FORENSIC_DIR = "backend/data/forensics"
os.makedirs(f"{BASE_FORENSIC_DIR}/original", exist_ok=True)
os.makedirs(f"{BASE_FORENSIC_DIR}/ela", exist_ok=True)
os.makedirs(f"{BASE_FORENSIC_DIR}/rad", exist_ok=True)

def perform_ela_and_save(image_path, save_path, quality=90):
    original = Image.open(image_path).convert('RGB')
    temp_resaved = 'temp_resaved.jpg'
    original.save(temp_resaved, 'JPEG', quality=quality)
    resaved = Image.open(temp_resaved)
    
    # Calculate difference
    diff = ImageChops.difference(original, resaved)
    
    # Enhance contrast so the forgery 'glows'
    extrema = diff.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    scale = 255.0 / max_diff if max_diff != 0 else 1
    diff_enhanced = ImageChops.multiply(diff, ImageChops.constant(diff, int(scale)))
    
    diff_enhanced.save(save_path)
    os.remove(temp_resaved)
    return np.mean(np.array(diff)) / 255.0

async def detect_pixel_anomalies(upload_file):
    """
    Orchestrates forensic scan and saves visual artifacts for the Dashboard.
    """
    file_extension = upload_file.filename.split('.')[-1]
    # Use a clean filename for the internal vault
    clean_name = upload_file.filename.replace(f".{file_extension}", "")
    
    # Paths for visual evidence
    orig_path = f"{BASE_FORENSIC_DIR}/original/{upload_file.filename}"
    ela_viz_path = f"{BASE_FORENSIC_DIR}/ela/{clean_name}_ela.jpg"
    rad_viz_path = f"{BASE_FORENSIC_DIR}/rad/{clean_name}_recon.jpg"

    # Save the original for the 'Before/After' view
    content = await upload_file.read()
    with open(orig_path, "wb") as f:
        f.write(content)

    try:
        # A. ELA Logic & Visual Generation
        # We modify perform_ela to also save the difference map
        ela_score = perform_ela_and_save(orig_path, ela_viz_path)
        ela_status, _ = get_forgery_judgment(ela_score)

        # B. Neural Logic & Reconstruction Save
        img = Image.open(orig_path).convert('RGB')
        img_tensor = preprocess(img).unsqueeze(0).to(DEVICE)
        
        # Get score and the actual reconstructed image
        mse_score, is_rad_forgery = calculate_forgery_score(img_tensor)
        recon_tensor = get_reconstruction(img_tensor)
        
        # Save the RAD reconstruction visual
        recon_img = transforms.ToPILImage()(recon_tensor.squeeze(0).cpu())
        recon_img.save(rad_viz_path)

        combined_score = (ela_score * 0.7) + (mse_score * 0.3)
        
        return {
            "forgery_probability": round(combined_score, 4),
            "ela_status": ela_status,
            "neural_anomaly": "DETECTED" if is_rad_forgery else "CLEAN",
            "judgment": "FORGED" if (combined_score > 0.05 or is_rad_forgery) else "AUTHENTIC",
            "visuals": {
                "original": orig_path,
                "ela_map": ela_viz_path,
                "reconstruction": rad_viz_path
            }
        }
    except Exception as e:
        print(f"Forensic Error: {e}")
        return {"error": str(e)}

def get_reconstruction(img_tensor):
    """
    REQUIRED BY secure_ingest.py: 
    Returns the decoded image from the Autoencoder to visualize anomalies.
    """
    model = get_model()
    img_tensor = img_tensor.to(DEVICE)
    with torch.no_grad():
        return model(img_tensor)

def calculate_forgery_score(img_tensor):
    """
    REQUIRED BY secure_ingest.py:
    Computes the Mean Squared Error between input and reconstruction.
    """
    model = get_model()
    img_tensor = img_tensor.to(DEVICE)
    with torch.no_grad():
        reconstruction = model(img_tensor)
        loss_fn = nn.MSELoss()
        mse = loss_fn(img_tensor, reconstruction).item()
    
    # Return both the score and a boolean (threshold at 0.025)
    return mse, mse > 0.025

# 3. SUPPORTING UTILITIES
def perform_ela(image_path, quality=90):
    original = Image.open(image_path).convert('RGB')
    resaved_path = 'temp_ela_resave.jpg'
    original.save(resaved_path, 'JPEG', quality=quality)
    resaved = Image.open(resaved_path)
    
    diff = ImageChops.difference(original, resaved)
    extrema = diff.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    scale = 255.0 / max_diff if max_diff != 0 else 1
    
    return np.mean(np.array(diff)) * scale / 255.0

def get_forgery_judgment(score):
    if score < 0.02: return "AUTHENTIC", "Uniform"
    if score < 0.08: return "SUSPICIOUS", "Inconsistent"
    return "FORGED", "High Variance"