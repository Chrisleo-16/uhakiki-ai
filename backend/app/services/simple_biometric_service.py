"""
Simplified Biometric Service
Handles biometric verification and liveness detection without external dependencies
"""

from datetime import datetime
from typing import Dict, Optional
import logging
import random

logger = logging.getLogger(__name__)

class SimpleBiometricService:
    """Simplified biometric service for demonstration"""
    
    def __init__(self):
        self.challenges = ['BLINK', 'TURN_LEFT', 'TURN_RIGHT', 'SMILE', 'LOOK_UP', 'LOOK_DOWN']
        self.current_challenge = None
        self.challenge_index = 0
    
    def generate_new_challenge(self) -> str:
        """Generate a new MBIC liveness challenge"""
        self.challenge_index = (self.challenge_index + 1) % len(self.challenges)
        self.current_challenge = self.challenges[self.challenge_index]
        return self.current_challenge
    
    def process_frame(self, image_data: str) -> Dict:
        """Process frame for liveness detection (simplified)"""
        try:
            # Simulate liveness detection
            liveness_score = random.uniform(0.6, 0.95)
            face_detected = random.choice([True, True, False])  # 2/3 chance
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "challenge": self.current_challenge or "BLINK",
                "status": "LIVENESS_CONFIRMED" if liveness_score > 0.7 else "PROCESSING",
                "liveness_score": liveness_score,
                "face_detected": face_detected,
                "challenge_met": liveness_score > 0.8,
                "feedback": "Liveness verified" if liveness_score > 0.7 else "Continue following challenges",
                "details": {
                    "face_quality": "good" if face_detected else "poor",
                    "lighting": "adequate",
                    "position": "centered"
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Frame processing error: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "ERROR",
                "feedback": f"Processing error: {str(e)}",
                "liveness_score": 0.0
            }
    
    def verify_face_match(self, student_id: str) -> Dict:
        """Verify if face matches reference (simplified)"""
        try:
            # Simulate face matching
            confidence = random.uniform(0.7, 0.98)
            verified = confidence > 0.8
            
            return {
                "verified": verified,
                "confidence": confidence,
                "feedback": "Face verified successfully" if verified else "Face does not match reference",
                "face_quality": {
                    "sharpness": random.uniform(0.7, 0.95),
                    "brightness": random.uniform(0.6, 0.9),
                    "contrast": random.uniform(0.7, 0.9)
                }
            }
            
        except Exception as e:
            logger.error(f"Face verification error: {e}")
            return {
                "verified": False,
                "confidence": 0.0,
                "feedback": f"Verification error: {str(e)}"
            }
    
    def register_reference_face(self, student_id: str) -> Dict:
        """Register reference face (simplified)"""
        try:
            # Simulate face registration
            face_detected = random.choice([True, True, True, False])  # 3/4 chance
            
            if not face_detected:
                return {
                    "success": False,
                    "message": "No face detected in ID card",
                    "feedback": "Please ensure the ID card has a clear photo"
                }
            
            return {
                "success": True,
                "message": "Reference face registered successfully",
                "student_id": student_id,
                "face_quality": "good",
                "feedback": "Face registration completed"
            }
            
        except Exception as e:
            logger.error(f"Face registration error: {e}")
            return {
                "success": False,
                "message": f"Registration error: {str(e)}"
            }
    
    def get_reference_face(self, student_id: str) -> Dict:
        """Get reference face information (simplified)"""
        return {
            "student_id": student_id,
            "face_registered": True,
            "registration_date": "2024-06-15T10:30:00Z",
            "face_quality": "good",
            "reference_available": True
        }
    
    def complete_verification(self, student_id: str, liveness_score: float, face_verified: bool) -> Dict:
        """Complete biometric verification process"""
        try:
            # Calculate overall confidence
            overall_confidence = (liveness_score * 0.6) + (0.8 if face_verified else 0.4)
            
            # Determine verification result
            if overall_confidence > 0.7 and face_verified:
                result = "VERIFIED"
                status = "PASS"
            elif overall_confidence > 0.5:
                result = "REQUIRES_REVIEW"
                status = "REQUIRES_HUMAN_REVIEW"
            else:
                result = "FAILED"
                status = "FAIL"
            
            return {
                "verification_result": result,
                "status": status,
                "confidence": overall_confidence,
                "student_id": student_id,
                "message": f"Biometric verification {result.lower()}",
                "next_steps": "Proceed to document verification" if result == "VERIFIED" else "Manual review required"
            }
            
        except Exception as e:
            logger.error(f"Biometric completion error: {e}")
            return {
                "verification_result": "ERROR",
                "status": "FAIL",
                "message": f"Completion error: {str(e)}"
            }

# Global service instance
simple_biometric_service = SimpleBiometricService()
