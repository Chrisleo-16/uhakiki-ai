import torch
import torch.nn as nn

class DocumentAutoencoder(nn.Module):
    """
    The RAD (Reconstruction Anomaly Detector):
    Trained ONLY on authentic Kenyan ID/Academic patterns.
    """
    def __init__(self):
        super(DocumentAutoencoder, self).__init__()
        
        # Encoder: Compressing the document signal
        self.encoder = nn.Sequential(
            nn.Conv2d(1, 32, 3, stride=2, padding=1), # [32, 112, 112]
            nn.ReLU(),
            nn.Conv2d(32, 64, 3, stride=2, padding=1), # [64, 56, 56]
            nn.ReLU(),
            nn.Conv2d(64, 128, 3, stride=2, padding=1), # [128, 28, 28]
        )
        
        # Decoder: Attempting to reconstruct the document
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(128, 64, 3, stride=2, padding=1, output_padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(64, 32, 3, stride=2, padding=1, output_padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(32, 1, 3, stride=2, padding=1, output_padding=1),
            nn.Sigmoid() # Output pixels between 0 and 1
        )

    def forward(self, x):
        x = self.encoder(x)
        x = self.decoder(x)
        return x