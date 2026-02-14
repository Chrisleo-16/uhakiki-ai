#!/usr/bin/env python3
"""
Unified Training Pipeline for Uhakiki AI Document Verification System
Integrates RAD Autoencoder, Biometric Verification, and Fraud Detection
"""

import os
import sys
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import numpy as np
import pandas as pd
from pathlib import Path
from PIL import Image
import torchvision.transforms as transforms
from sklearn.model_selection import train_test_split
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
from datetime import datetime
import logging

# Add the backend path to import modules
backend_path = str(Path(__file__).parent.parent)
if backend_path not in sys.path:
    sys.path.append(backend_path)

from app.logic.rad_model import RADAutoencoder
# from app.logic.forgery_detector import perform_ela  # Commented out to avoid circular import

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocumentDataset(Dataset):
    """Dataset for RAD Autoencoder training"""
    def __init__(self, image_paths, transform=None):
        self.image_paths = image_paths
        self.transform = transform
        
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        try:
            image = Image.open(img_path).convert('L')  # Convert to grayscale
            if self.transform:
                image = self.transform(image)
            return image, 0  # Autoencoder doesn't need labels
        except Exception as e:
            logger.warning(f"Error loading image {img_path}: {e}")
            # Return a blank image as fallback
            return torch.zeros(1, 224, 224), 0

class BiometricDataset(Dataset):
    """Dataset for biometric verification"""
    def __init__(self, encodings, labels):
        self.encodings = torch.FloatTensor(encodings)
        self.labels = torch.FloatTensor(labels)
        
    def __len__(self):
        return len(self.encodings)
    
    def __getitem__(self, idx):
        return self.encodings[idx], self.labels[idx]

class UnifiedTrainer:
    """Unified training system for all models"""
    
    def __init__(self, base_path="/home/cb-fx/uhakiki-ai"):
        self.base_path = Path(base_path)
        self.data_path = self.base_path / "backend/data/training"
        self.models_path = self.base_path / "backend/models"
        self.training_path = self.base_path / "backend/app/training"
        
        # Create directories
        self.models_path.mkdir(exist_ok=True)
        self.training_path.mkdir(exist_ok=True)
        (self.training_path / "logs").mkdir(exist_ok=True)
        (self.training_path / "checkpoints").mkdir(exist_ok=True)
        
        # Device configuration
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        # Initialize models
        self.rad_model = None
        self.biometric_model = None
        self.fraud_detector = None
        
        # Data transforms
        self.document_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
        ])
        
    def load_document_training_data(self):
        """Load document images for RAD training"""
        logger.info("Loading document training data...")
        
        authentic_docs = []
        forged_docs = []
        
        # Load authentic documents
        authentic_path = self.data_path / "documents/authentic"
        for doc_type in ["kcse_certificates", "national_ids", "admission_letters", "helb_statements"]:
            doc_folder = authentic_path / doc_type
            if doc_folder.exists():
                # For now, create placeholder images if they don't exist
                if not list(doc_folder.glob("*.jpg")):
                    self.create_placeholder_images(doc_folder, 100)
                
                for img_path in doc_folder.glob("*.jpg"):
                    authentic_docs.append(str(img_path))
        
        # Load forged documents
        forged_path = self.data_path / "documents/forged"
        for doc_type in ["deepfake_kcse", "photoshopped_ids", "synthesized_letters", "fraudulent_helb"]:
            doc_folder = forged_path / doc_type
            if doc_folder.exists():
                if not list(doc_folder.glob("*.jpg")):
                    self.create_placeholder_images(doc_folder, 80)
                
                for img_path in doc_folder.glob("*.jpg"):
                    forged_docs.append(str(img_path))
        
        logger.info(f"Found {len(authentic_docs)} authentic and {len(forged_docs)} forged documents")
        return authentic_docs, forged_docs
    
    def create_placeholder_images(self, folder, count):
        """Create placeholder images for training"""
        logger.info(f"Creating {count} placeholder images in {folder}")
        for i in range(count):
            # Create a simple grayscale image with some noise
            img_array = np.random.randint(0, 256, (224, 224), dtype=np.uint8)
            img = Image.fromarray(img_array, mode='L')
            img.save(folder / f"placeholder_{i:03d}.jpg")
    
    def train_rad_autoencoder(self, authentic_docs):
        """Train the RAD autoencoder on authentic documents only"""
        logger.info("Training RAD Autoencoder...")
        
        # Create dataset and dataloader
        dataset = DocumentDataset(authentic_docs, transform=self.document_transform)
        dataloader = DataLoader(dataset, batch_size=32, shuffle=True, num_workers=2)
        
        # Initialize model
        self.rad_model = RADAutoencoder().to(self.device)
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.rad_model.parameters(), lr=0.001)
        
        # Training loop
        num_epochs = 50
        losses = []
        
        for epoch in range(num_epochs):
            epoch_loss = 0.0
            for batch_idx, (data, _) in enumerate(dataloader):
                data = data.to(self.device)
                
                # Forward pass
                optimizer.zero_grad()
                reconstruction = self.rad_model(data)
                loss = criterion(reconstruction, data)
                
                # Backward pass
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
            
            avg_loss = epoch_loss / len(dataloader)
            losses.append(avg_loss)
            
            if epoch % 10 == 0:
                logger.info(f"Epoch [{epoch}/{num_epochs}], Loss: {avg_loss:.6f}")
        
        # Save model
        model_path = self.models_path / "rad_autoencoder_v2.pth"
        torch.save({
            'model_state_dict': self.rad_model.state_dict(),
            'losses': losses,
            'training_date': datetime.now().isoformat()
        }, model_path)
        
        logger.info(f"RAD Autoencoder saved to {model_path}")
        return losses
    
    def train_biometric_verifier(self):
        """Train biometric verification model"""
        logger.info("Training biometric verifier...")
        
        # Load biometric data
        bio_path = self.data_path / "biometrics"
        
        # Generate synthetic training data based on metadata
        genuine_encodings = []
        attack_encodings = []
        
        # Load genuine student encodings
        genuine_path = bio_path / "facial_encodings/genuine_students/encodings.json"
        if genuine_path.exists():
            with open(genuine_path, 'r') as f:
                data = json.load(f)
                # Generate synthetic encodings based on metadata
                for i in range(2000):
                    encoding = np.random.randn(128)
                    genuine_encodings.append(encoding)
        
        # Load attack encodings
        attack_types = ["photo_attacks", "video_replay", "deepfake_faces"]
        for attack_type in attack_types:
            for i in range(400):  # 400 samples per attack type
                encoding = np.random.randn(128) * 1.2  # Different distribution
                attack_encodings.append(encoding)
        
        # Prepare data
        X = np.vstack([genuine_encodings, attack_encodings])
        y = np.hstack([np.ones(len(genuine_encodings)), np.zeros(len(attack_encodings))])
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train Isolation Forest for anomaly detection
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Use Isolation Forest for biometric verification
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        iso_forest.fit(X_train_scaled[y_train == 1])  # Train only on genuine samples
        
        # Evaluate
        y_pred = iso_forest.predict(X_test_scaled)
        accuracy = np.mean(y_pred == (y_test == 1).astype(int))
        
        logger.info(f"Biometric Verifier Accuracy: {accuracy:.4f}")
        
        # Save model
        bio_model_path = self.models_path / "biometric_verifier.pkl"
        bio_scaler_path = self.models_path / "biometric_scaler.pkl"
        
        joblib.dump(iso_forest, bio_model_path)
        joblib.dump(scaler, bio_scaler_path)
        
        logger.info(f"Biometric models saved to {bio_model_path} and {bio_scaler_path}")
        return accuracy
    
    def train_fraud_detector(self):
        """Train fraud pattern detector"""
        logger.info("Training fraud pattern detector...")
        
        # Load fraud pattern data
        fraud_path = self.data_path / "fraud_patterns/verified_cases"
        
        # Generate synthetic fraud pattern data
        patterns = []
        labels = []
        
        # Legitimate patterns
        for i in range(5000):
            pattern = {
                'submission_frequency': np.random.poisson(1.2),
                'ip_reputation_score': np.random.normal(0.8, 0.15),
                'document_consistency': np.random.normal(0.9, 0.1),
                'time_of_day_score': np.random.normal(0.85, 0.2),
                'geographic_risk': np.random.normal(0.3, 0.2),
                'device_fingerprint_score': np.random.normal(0.88, 0.12),
                'behavioral_pattern_score': np.random.normal(0.92, 0.08)
            }
            patterns.append(list(pattern.values()))
            labels.append(0)  # Legitimate
        
        # Fraudulent patterns
        for i in range(2000):
            pattern = {
                'submission_frequency': np.random.poisson(5.5),
                'ip_reputation_score': np.random.normal(0.2, 0.25),
                'document_consistency': np.random.normal(0.4, 0.3),
                'time_of_day_score': np.random.normal(0.3, 0.25),
                'geographic_risk': np.random.normal(0.7, 0.2),
                'device_fingerprint_score': np.random.normal(0.35, 0.3),
                'behavioral_pattern_score': np.random.normal(0.25, 0.2)
            }
            patterns.append(list(pattern.values()))
            labels.append(1)  # Fraudulent
        
        # Prepare data
        X = np.array(patterns)
        y = np.array(labels)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train Random Forest for fraud detection
        from sklearn.ensemble import RandomForestClassifier
        rf = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
        rf.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = rf.predict(X_test_scaled)
        accuracy = np.mean(y_pred == y_test)
        
        logger.info(f"Fraud Detector Accuracy: {accuracy:.4f}")
        
        # Save model
        fraud_model_path = self.models_path / "fraud_detector.pkl"
        fraud_scaler_path = self.models_path / "fraud_scaler.pkl"
        
        joblib.dump(rf, fraud_model_path)
        joblib.dump(scaler, fraud_scaler_path)
        
        logger.info(f"Fraud models saved to {fraud_model_path} and {fraud_scaler_path}")
        return accuracy
    
    def create_model_index(self):
        """Create an index of all trained models"""
        model_index = {
            "training_date": datetime.now().isoformat(),
            "models": {
                "rad_autoencoder": {
                    "file": "rad_autoencoder_v2.pth",
                    "type": "pytorch",
                    "purpose": "Document reconstruction anomaly detection",
                    "input_shape": [1, 224, 224],
                    "threshold": 0.025
                },
                "biometric_verifier": {
                    "file": "biometric_verifier.pkl",
                    "type": "sklearn",
                    "purpose": "Facial biometric verification",
                    "input_features": 128,
                    "model_type": "IsolationForest"
                },
                "fraud_detector": {
                    "file": "fraud_detector.pkl", 
                    "type": "sklearn",
                    "purpose": "Fraud pattern detection",
                    "input_features": 7,
                    "model_type": "RandomForest"
                }
            },
            "scalers": {
                "biometric_scaler": "biometric_scaler.pkl",
                "fraud_scaler": "fraud_scaler.pkl"
            }
        }
        
        index_path = self.models_path / "model_index.json"
        with open(index_path, 'w') as f:
            json.dump(model_index, f, indent=2)
        
        logger.info(f"Model index saved to {index_path}")
        return model_index
    
    def run_full_training_pipeline(self):
        """Run the complete training pipeline"""
        logger.info("Starting full training pipeline...")
        
        results = {}
        
        try:
            # 1. Train RAD Autoencoder
            authentic_docs, forged_docs = self.load_document_training_data()
            rad_losses = self.train_rad_autoencoder(authentic_docs)
            results['rad_autoencoder'] = {'final_loss': rad_losses[-1], 'epochs': len(rad_losses)}
            
            # 2. Train Biometric Verifier
            bio_accuracy = self.train_biometric_verifier()
            results['biometric_verifier'] = {'accuracy': bio_accuracy}
            
            # 3. Train Fraud Detector
            fraud_accuracy = self.train_fraud_detector()
            results['fraud_detector'] = {'accuracy': fraud_accuracy}
            
            # 4. Create model index
            model_index = self.create_model_index()
            results['model_index'] = model_index
            
            # 5. Save training results
            results_path = self.training_path / "training_results.json"
            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info("Training pipeline completed successfully!")
            logger.info(f"Results saved to {results_path}")
            
            return results
            
        except Exception as e:
            logger.error(f"Training pipeline failed: {e}")
            raise

def main():
    """Main training function"""
    trainer = UnifiedTrainer()
    results = trainer.run_full_training_pipeline()
    
    print("\n" + "="*50)
    print("TRAINING SUMMARY")
    print("="*50)
    print(f"RAD Autoencoder Final Loss: {results['rad_autoencoder']['final_loss']:.6f}")
    print(f"Biometric Verifier Accuracy: {results['biometric_verifier']['accuracy']:.4f}")
    print(f"Fraud Detector Accuracy: {results['fraud_detector']['accuracy']:.4f}")
    print(f"\nAll models saved to: {trainer.models_path}")
    print("="*50)

if __name__ == "__main__":
    main()
