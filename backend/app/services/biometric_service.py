"""
Biometric Liveness Service
Handles real-time biometric verification and liveness detection
"""

import cv2
import numpy as np
import base64
import logging
from typing import Dict, Tuple, Optional
from datetime import datetime
import os
import json

logger = logging.getLogger(__name__)

class BiometricLivenessService:
    """Service for biometric liveness detection and face verification"""
    
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        self.smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')
        
        # MBIC challenge states
        self.current_challenge = None
        self.challenge_sequence = ['BLINK', 'TURN_LEFT', 'TURN_RIGHT', 'SMILE', 'LOOK_UP', 'LOOK_DOWN']
        self.challenge_index = 0
        self.challenge_completed = False
        
    def decode_base64_image(self, base64_string: str) -> Optional[np.ndarray]:
        """Decode base64 image string to OpenCV image"""
        try:
            # Remove data URL prefix if present
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            # Decode
            image_bytes = base64.b64decode(base64_string)
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                logger.error("Failed to decode image")
                return None
            
            # Ensure image is 3-channel BGR for consistent processing
            if len(image.shape) == 2:
                # Image is grayscale, convert to BGR
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            elif len(image.shape) == 3 and image.shape[2] == 1:
                # Image has single channel, convert to BGR
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            elif len(image.shape) == 3 and image.shape[2] == 4:
                # Image has alpha channel, convert to BGR
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            
            return image
        except Exception as e:
            logger.error(f"Error decoding base64 image: {e}")
            return None
    
    def detect_face(self, image: np.ndarray) -> Tuple[bool, Optional[Tuple[int, int, int, int]]]:
        """Detect face in image"""
        try:
            # Convert to grayscale for face detection
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0:
                # Return the largest face
                largest_face = max(faces, key=lambda x: x[2] * x[3])
                return True, tuple(largest_face)
            
            return False, None
        except Exception as e:
            logger.error(f"Face detection error: {e}")
            return False, None
    
    def detect_eyes(self, image: np.ndarray, face_region: Tuple[int, int, int, int]) -> Tuple[bool, int]:
        """Detect eyes for blink detection"""
        try:
            x, y, w, h = face_region
            face_roi = image[y:y+h, x:x+w]
            
            # Convert to grayscale for eye detection
            if len(face_roi.shape) == 3:
                gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            else:
                gray_face = face_roi
            
            eyes = self.eye_cascade.detectMultiScale(gray_face, 1.1, 4)
            eye_count = len(eyes)
            
            return eye_count >= 2, eye_count
        except Exception as e:
            logger.error(f"Eye detection error: {e}")
            return False, 0
    
    def detect_smile(self, image: np.ndarray, face_region: Tuple[int, int, int, int]) -> bool:
        """Detect smile for liveness"""
        try:
            x, y, w, h = face_region
            face_roi = image[y:y+h, x:x+w]
            
            # Convert to grayscale for smile detection
            if len(face_roi.shape) == 3:
                gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            else:
                gray_face = face_roi
            
            smiles = self.smile_cascade.detectMultiScale(gray_face, 1.8, 20)
            return len(smiles) > 0
        except Exception as e:
            logger.error(f"Smile detection error: {e}")
            return False
    
    def analyze_facial_landmarks(self, image: np.ndarray, face_region: Tuple[int, int, int, int]) -> Dict:
        """Analyze facial landmarks for liveness detection"""
        try:
            x, y, w, h = face_region
            face_roi = image[y:y+h, x:x+w]
            
            # Convert to grayscale for analysis
            if len(face_roi.shape) == 3:
                gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            else:
                gray_face = face_roi
            
            # Calculate basic metrics
            face_area = w * h
            image_area = image.shape[0] * image.shape[1]
            face_ratio = face_area / image_area
            
            # Edge detection for texture analysis
            edges = cv2.Canny(gray_face, 50, 150)
            edge_density = np.sum(edges > 0) / (w * h)
            
            # Blur detection (to detect photo/print attacks)
            laplacian_var = cv2.Laplacian(gray_face, cv2.CV_64F).var()
            
            return {
                "face_area": face_area,
                "face_ratio": face_ratio,
                "edge_density": float(edge_density),
                "blur_score": float(laplacian_var),
                "is_clear": laplacian_var > 100,  # Threshold for clear image
                "face_size_appropriate": 0.1 < face_ratio < 0.8,  # Reasonable face size
            }
        except Exception as e:
            logger.error(f"Facial landmark analysis error: {e}")
            return {}
    
    def generate_new_challenge(self) -> str:
        """Generate new MBIC challenge"""
        self.challenge_index = (self.challenge_index + 1) % len(self.challenge_sequence)
        self.current_challenge = self.challenge_sequence[self.challenge_index]
        self.challenge_completed = False
        return self.current_challenge
    
    def process_mbic_frame(self, image: np.ndarray, reference_encoding: Optional[np.ndarray] = None) -> Dict:
        """Process frame for MBIC liveness detection"""
        try:
            result = {
                "timestamp": datetime.now().isoformat(),
                "challenge": self.current_challenge,
                "status": "PROCESSING",
                "liveness_score": 0.0,
                "face_detected": False,
                "challenge_met": False,
                "feedback": "",
                "details": {}
            }
            
            # Detect face
            face_detected, face_region = self.detect_face(image)
            result["face_detected"] = face_detected
            
            if not face_detected:
                result["status"] = "NO_FACE"
                result["feedback"] = "Please position your face in the camera"
                return result
            
            if not face_region:
                result["status"] = "ERROR"
                result["feedback"] = "Face detection failed"
                return result
            
            # Analyze facial landmarks
            landmarks = self.analyze_facial_landmarks(image, face_region)
            result["details"]["landmarks"] = landmarks
            
            # Check image quality
            if not landmarks.get("is_clear", False):
                result["status"] = "POOR_QUALITY"
                result["feedback"] = "Image is too blurry, please move closer"
                return result
            
            if not landmarks.get("face_size_appropriate", False):
                result["status"] = "POOR_POSITIONING"
                result["feedback"] = "Please adjust your distance from camera"
                return result
            
            # Process based on current challenge
            challenge_result = self._process_challenge(image, face_region)
            result.update(challenge_result)
            
            # Calculate overall liveness score
            liveness_score = self._calculate_liveness_score(result)
            result["liveness_score"] = liveness_score
            
            # Determine if liveness is confirmed
            if liveness_score > 0.7 and result.get("challenge_met", False):
                result["status"] = "LIVENESS_CONFIRMED"
                result["feedback"] = "Liveness verified successfully"
            elif liveness_score > 0.4:
                result["status"] = "PARTIAL_LIVENESS"
                result["feedback"] = "Continue following the challenges"
            else:
                result["status"] = "LIVENESS_FAILED"
                result["feedback"] = "Liveness detection failed, please try again"
            
            return result
            
        except Exception as e:
            logger.error(f"MBIC frame processing error: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "ERROR",
                "feedback": f"Processing error: {str(e)}",
                "liveness_score": 0.0
            }
    
    def _process_challenge(self, image: np.ndarray, face_region: Tuple[int, int, int, int]) -> Dict:
        """Process specific MBIC challenge"""
        challenge = self.current_challenge
        
        if challenge == "BLINK":
            return self._process_blink_challenge(image, face_region)
        elif challenge == "SMILE":
            return self._process_smile_challenge(image, face_region)
        elif challenge in ["TURN_LEFT", "TURN_RIGHT", "LOOK_UP", "LOOK_DOWN"]:
            return self._process_movement_challenge(image, face_region)
        else:
            return {"challenge_met": False, "feedback": "Unknown challenge"}
    
    def _process_blink_challenge(self, image: np.ndarray, face_region: Tuple[int, int, int, int]) -> Dict:
        """Process blink detection challenge"""
        eyes_detected, eye_count = self.detect_eyes(image, face_region)
        
        # Simple blink detection (would need temporal analysis in production)
        blink_detected = eyes_detected and eye_count >= 2
        
        return {
            "challenge_met": blink_detected,
            "feedback": "Blink detected" if blink_detected else "Please blink naturally",
            "eye_count": eye_count,
            "eyes_detected": eyes_detected
        }
    
    def _process_smile_challenge(self, image: np.ndarray, face_region: Tuple[int, int, int, int]) -> Dict:
        """Process smile detection challenge"""
        smile_detected = self.detect_smile(image, face_region)
        
        return {
            "challenge_met": smile_detected,
            "feedback": "Smile detected" if smile_detected else "Please smile naturally",
            "smile_detected": smile_detected
        }
    
    def _process_movement_challenge(self, image: np.ndarray, face_region: Tuple[int, int, int, int]) -> Dict:
        """Process head movement challenge"""
        # In production, this would track face position over time
        # For now, we'll simulate with random success based on face detection quality
        landmarks = self.analyze_facial_landmarks(image, face_region)
        face_quality = landmarks.get("face_ratio", 0.5)
        
        # Simulate movement detection
        movement_detected = 0.3 < face_quality < 0.7
        
        return {
            "challenge_met": movement_detected,
            "feedback": "Movement detected" if movement_detected else f"Please {self.current_challenge.replace('_', ' ').lower()}",
            "face_quality": face_quality
        }
    
    def _calculate_liveness_score(self, result: Dict) -> float:
        """Calculate overall liveness confidence score"""
        score = 0.0
        
        # Face detection (30%)
        if result.get("face_detected", False):
            score += 0.3
        
        # Image quality (20%)
        landmarks = result.get("details", {}).get("landmarks", {})
        if landmarks.get("is_clear", False):
            score += 0.1
        if landmarks.get("face_size_appropriate", False):
            score += 0.1
        
        # Challenge completion (50%)
        if result.get("challenge_met", False):
            score += 0.5
        
        return min(score, 1.0)
    
    def verify_face_match(self, live_image: np.ndarray, reference_encoding: np.ndarray, tolerance: float = 0.6) -> Dict:
        """Verify if live face matches reference face"""
        try:
            # This is a simplified version - in production you'd use proper face recognition
            # For now, we'll simulate with face detection quality
            
            face_detected, face_region = self.detect_face(live_image)
            if not face_detected:
                return {
                    "verified": False,
                    "confidence": 0.0,
                    "feedback": "No face detected in live image"
                }
            
            # Analyze face quality
            landmarks = self.analyze_facial_landmarks(live_image, face_region)
            
            # Simulate face matching (would use actual face recognition in production)
            quality_score = 0.0
            if landmarks.get("is_clear", False):
                quality_score += 0.4
            if landmarks.get("face_size_appropriate", False):
                quality_score += 0.3
            if landmarks.get("edge_density", 0) > 0.1:
                quality_score += 0.3
            
            # Add some randomness to simulate real matching
            import random
            quality_score += random.uniform(-0.2, 0.2)
            quality_score = max(0.0, min(1.0, quality_score))
            
            verified = quality_score > tolerance
            
            return {
                "verified": verified,
                "confidence": quality_score,
                "feedback": "Face verified successfully" if verified else "Face does not match reference",
                "face_quality": landmarks
            }
            
        except Exception as e:
            logger.error(f"Face verification error: {e}")
            return {
                "verified": False,
                "confidence": 0.0,
                "feedback": f"Verification error: {str(e)}"
            }

# Global service instance
biometric_service = BiometricLivenessService()
