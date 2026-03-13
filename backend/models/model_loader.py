"""
Unified Model Loader for Uhakiki AI
Centralized loading and management of all trained models
"""

import torch
import torch.nn as nn
import joblib
import json
import numpy as np
from pathlib import Path
import logging
from typing import Dict, Any, Tuple, Optional
from pydantic import *
from app.logic.rad_model import RADAutoencoder

logger = logging.getLogger(__name__)

class ModelManager:
    """Centralized model management for the verification system"""
    
    def __init__(self, models_path: str = "/home/cb-fx/uhakiki-ai/backend/models"):
        self.models_path = Path(models_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Model cache
        self._rad_model = None
        self._biometric_verifier = None
        self._fraud_detector = None
        self._scalers = {}
        self._model_index = None
        
        # Load model index
        self._load_model_index()
    
    def _load_model_index(self):
        """Load the model configuration index"""
        index_path = self.models_path / "model_index.json"
        if index_path.exists():
            with open(index_path, 'r') as f:
                self._model_index = json.load(f)
            logger.info("Model index loaded successfully")
        else:
            logger.warning("Model index not found. Available models may be limited.")
            self._model_index = {}
    
    def load_rad_autoencoder(self) -> RADAutoencoder:
        """Load the RAD autoencoder model"""
        if self._rad_model is None:
            # Get the file name from model index
            file_name = "rad_autoencoder_v2.pth"  # default
            if self._model_index and 'models' in self._model_index:
                rad_config = self._model_index['models'].get('rad_autoencoder', {})
                file_name = rad_config.get('file', file_name)
            
            model_path = self.models_path / file_name
            if not model_path.exists():
                # Fallback to original model
                model_path = self.models_path / "rad_v1.pth"
                if not model_path.exists():
                    # Try the kenyan one as a last resort?
                    model_path = self.models_path / "rad_autoencoder_kenyan.pth"
            
            if model_path.exists():
                self._rad_model = RADAutoencoder().to(self.device)
                
                # Load state dict
                checkpoint = torch.load(model_path, map_location=self.device)
                if 'model_state_dict' in checkpoint:
                    self._rad_model.load_state_dict(checkpoint['model_state_dict'])
                else:
                    self._rad_model.load_state_dict(checkpoint)
                
                self._rad_model.eval()
                logger.info(f"RAD Autoencoder loaded from {model_path}")
            else:
                raise FileNotFoundError("RAD Autoencoder model not found")
        
        return self._rad_model
    
    def load_biometric_verifier(self):
        """Load the biometric verification model"""
        if self._biometric_verifier is None:
            model_path = self.models_path / "biometric_verifier.pkl"
            scaler_path = self.models_path / "biometric_scaler.pkl"
            
            if model_path.exists():
                self._biometric_verifier = joblib.load(model_path)
                
                if scaler_path.exists():
                    self._scalers['biometric'] = joblib.load(scaler_path)
                
                logger.info(f"Biometric verifier loaded from {model_path}")
            else:
                raise FileNotFoundError("Biometric verifier model not found")
        
        return self._biometric_verifier
    
    def load_fraud_detector(self):
        """Load the fraud detection model"""
        if self._fraud_detector is None:
            model_path = self.models_path / "fraud_detector.pkl"
            scaler_path = self.models_path / "fraud_scaler.pkl"
            
            if model_path.exists():
                self._fraud_detector = joblib.load(model_path)
                
                if scaler_path.exists():
                    self._scalers['fraud'] = joblib.load(scaler_path)
                
                logger.info(f"Fraud detector loaded from {model_path}")
            else:
                raise FileNotFoundError("Fraud detector model not found")
        
        return self._fraud_detector
    
    def get_scaler(self, scaler_name: str):
        """Get a specific scaler"""
        if scaler_name in self._scalers:
            return self._scalers[scaler_name]
        else:
            scaler_path = self.models_path / f"{scaler_name}.pkl"
            if scaler_path.exists():
                self._scalers[scaler_name] = joblib.load(scaler_path)
                return self._scalers[scaler_name]
            else:
                raise FileNotFoundError(f"Scaler {scaler_name} not found")
    
    def predict_document_authenticity(self, image_tensor: torch.Tensor) -> Tuple[float, bool]:
        """
        Predict document authenticity using RAD autoencoder
        
        Args:
            image_tensor: Preprocessed image tensor [1, 224, 224]
            
        Returns:
            Tuple of (mse_score, is_forged)
        """
        model = self.load_rad_autoencoder()
        
        with torch.no_grad():
            image_tensor = image_tensor.to(self.device)
            if len(image_tensor.shape) == 3:
                image_tensor = image_tensor.unsqueeze(0)  # Add batch dimension
            
            reconstruction = model(image_tensor)
            mse_loss = nn.MSELoss()
            mse_score = mse_loss(image_tensor, reconstruction).item()
            
            # Use threshold from trained model config
            threshold = 0.025  # Default fallback
            try:
                # Load the actual trained threshold
                config_path = self.models_path / "kenyan_threshold_config.json"
                if config_path.exists():
                    import json
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        threshold = config.get('threshold', 0.025)
                        print(f"📊 Using trained threshold: {threshold}")
            except Exception as e:
                print(f"⚠️ Could not load threshold config, using default: {e}")
            
            is_forged = mse_score > threshold
            
            return mse_score, is_forged
    
    def predict_biometric_authenticity(self, encoding: np.ndarray) -> Tuple[float, bool]:
        """
        Predict biometric authenticity
        
        Args:
            encoding: Face encoding array
            
        Returns:
            Tuple of (anomaly_score, is_genuine)
        """
        model = load_biometric_verifier()
        scaler = self.get_scaler('biometric')
        
        # Scale the encoding
        encoding_scaled = scaler.transform(encoding.reshape(1, -1))
        
        # Predict (IsolationForest returns 1 for inliers, -1 for outliers)
        prediction = model.predict(encoding_scaled)[0]
        anomaly_score = model.decision_function(encoding_scaled)[0]
        
        is_genuine = prediction == 1
        
        return anomaly_score, is_genuine
    
    def predict_fraud_probability(self, features: np.ndarray) -> Tuple[float, bool]:
        """
        Predict fraud probability
        
        Args:
            features: Fraud pattern features
            
        Returns:
            Tuple of (fraud_probability, is_fraudulent)
        """
        model = self.load_fraud_detector()
        scaler = self.get_scaler('fraud')
        
        # Scale features
        features_scaled = scaler.transform(features.reshape(1, -1))
        
        # Get fraud probability
        fraud_proba = model.predict_proba(features_scaled)[0]
        fraud_probability = fraud_proba[1]  # Probability of class 1 (fraud)
        
        is_fraudulent = fraud_probability > 0.5
        
        return fraud_probability, is_fraudulent
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models"""
        return {
            "rad_model_loaded": self._rad_model is not None,
            "biometric_verifier_loaded": self._biometric_verifier is not None,
            "fraud_detector_loaded": self._fraud_detector is not None,
            "available_scalers": list(self._scalers.keys()),
            "model_index": self._model_index,
            "device": str(self.device)
        }
    
    def reload_models(self):
        """Force reload all models"""
        self._rad_model = None
        self._biometric_verifier = None
        self._fraud_detector = None
        self._scalers = {}
        self._load_model_index()
        logger.info("Models cache cleared - will reload on next access")

# Global model manager instance
model_manager = ModelManager()

# Convenience functions for backward compatibility
def get_rad_model():
    """Get RAD autoencoder model"""
    return model_manager.load_rad_autoencoder()

def get_biometric_verifier():
    """Get biometric verification model"""
    return model_manager.load_biometric_verifier()

def get_fraud_detector():
    """Get fraud detection model"""
    return model_manager.load_fraud_detector()
class SignUpRequest(BaseModel):
    username : str
    password : str
    email : str

class SignInRequest(BaseModel):
    username : str
    password : str

class TokenResponse(BaseModel):
    token_type : str = "bearer"
    access_token : str

# Updated models for Kenyan citizen registration
class KenyanRegistrationRequest(BaseModel):
    citizenship: str
    identificationType: str  # 'national_id' or 'kcse_certificate'
    identificationNumber: str
    firstName: str
    email: str
    password: str
    dateOfBirth: Optional[str] = None  # For KCSE registration
    kcseExamYear: Optional[str] = None  # For KCSE registration

class ForeignRegistrationRequest(BaseModel):
    citizenship: str
    identificationType: str  # 'passport'
    identificationNumber: str
    firstName: str
    email: str
    password: str

class RegistrationResponse(BaseModel):
    status: str
    message: str
    access_token: Optional[str] = None
    user_id: Optional[str] = None
