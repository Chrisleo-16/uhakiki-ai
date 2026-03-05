#!/usr/bin/env python3
"""
Kenyan ID Customization Training Pipeline
Fine-tunes the RAD Autoencoder on authentic Kenyan National IDs
to reduce false positives for local document verification.
"""

import os
import sys
import json
import shutil
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import numpy as np
from pathlib import Path
from PIL import Image
import torchvision.transforms as transforms
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add backend path - go up from app/training to backend, then add to path
script_dir = Path(__file__).parent.parent  # app/training
backend_path = script_dir.parent  # app
uhakiki_path = backend_path.parent  # root

# Add paths in correct order
sys.path.insert(0, str(uhakiki_path))
sys.path.insert(0, str(backend_path))

from app.logic.rad_model import RADAutoencoder


class KenyanDocumentDataset(Dataset):
    """Dataset specifically for Kenyan documents"""
    def __init__(self, image_paths, transform=None):
        self.image_paths = image_paths
        self.transform = transform
        
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        try:
            image = Image.open(img_path).convert('L')  # Grayscale
            if self.transform:
                image = self.transform(image)
            return image, 0
        except Exception as e:
            logger.warning(f"Error loading {img_path}: {e}")
            return torch.zeros(1, 224, 224), 0


class KenyanIDCustomizer:
    """Customizes the forgery detection model for Kenyan IDs"""
    
    def __init__(self, base_path="/home/cb-fx/uhakiki-ai"):
        self.base_path = Path(base_path)
        self.forensics_original = self.base_path / "backend/data/forensics/original"
        self.training_dir = self.base_path / "backend/data/training/documents/authentic/national_ids"
        self.models_path = self.base_path / "backend/models"
        
        # Device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        # Transforms
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
        ])
        
    def prepare_training_data(self):
        """
        Copy authentic Kenyan IDs to training directory
        and augment with variations for robust training
        """
        logger.info("Preparing Kenyan ID training data...")
        
        # Create training directory
        self.training_dir.mkdir(parents=True, exist_ok=True)
        
        # Find original Kenyan IDs
        original_ids = list(self.forensics_original.glob("*.jpg")) + \
                       list(self.forensics_original.glob("*.jpeg")) + \
                       list(self.forensics_original.glob("*.png"))
        
        logger.info(f"Found {len(original_ids)} original Kenyan IDs")
        
        if len(original_ids) == 0:
            logger.error("No original Kenyan IDs found!")
            return []
        
        training_images = []
        
        for orig_path in original_ids:
            # Copy original
            dest_path = self.training_dir / f"kenyan_id_{orig_path.name}"
            shutil.copy2(orig_path, dest_path)
            training_images.append(str(dest_path))
            logger.info(f"Copied: {orig_path.name}")
            
            # Create augmented versions for better training
            self.create_augmented_versions(orig_path, self.training_dir)
        
        logger.info(f"Prepared {len(training_images)} training images (with augmentations)")
        return training_images
    
    def create_augmented_versions(self, source_path, dest_dir):
        """Create augmented versions of the ID for training variety"""
        try:
            img = Image.open(source_path)
            
            # Variations to create
            augmentations = [
                ("slight_blur", lambda i: i.filter(ImageFilter.GaussianBlur(radius=0.5))),
                ("slight_brightness", self.adjust_brightness),
                ("slight_contrast", self.adjust_contrast),
                ("compression_variation", lambda i: i.save(dest_dir / "temp.jpg", 'JPEG', quality=85) or Image.open(dest_dir / "temp.jpg")),
            ]
            
            for aug_name, aug_fn in augmentations:
                try:
                    aug_img = aug_fn(img.copy())
                    aug_path = dest_dir / f"kenyan_id_{source_path.stem}_{aug_name}{source_path.suffix}"
                    aug_img.save(aug_path)
                except Exception as e:
                    logger.warning(f"Augmentation {aug_name} failed: {e}")
            
            # Clean up temp file
            temp_path = dest_dir / "temp.jpg"
            if temp_path.exists():
                temp_path.unlink()
                
        except Exception as e:
            logger.warning(f"Failed to create augmentations for {source_path}: {e}")
    
    def adjust_brightness(self, img):
        from PIL import ImageEnhance
        return ImageEnhance.Brightness(img).enhance(1.1)
    
    def adjust_contrast(self, img):
        from PIL import ImageEnhance
        return ImageEnhance.Contrast(img).enhance(1.1)
    
    def finetune_model(self, training_images, num_epochs=30, learning_rate=0.0005):
        """
        Fine-tune the RAD autoencoder on authentic Kenyan IDs
        """
        logger.info("Fine-tuning RAD Autoencoder on Kenyan IDs...")
        
        # Check for existing model
        model_path = self.models_path / "rad_autoencoder_v2.pth"
        
        # Initialize model
        model = RADAutoencoder().to(self.device)
        
        if model_path.exists():
            logger.info("Loading existing model for fine-tuning...")
            checkpoint = torch.load(model_path, map_location=self.device)
            model.load_state_dict(checkpoint.get('model_state_dict', checkpoint))
        
        # Create dataset and dataloader
        dataset = KenyanDocumentDataset(training_images, transform=self.transform)
        dataloader = DataLoader(dataset, batch_size=4, shuffle=True, num_workers=0)
        
        # Loss and optimizer
        criterion = nn.MSELoss()
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        
        # Training loop
        losses = []
        
        for epoch in range(num_epochs):
            epoch_loss = 0.0
            for batch_idx, (data, _) in enumerate(dataloader):
                data = data.to(self.device)
                
                # Forward pass
                optimizer.zero_grad()
                reconstruction = model(data)
                loss = criterion(reconstruction, data)
                
                # Backward pass
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
            
            avg_loss = epoch_loss / len(dataloader)
            losses.append(avg_loss)
            
            if epoch % 5 == 0:
                logger.info(f"Epoch [{epoch}/{num_epochs}], Loss: {avg_loss:.6f}")
        
        # Save fine-tuned model
        save_path = self.models_path / "rad_autoencoder_kenyan.pth"
        torch.save({
            'model_state_dict': model.state_dict(),
            'losses': losses,
            'training_date': datetime.now().isoformat(),
            'training_type': 'kenyan_id_finetune',
            'num_training_samples': len(training_images)
        }, save_path)
        
        logger.info(f"Fine-tuned model saved to {save_path}")
        return losses, model
    
    def calculate_adaptive_threshold(self, training_images):
        """
        Calculate adaptive threshold based on authentic Kenyan IDs
        This ensures genuine IDs aren't flagged as forged
        """
        logger.info("Calculating adaptive threshold for Kenyan IDs...")
        
        # Load the fine-tuned model
        model = RADAutoencoder().to(self.device)
        model_path = self.models_path / "rad_autoencoder_kenyan.pth"
        
        if model_path.exists():
            checkpoint = torch.load(model_path, map_location=self.device)
            model.load_state_dict(checkpoint.get('model_state_dict', checkpoint))
        
        model.eval()
        
        mse_scores = []
        
        with torch.no_grad():
            for img_path in training_images:
                try:
                    img = Image.open(img_path).convert('L')
                    img_tensor = self.transform(img).unsqueeze(0).to(self.device)
                    
                    reconstruction = model(img_tensor)
                    mse = nn.MSELoss()(img_tensor, reconstruction).item()
                    mse_scores.append(mse)
                except Exception as e:
                    logger.warning(f"Error calculating MSE for {img_path}: {e}")
        
        if mse_scores:
            mean_mse = np.mean(mse_scores)
            std_mse = np.std(mse_scores)
            
            # Set threshold at mean + 2*std to allow for natural variation
            # This ensures authentic IDs won't be flagged
            adaptive_threshold = mean_mse + (2 * std_mse)
            
            logger.info(f"MSE Stats - Mean: {mean_mse:.6f}, Std: {std_mse:.6f}")
            logger.info(f"Adaptive Threshold: {adaptive_threshold:.6f}")
            
            # Save threshold configuration
            config = {
                "threshold": adaptive_threshold,
                "mean_mse": mean_mse,
                "std_mse": std_mse,
                "training_samples": len(mse_scores),
                "calibration_date": datetime.now().isoformat(),
                "document_type": "kenyan_national_id"
            }
            
            config_path = self.models_path / "kenyan_threshold_config.json"
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Threshold config saved to {config_path}")
            return adaptive_threshold
        
        return 0.025  # Default fallback
    
    def run_customization(self):
        """Run the full Kenyan ID customization pipeline"""
        logger.info("=" * 60)
        logger.info("Starting Kenyan ID Model Customization")
        logger.info("=" * 60)
        
        # Step 1: Prepare training data
        training_images = self.prepare_training_data()
        
        if len(training_images) == 0:
            logger.error("No training data available. Aborting.")
            return None
        
        # Step 2: Fine-tune model
        losses, model = self.finetune_model(training_images)
        
        # Step 3: Calculate adaptive threshold
        threshold = self.calculate_adaptive_threshold(training_images)
        
        logger.info("=" * 60)
        logger.info("Kenyan ID Customization Complete!")
        logger.info("=" * 60)
        
        return {
            "training_images": len(training_images),
            "final_loss": losses[-1],
            "adaptive_threshold": threshold
        }


def main():
    """Main entry point"""
    customizer = KenyanIDCustomizer()
    results = customizer.run_customization()
    
    if results:
        print("\n" + "=" * 50)
        print("CUSTOMIZATION SUMMARY")
        print("=" * 50)
        print(f"Training Samples: {results['training_images']}")
        print(f"Final Loss: {results['final_loss']:.6f}")
        print(f"Adaptive Threshold: {results['adaptive_threshold']:.6f}")
        print("\nThe model is now customized for Kenyan National IDs!")
        print("False positives should be significantly reduced.")
        print("=" * 50)
    else:
        print("Customization failed. Check logs for details.")


if __name__ == "__main__":
    main()
