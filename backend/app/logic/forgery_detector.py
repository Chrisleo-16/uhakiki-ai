import torch
import torch.nn as nn
from app.models.autoencoder import DocumentAutoencoder

# 1. Initialize the RAD (Reconstruction Anomaly Detector) Engine
# We do this at the module level so it loads into memory once.
model = DocumentAutoencoder()
model.eval()

def calculate_forgery_score(image_tensor: torch.Tensor):
    """
    The Core Neural Guardrail:
    Calculates the Reconstruction Residual (MSE Loss).
    
    If the document has been digitally altered, the Autoencoder 
    will fail to reconstruct the pixels, resulting in a high score.
    """
    with torch.no_grad():
        # Pass the image through the 'Eyes'
        reconstruction = model(image_tensor)
        
        # MSE Loss = (Original - Reconstructed)^2
        # It measures the 'energy' of the difference between pixels.
        loss_function = nn.MSELoss()
        mse_loss = loss_function(reconstruction, image_tensor)
        
        # Threshold tau = 0.05 (Dynamic limit for forgery)
        # Any residual above this means the document signal is synthetic or modified.
        mse_value = float(mse_loss.item())
        is_forgery = mse_value > 0.05
        
        return mse_value, is_forgery