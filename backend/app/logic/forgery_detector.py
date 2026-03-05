import torch
import torch.nn as nn
import numpy as np
import os
import json
from PIL import Image, ImageChops, ImageFilter
from torchvision import transforms
from .rad_model import RADAutoencoder
# from ..models.model_loader import model_manager  # Commented out to avoid circular import

# 1. SETUP & MODEL LOADING
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Default thresholds (generic model)
DEFAULT_MSE_THRESHOLD = 0.025
DEFAULT_ELA_THRESHOLD = 0.05

# Load Kenyan-specific configuration if available
KENYAN_CONFIG_PATH = "backend/models/kenyan_threshold_config.json"
KENYAN_MODEL_PATH = "backend/models/rad_autoencoder_kenyan.pth"

def load_kenyan_config():
    """Load Kenyan-specific threshold configuration"""
    if os.path.exists(KENYAN_CONFIG_PATH):
        try:
            with open(KENYAN_CONFIG_PATH, 'r') as f:
                config = json.load(f)
            print(f"Loaded Kenyan threshold config: {config.get('threshold')}")
            return config
        except Exception as e:
            print(f"Failed to load Kenyan config: {e}")
    return None

# Check for Kenyan configuration
kenyan_config = load_kenyan_config()

# Use centralized model manager
def get_model():
    """Get RAD model - tries Kenyan model first, then falls back to generic"""
    try:
        # Try to load Kenyan-specific model first
        if os.path.exists(KENYAN_MODEL_PATH):
            model = RADAutoencoder().to(DEVICE)
            checkpoint = torch.load(KENYAN_MODEL_PATH, map_location=DEVICE)
            model.load_state_dict(checkpoint.get('model_state_dict', checkpoint))
            print("Loaded Kenyan-customized RAD model")
            return model
        
        # Try to use model manager if available
        from backend.models.model_loader import model_manager
        return model_manager.load_rad_autoencoder()
    except ImportError:
        # Fallback to direct model loading
        return RADAutoencoder().to(DEVICE)

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
    Uses adaptive thresholds for Kenyan IDs when configured.
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

        # Determine adaptive threshold for judgment
        if kenyan_config and 'threshold' in kenyan_config:
            adaptive_threshold = kenyan_config['threshold']
            combined_threshold = (ela_score * 0.7) + (adaptive_threshold * 0.3 * 100)  # Scale MSE
            is_forged = (combined_threshold > 0.05 or is_rad_forgery)
            model_type = "kenyan_customized"
        else:
            combined_score = (ela_score * 0.7) + (mse_score * 0.3)
            is_forged = (combined_score > 0.05 or is_rad_forgery)
            model_type = "generic"
        
        # Assess image quality
        quality_score, is_blurry = assess_image_quality(orig_path)
        
        # Adjust judgment if image is blurry (common for real photos)
        if is_blurry and quality_score < 30:
            # Lower confidence for blurry images but don't auto-fail
            judgment = "NEEDS_BETTER_IMAGE" if is_forged else "AUTHENTIC"
            message = "Image is blurry. Please retake with better lighting."
        else:
            judgment = "FORGED" if is_forged else "AUTHENTIC"
            message = "Document appears authentic" if not is_forged else "Document appears to be forged"
        
        return {
            "forgery_probability": round(combined_score if model_type == "generic" else (ela_score * 0.7 + mse_score * 0.3), 4),
            "ela_status": ela_status,
            "neural_anomaly": "DETECTED" if is_rad_forgery else "CLEAN",
            "judgment": judgment,
            "message": message,
            "mse_score": mse_score,
            "quality_score": quality_score,
            "is_blurry": is_blurry,
            "model_type": model_type,
            "adaptive_threshold": kenyan_config.get('threshold') if kenyan_config else DEFAULT_MSE_THRESHOLD,
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
    Uses adaptive threshold for Kenyan IDs if configured.
    """
    model = get_model()
    img_tensor = img_tensor.to(DEVICE)
    with torch.no_grad():
        reconstruction = model(img_tensor)
        loss_fn = nn.MSELoss()
        mse = loss_fn(img_tensor, reconstruction).item()
    
    # Use adaptive threshold if Kenyan config exists, otherwise use default
    if kenyan_config and 'threshold' in kenyan_config:
        threshold = kenyan_config['threshold']
        print(f"Using Kenyan adaptive threshold: {threshold}")
    else:
        threshold = DEFAULT_MSE_THRESHOLD
    
    # Return both the score and a boolean
    return mse, mse > threshold

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

def enhance_blurry_image(image_path):
    """
    Enhance blurry images to improve detection accuracy.
    This helps when the document is captured with poor lighting or motion blur.
    """
    try:
        img = Image.open(image_path)
        
        # Apply sharpening filter
        enhanced = img.filter(ImageFilter.SHARPEN)
        enhanced = enhanced.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        
        return enhanced, True
    except Exception as e:
        print(f"Image enhancement failed: {e}")
        return None, False

def assess_image_quality(image_path):
    """
    Assess image quality and return a quality score.
    Returns (quality_score, is_blurry) where quality_score is 0-100.
    """
    try:
        img = Image.open(image_path)
        img_gray = img.convert('L')
        
        # Use Laplacian variance as blur detection
        import numpy as np
        img_array = np.array(img_gray)
        
        # Calculate Laplacian variance (higher = sharper)
        laplacian = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])
        from scipy import signal
        variance = np.var(signal.convolve2d(img_array, laplacian, mode='same'))
        
        # Normalize to 0-100 scale (empirical thresholds)
        quality_score = min(100, int(variance / 10))
        is_blurry = variance < 100
        
        return quality_score, is_blurry
    except ImportError:
        # If scipy not available, use simple variance
        try:
            img_gray = img.convert('L')
            variance = np.var(np.array(img_gray))
            quality_score = min(100, int(variance / 100))
            is_blurry = variance < 1000
            return quality_score, is_blurry
        except:
            return 50, False  # Default uncertain quality
    except Exception as e:
        print(f"Quality assessment failed: {e}")
        return 50, False