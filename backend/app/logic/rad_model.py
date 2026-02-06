import torch
import torch.nn as nn

class RADAutoencoder(nn.Module):
    """
    Residual Anomaly Detection (RAD) Autoencoder.
    Optimized for 224x224 Document Images.
    """
    def __init__(self):
        super(RADAutoencoder, self).__init__()
        
        # --- ENCODER (Compresses the Document) ---
        self.encoder = nn.Sequential(
            # Input: 1 x 224 x 224 (Grayscale)
            nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2), # -> 32 x 112 x 112
            
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2), # -> 64 x 56 x 56
            
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2)  # -> 128 x 28 x 28 (The Latent "Fingerprint")
        )
        
        # --- DECODER (Reconstructs the Document) ---
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(128, 64, kernel_size=2, stride=2),
            nn.ReLU(), # -> 64 x 56 x 56
            
            nn.ConvTranspose2d(64, 32, kernel_size=2, stride=2),
            nn.ReLU(), # -> 32 x 112 x 112
            
            nn.ConvTranspose2d(32, 1, kernel_size=2, stride=2),
            nn.Sigmoid() # -> 1 x 224 x 224 (Output pixel range 0-1)
        )

    def forward(self, x):
        x = self.encoder(x)
        x = self.decoder(x)
        return x