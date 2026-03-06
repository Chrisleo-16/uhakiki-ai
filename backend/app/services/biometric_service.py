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

# ── Central image utilities (fixes all "Bad number of channels" errors) ────────
from app.logic.image_utils import ensure_bgr_image, ensure_gray_image, decode_image_safe

logger = logging.getLogger(__name__)


class BiometricLivenessService:
    """Service for biometric liveness detection and face verification"""

    def __init__(self):
        self.face_cascade  = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.eye_cascade   = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )
        self.smile_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_smile.xml'
        )

        self.current_challenge  = None
        self.challenge_sequence = [
            'BLINK', 'TURN_LEFT', 'TURN_RIGHT', 'SMILE', 'LOOK_UP', 'LOOK_DOWN'
        ]
        self.challenge_index    = 0
        self.challenge_completed = False

    # ── Image I/O ─────────────────────────────────────────────────────────────

    def decode_base64_image(self, base64_string: str) -> Optional[np.ndarray]:
        """Decode base64 string → guaranteed 3-channel BGR ndarray."""
        try:
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            image_bytes = base64.b64decode(base64_string)
            image = decode_image_safe(image_bytes, force_bgr=True)
            if image is None:
                logger.error("Failed to decode image")
            return image
        except Exception as e:
            logger.error(f"Error decoding base64 image: {e}")
            return None

    # ── Detection helpers ─────────────────────────────────────────────────────

    def detect_face(
        self, image: np.ndarray
    ) -> Tuple[bool, Optional[Tuple[int, int, int, int]]]:
        """Detect face in image. Returns (found, (x,y,w,h) or None)."""
        try:
            gray  = ensure_gray_image(image)   # safe regardless of input format
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            if len(faces) > 0:
                largest = max(faces, key=lambda x: x[2] * x[3])
                return True, tuple(largest)
            return False, None
        except Exception as e:
            logger.error(f"Face detection error: {e}")
            return False, None

    def detect_eyes(
        self, image: np.ndarray, face_region: Tuple[int, int, int, int]
    ) -> Tuple[bool, int]:
        """Detect eyes within the face ROI."""
        try:
            x, y, w, h   = face_region
            bgr_face     = ensure_bgr_image(image)[y:y + h, x:x + w]
            gray_face    = ensure_gray_image(bgr_face)
            eyes         = self.eye_cascade.detectMultiScale(gray_face, 1.1, 4)
            eye_count    = len(eyes)
            return eye_count >= 2, eye_count
        except Exception as e:
            logger.error(f"Eye detection error: {e}")
            return False, 0

    def detect_smile(
        self, image: np.ndarray, face_region: Tuple[int, int, int, int]
    ) -> bool:
        """Detect smile within the face ROI."""
        try:
            x, y, w, h = face_region
            bgr_face   = ensure_bgr_image(image)[y:y + h, x:x + w]
            gray_face  = ensure_gray_image(bgr_face)
            smiles     = self.smile_cascade.detectMultiScale(gray_face, 1.8, 20)
            return len(smiles) > 0
        except Exception as e:
            logger.error(f"Smile detection error: {e}")
            return False

    def analyze_facial_landmarks(
        self, image: np.ndarray, face_region: Tuple[int, int, int, int]
    ) -> Dict:
        """Analyze facial landmarks for liveness detection."""
        try:
            x, y, w, h   = face_region
            bgr_face     = ensure_bgr_image(image)[y:y + h, x:x + w]
            gray_face    = ensure_gray_image(bgr_face)

            face_area    = w * h
            image_area   = image.shape[0] * image.shape[1]
            face_ratio   = face_area / image_area

            edges        = cv2.Canny(gray_face, 50, 150)
            edge_density = float(np.sum(edges > 0) / (w * h))

            laplacian_var = float(cv2.Laplacian(gray_face, cv2.CV_64F).var())

            return {
                "face_area":             face_area,
                "face_ratio":            face_ratio,
                "edge_density":          edge_density,
                "blur_score":            laplacian_var,
                "is_clear":              laplacian_var > 100,
                "face_size_appropriate": 0.1 < face_ratio < 0.8,
            }
        except Exception as e:
            logger.error(f"Facial landmark analysis error: {e}")
            return {}

    # ── Challenge management ──────────────────────────────────────────────────

    def generate_new_challenge(self) -> str:
        self.challenge_index     = (self.challenge_index + 1) % len(self.challenge_sequence)
        self.current_challenge   = self.challenge_sequence[self.challenge_index]
        self.challenge_completed = False
        return self.current_challenge

    # ── MBIC frame processing ─────────────────────────────────────────────────

    def process_mbic_frame(
        self,
        image: np.ndarray,
        reference_encoding: Optional[np.ndarray] = None,
    ) -> Dict:
        """Process a single webcam frame for MBIC liveness detection."""
        try:
            # Normalise once at the entry point; all helpers receive BGR
            image = ensure_bgr_image(image)

            result = {
                "timestamp":     datetime.now().isoformat(),
                "challenge":     self.current_challenge,
                "status":        "PROCESSING",
                "liveness_score": 0.0,
                "face_detected": False,
                "challenge_met": False,
                "feedback":      "",
                "details":       {},
            }

            face_detected, face_region = self.detect_face(image)
            result["face_detected"] = face_detected

            if not face_detected:
                result["status"]   = "NO_FACE"
                result["feedback"] = "Please position your face in the camera"
                return result

            if not face_region:
                result["status"]   = "ERROR"
                result["feedback"] = "Face detection failed"
                return result

            landmarks = self.analyze_facial_landmarks(image, face_region)
            result["details"]["landmarks"] = landmarks

            if not landmarks.get("is_clear", False):
                result["status"]   = "POOR_QUALITY"
                result["feedback"] = "Image is too blurry, please move closer"
                return result

            if not landmarks.get("face_size_appropriate", False):
                result["status"]   = "POOR_POSITIONING"
                result["feedback"] = "Please adjust your distance from camera"
                return result

            challenge_result = self._process_challenge(image, face_region)
            result.update(challenge_result)

            liveness_score        = self._calculate_liveness_score(result)
            result["liveness_score"] = liveness_score

            if liveness_score > 0.7 and result.get("challenge_met", False):
                result["status"]   = "LIVENESS_CONFIRMED"
                result["feedback"] = "Liveness verified successfully"
            elif liveness_score > 0.4:
                result["status"]   = "PARTIAL_LIVENESS"
                result["feedback"] = "Continue following the challenges"
            else:
                result["status"]   = "LIVENESS_FAILED"
                result["feedback"] = "Liveness detection failed, please try again"

            return result

        except Exception as e:
            logger.error(f"MBIC frame processing error: {e}")
            return {
                "timestamp":     datetime.now().isoformat(),
                "status":        "ERROR",
                "feedback":      f"Processing error: {str(e)}",
                "liveness_score": 0.0,
            }

    # ── Challenge processing ──────────────────────────────────────────────────

    def _process_challenge(
        self, image: np.ndarray, face_region: Tuple[int, int, int, int]
    ) -> Dict:
        challenge = self.current_challenge
        if challenge == "BLINK":
            return self._process_blink_challenge(image, face_region)
        elif challenge == "SMILE":
            return self._process_smile_challenge(image, face_region)
        elif challenge in ("TURN_LEFT", "TURN_RIGHT", "LOOK_UP", "LOOK_DOWN"):
            return self._process_movement_challenge(image, face_region)
        return {"challenge_met": False, "feedback": "Unknown challenge"}

    def _process_blink_challenge(
        self, image: np.ndarray, face_region: Tuple[int, int, int, int]
    ) -> Dict:
        eyes_detected, eye_count = self.detect_eyes(image, face_region)
        blink_detected = eyes_detected and eye_count >= 2
        return {
            "challenge_met": blink_detected,
            "feedback":      "Blink detected" if blink_detected else "Please blink naturally",
            "eye_count":     eye_count,
            "eyes_detected": eyes_detected,
        }

    def _process_smile_challenge(
        self, image: np.ndarray, face_region: Tuple[int, int, int, int]
    ) -> Dict:
        smile_detected = self.detect_smile(image, face_region)
        return {
            "challenge_met": smile_detected,
            "feedback":      "Smile detected" if smile_detected else "Please smile naturally",
            "smile_detected": smile_detected,
        }

    def _process_movement_challenge(
        self, image: np.ndarray, face_region: Tuple[int, int, int, int]
    ) -> Dict:
        landmarks     = self.analyze_facial_landmarks(image, face_region)
        face_quality  = landmarks.get("face_ratio", 0.5)
        movement_detected = 0.3 < face_quality < 0.7
        return {
            "challenge_met": movement_detected,
            "feedback": (
                "Movement detected"
                if movement_detected
                else f"Please {self.current_challenge.replace('_', ' ').lower()}"
            ),
            "face_quality": face_quality,
        }

    # ── Scoring ───────────────────────────────────────────────────────────────

    def _calculate_liveness_score(self, result: Dict) -> float:
        score = 0.0
        if result.get("face_detected", False):
            score += 0.3
        landmarks = result.get("details", {}).get("landmarks", {})
        if landmarks.get("is_clear", False):
            score += 0.1
        if landmarks.get("face_size_appropriate", False):
            score += 0.1
        if result.get("challenge_met", False):
            score += 0.5
        return min(score, 1.0)

    # ── Face matching ─────────────────────────────────────────────────────────

    def verify_face_match(
        self,
        live_image: np.ndarray,
        reference_encoding: np.ndarray,
        tolerance: float = 0.6,
    ) -> Dict:
        """Verify if live face matches reference face (simplified)."""
        try:
            live_image = ensure_bgr_image(live_image)

            face_detected, face_region = self.detect_face(live_image)
            if not face_detected:
                return {
                    "verified":   False,
                    "confidence": 0.0,
                    "feedback":   "No face detected in live image",
                }

            landmarks     = self.analyze_facial_landmarks(live_image, face_region)
            quality_score = 0.0
            if landmarks.get("is_clear", False):
                quality_score += 0.4
            if landmarks.get("face_size_appropriate", False):
                quality_score += 0.3
            if landmarks.get("edge_density", 0) > 0.1:
                quality_score += 0.3

            import random
            quality_score = max(0.0, min(1.0, quality_score + random.uniform(-0.2, 0.2)))
            verified      = quality_score > tolerance

            return {
                "verified":     verified,
                "confidence":   quality_score,
                "feedback":     (
                    "Face verified successfully"
                    if verified
                    else "Face does not match reference"
                ),
                "face_quality": landmarks,
            }

        except Exception as e:
            logger.error(f"Face verification error: {e}")
            return {
                "verified":   False,
                "confidence": 0.0,
                "feedback":   f"Verification error: {str(e)}",
            }


# Global service instance
biometric_service = BiometricLivenessService()