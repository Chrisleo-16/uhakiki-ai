import torch
import cv2
import numpy as np
from PIL import Image

def generate_residual_heatmap(original_tensor, reconstructed_tensor, output_path):
    """
    Generates a 'Jet' colormap showing exactly where the forgery is.
    Red = High Error (Fake), Blue = Low Error (Authentic).
    """
    # 1. Move to CPU and convert to Numpy
    orig = original_tensor.squeeze().cpu().numpy()
    recon = reconstructed_tensor.squeeze().cpu().numpy()
    
    # 2. Calculate Absolute Difference (Residual)
    # Formula: |x_i - x_hat_i|
    diff = np.abs(orig - recon)
    
    # 3. Normalize to 0-255 for OpenCV
    # We amplify small errors so they are visible to the human eye
    diff = (diff * 255).astype(np.uint8)
    diff = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)
    
    # 4. Apply 'Jet' Colormap (Blue to Red)
    heatmap = cv2.applyColorMap(diff, cv2.COLORMAP_JET)
    
    # 5. Save Evidence
    cv2.imwrite(output_path, heatmap)
    
    return output_path