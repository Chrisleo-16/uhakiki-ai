import torch
import torch.nn as nn
from app.logic.rad_model import RADAutoencoder
import os

# 1. SETUP DEVICE (GPU OPTIMIZATION)
# This ensures sub-500ms speeds on Konza Cloud
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 2. LOAD MODEL
model = RADAutoencoder().to(DEVICE)
model.eval() # Set to inference mode

# 3. DYNAMIC THRESHOLD LOGIC
# In a real training loop, you calculate this from the mean + 2*std_dev of the training set.
# For the demo, we default to a strict value, but allow it to be loaded.
DYNAMIC_THRESHOLD = float(os.getenv("RAD_THRESHOLD", "0.025")) 

def calculate_forgery_score(img_tensor):
    """
    Computes the Mean Squared Error (MSE) between input and reconstruction.
    Returns: (score, is_fraudulent)
    """
    # Move input to the same device as the model (GPU/CPU)
    img_tensor = img_tensor.to(DEVICE)

    with torch.no_grad():
        # The 'Orient' Phase: Reconstruct the image
        reconstruction = model(img_tensor)
        
        # Calculate MSE Loss (The "Residual")
        loss_fn = nn.MSELoss()
        mse_score = loss_fn(img_tensor, reconstruction).item()

    # The 'Decide' Phase: Compare against Dynamic Threshold
    is_forgery = mse_score > DYNAMIC_THRESHOLD
    
    return mse_score, is_forgery

def get_reconstruction(img_tensor):
    """Helper to get the reconstructed tensor for the visualizer."""
    img_tensor = img_tensor.to(DEVICE)
    with torch.no_grad():
        return model(img_tensor)