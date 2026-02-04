import torch
import cv2
import numpy as np
from PIL import Image

def generate_residual_heatmap(original_tensor, reconstruction_tensor, output_path="residual_map.png"):
    """
    Computes the absolute difference between original and reconstruction.
    High differences (forgeries) are highlighted as 'Hot' spots.
    """
    # 1. Calculate Absolute Difference
    # We use .squeeze() to remove batch dimensions
    diff = torch.abs(original_tensor - reconstruction_tensor).squeeze().cpu().numpy()
    
    # 2. Normalize to 0-255 for OpenCV
    diff_normalized = (diff * 255).astype(np.uint8)
    
    # 3. Apply a Color Map (JET or HOT looks best for security)
    heatmap = cv2.applyColorMap(diff_normalized, cv2.COLORMAP_JET)
    
    # 4. Save the "Evidence"
    cv2.imwrite(output_path, heatmap)
    return output_path