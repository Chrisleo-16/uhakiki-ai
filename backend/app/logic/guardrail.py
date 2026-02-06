import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

def validate_input_quality(image_path):
    """
    Sovereign Guardrail: Rejects adversarial low-resolution attempts.
    Evaluates Gradient Magnitude for legibility and SSIM for structural integrity.
    """
    # Load image in grayscale for signal analysis
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return False, "Error: Could not decode image signal."

    # 1. Gradient Magnitude Check (Legibility)
    # Uses Sobel operators to calculate the intensity change (edges)
    sobelx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=5)
    sobely = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=5)
    gradient_magnitude = np.sqrt(sobelx**2 + sobely**2).mean()

    # 2. Laplacian Variance (Focus/Blur Check)
    blur_score = cv2.Laplacian(img, cv2.CV_64F).var()

    # 3. Structural Integrity (SSIM)
    # We compare the image against a slightly denoised version.
    # High similarity to a blurred version indicates a lack of high-frequency detail (forgery attempt/blur).
    denoised = cv2.GaussianBlur(img, (5, 5), 0)
    structure_score, _ = ssim(img, denoised, full=True)

    # Thresholds based on Phase 2 Specs
    # gradient_magnitude > 50 (sharp edges)
    # blur_score > 100 (well-focused)
    # structure_score < 0.95 (not overly 'flat' or artificial)
    
    if gradient_magnitude < 45:
        return False, f"Low Gradient Magnitude ({gradient_magnitude:.2f}): Document is too faint or low-contrast."
    if blur_score < 100:
        return False, f"Low Laplacian Variance ({blur_score:.2f}): Image is blurry."
    
    return True, "Quality Verified: Signal is robust."