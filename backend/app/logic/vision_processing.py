import cv2
import numpy as np

def check_input_quality(image_bytes):
    """
    Input Quality Guardrail:
    Ensures the document is sharp and high-resolution enough for analysis.
    Uses Laplacian variance to measure sharpness (Gradient Magnitude).
    """
    # Convert bytes to OpenCV format
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    
    if img is None:
        return False, "Invalid image format"

    # 1. Resolution Check
    height, width = img.shape
    if height < 800 or width < 800:
        return False, f"Low resolution: {width}x{height}. Minimum 800x800 required."

    # 2. Sharpness Check (Laplacian Variance)
    # Authentic docs are crisp; blurry uploads hide forgery patterns.
    sharpness_score = cv2.Laplacian(img, cv2.CV_64F).var()
    
    # Threshold for a 'legible' document is typically > 100
    if sharpness_score < 100:
        return False, f"Image too blurry (Score: {round(sharpness_score, 2)}). Please re-scan."

    return True, "Quality passed"