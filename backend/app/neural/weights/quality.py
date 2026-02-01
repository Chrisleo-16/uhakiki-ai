import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

def assess_document_integrity(image_path):
    """
    Checks if the document is sharp enough and has consistent structure.
    """
    # Load image in grayscale
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return False, "Could not read document file."

    # 1. Gradient Magnitude Check (Blurriness)
    # We use the Laplacian variance; lower than 100 usually means it's too blurry.
    score = cv2.Laplacian(img, cv2.CV_64F).var()
    
    if score < 100:
        return False, f"Document too blurry (Score: {score:.2f}). Please re-upload."

    # 2. Basic Noise Check (Pixel Residuals)
    # Checks if the image is mostly 'flat' or contains too much digital noise
    noise_level = np.std(img)
    if noise_level < 5:
        return False, "Image lacks sufficient detail (possible solid color or blank)."

    return True, "Quality Verified. Proceeding to OODA Analysis."