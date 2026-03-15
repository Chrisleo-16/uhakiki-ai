import torch
import torch.nn as nn
import torch.nn.functional as F


class RADAutoencoder(nn.Module):
    """
    Architecture exactly matches checkpoint shapes:
      encoder.0  Conv2d(1,32)       [32,1,3,3]
      encoder.1  BatchNorm2d(32)    [32]
      encoder.4  Conv2d(32,64)      [64,32,3,3]
      encoder.5  BatchNorm2d(64)    [64]
      encoder.8  Conv2d(64,128)     [128,64,3,3]
      encoder.9  BatchNorm2d(128)   [128]
      decoder.0  CTrans(128,64,2,2) [128,64,2,2]
      decoder.2  CTrans(64,32,2,2)  [64,32,2,2]
      decoder.4  CTrans(32,1,2,2)   [32,1,2,2]

    Encoder:  224 → 112 → 56        (2 MaxPool)
    Decoder:  56  → 112 → 224 → 448 (3 ConvTranspose stride=2)
    forward() clamps output back to input size via interpolation.
    """

    def __init__(self):
        super().__init__()

        self.encoder = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),    # 0
            nn.BatchNorm2d(32),                             # 1
            nn.ReLU(inplace=True),                          # 2
            nn.MaxPool2d(2, 2),                             # 3
            nn.Conv2d(32, 64, kernel_size=3, padding=1),   # 4
            nn.BatchNorm2d(64),                             # 5
            nn.ReLU(inplace=True),                          # 6
            nn.MaxPool2d(2, 2),                             # 7
            nn.Conv2d(64, 128, kernel_size=3, padding=1),  # 8
            nn.BatchNorm2d(128),                            # 9
            nn.ReLU(inplace=True),                          # 10
        )

        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(128, 64, kernel_size=2, stride=2),  # 0
            nn.ReLU(inplace=True),                                  # 1
            nn.ConvTranspose2d(64, 32, kernel_size=2, stride=2),   # 2
            nn.ReLU(inplace=True),                                  # 3
            nn.ConvTranspose2d(32, 1, kernel_size=2, stride=2),    # 4
            nn.Sigmoid(),                                           # 5
        )

    def encode(self, x):
        return self.encoder(x)

    def forward(self, x):
        out = self.decoder(self.encode(x))
        # Decoder upsamples 3x so output is 448 — resize back to input size
        if out.shape[2:] != x.shape[2:]:
            out = F.interpolate(
                out, size=x.shape[2:],
                mode='bilinear', align_corners=False
            )
        return out
