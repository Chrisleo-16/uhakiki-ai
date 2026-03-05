"""
Image Utility Functions
Ensures consistent image format across the application
"""
import cv2
import numpy as np

def ensure_bgr_image(image: np.ndarray) -> np.ndarray:
    """
    Ensure the image is in BGR format (3 channels).
    Handles grayscale, RGBA, and other formats.
    
    Args:
        image: Input image in any format
        
    Returns:
        Image in BGR format (3 channels)
    """
    if image is None:
        return None
    
    # Already grayscale (2D array)
    if len(image.shape) == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    
    # Has 1 channel (single channel color)
    if len(image.shape) == 3 and image.shape[2] == 1:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    
    # Has 4 channels (RGBA)
    if len(image.shape) == 3 and image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    
    # Already BGR
    if len(image.shape) == 3 and image.shape[2] == 3:
        return image
    
    # Fallback - try to convert
    try:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    except:
        return image


def ensure_gray_image(image: np.ndarray) -> np.ndarray:
    """
    Ensure the image is in grayscale format (single channel).
    
    Args:
        image: Input image in any format
        
    Returns:
        Image in grayscale format
    """
    if image is None:
        return None
    
    # Already grayscale
    if len(image.shape) == 2:
        return image
    
    # Has 1 channel
    if len(image.shape) == 3 and image.shape[2] == 1:
        return image.squeeze()
    
    # Has 3 channels (BGR)
    if len(image.shape) == 3 and image.shape[2] == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Has 4 channels (RGBA)
    if len(image.shape) == 3 and image.shape[2] == 4:
        gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        return gray
    
    # Fallback
    return image


def decode_image_safe(image_data: bytes) -> np.ndarray:
    """
    Safely decode image data to BGR format.
    
    Args:
        image_data: Raw image bytes
        
    Returns:
        Image in BGR format (3 channels)
    """
    nparr = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        # Try loading as grayscale and convert
        image = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        if image is not None:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    
    return ensure_bgr_image(image)
