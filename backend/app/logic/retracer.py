import cv2
import numpy as np

class AdaptiveRetracer:
    @staticmethod
    def detect_blur(image):
        """Calculates the Laplacian variance to measure focus."""
        # Handle grayscale images
        if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1):
            gray = image  # Already grayscale
        elif len(image.shape) == 3 and image.shape[2] == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        return cv2.Laplacian(gray, cv2.CV_64F).var()

    @staticmethod
    def sharpen_document(image):
        """
        Applies a sharpening kernel to 'retrace' edges 
        lost to motion blur or low-res sensors.
        """
        # A 3x3 sharpening kernel (The 'Retracing' Filter)
        kernel = np.array([[-1, -1, -1], 
                           [-1,  9, -1], 
                           [-1, -1, -1]])
        
        sharpened = cv2.filter2D(image, -1, kernel)
        
        # Increase contrast for OCR readability
        sharpened = cv2.convertScaleAbs(sharpened, alpha=1.2, beta=10)
        
        return sharpened

def process_guardrail(image_path):
    img = cv2.imread(image_path)
    blur_score = AdaptiveRetracer.detect_blur(img)
    
    # Threshold for 'Actionable Blur' (reduced from 100 to 50 for better sensitivity)
    if blur_score < 50:
        print(f"[Loop Closure] Blurry image detected ({blur_score}). Retracing...")
        img = AdaptiveRetracer.sharpen_document(img)
        # Save the 'Retraced' version for the OCR model
        cv2.imwrite(image_path, img)
        return True, "Retraced"
    
    return False, "Clear"
    # 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