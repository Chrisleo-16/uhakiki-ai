"""
Reference Face Extraction Module
Extracts and stores face templates from ID cards for MBIC verification
"""

import cv2
import face_recognition
import numpy as np
import base64
import io
from typing import Optional, Tuple, Dict, Any
import logging
# Change line 14 in app/logic/face_extractor.py to:
from PIL import Image, ImageOps
from app.db.milvus_client import store_in_vault, search_vault, get_face_encoding

logger = logging.getLogger(__name__)

class FaceExtractor:
    """
    Extracts face templates from ID cards and stores them as reference encodings
    """
    
    def __init__(self):
        self.encoding_tolerance = 0.6  # Tolerance for face detection
        self.min_face_size = 50  # Minimum face size in pixels
        
    def extract_face_from_id_card(self, image_data: bytes, student_id: str) -> Dict[str, Any]:
        """
        Extract face from ID card and create reference encoding
        
        Args:
            image_data: ID card image bytes
            student_id: Student identifier for storage
            
        Returns:
            Dictionary with extraction results and face encoding
        """
        try:
            # Fix EXIF orientation before anything else (mobile uploads are often rotated)
            image_data = self._fix_orientation(image_data)

            # Convert bytes to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return {
                    "success": False,
                    "error": "Invalid image format",
                    "encoding": None
                }

            # Enhance image before detection (sharpening + contrast)
            image = self.enhance_image(image)

            # Convert to RGB for face_recognition
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect faces in the ID card
            # number_of_times_to_upsample=2 helps detect small faces in ID card photos
            face_locations = face_recognition.face_locations(
                rgb_image,
                model="hog",
                number_of_times_to_upsample=2
            )

            # Fallback to Haar Cascade if HOG fails
            if not face_locations:
                logger.info("HOG detected no faces, falling back to Haar Cascade...")
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                face_locations = self._detect_with_haar(gray)
            
            if not face_locations:
                return {
                    "success": False,
                    "error": "No face detected in ID card",
                    "encoding": None,
                    "suggestion": "Ensure ID card photo is clear and facing forward"
                }
            
            # Use the largest face found (most likely the person)
            largest_face = self._get_largest_face(face_locations)
            top, right, bottom, left = largest_face
            
            # Extract face encoding
            face_encodings = face_recognition.face_encodings(rgb_image, [largest_face])
            
            if not face_encodings:
                return {
                    "success": False,
                    "error": "Could not generate face encoding",
                    "encoding": None
                }
            
            face_encoding = face_encodings[0]
            
            # Create face crop for visual reference
            face_crop = rgb_image[top:bottom, left:right]
            face_crop_resized = cv2.resize(face_crop, (150, 150))
            
            # Convert face crop to base64 for storage
            _, buffer = cv2.imencode('.jpg', face_crop_resized)
            face_crop_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Store in vault
            storage_result = self._store_face_encoding(
                student_id, 
                face_encoding, 
                face_crop_base64,
                image.shape
            )
            
            return {
                "success": True,
                "encoding": face_encoding.tolist(),
                "face_crop": face_crop_base64,
                "face_location": largest_face,
                "confidence": self._calculate_detection_confidence(largest_face, image.shape),
                "storage_result": storage_result
            }
            
        except Exception as e:
            logger.error(f"Face extraction failed: {str(e)}")
            return {
                "success": False,
                "error": f"Face extraction error: {str(e)}",
                "encoding": None
            }

    def _fix_orientation(self, image_data: bytes) -> bytes:
        """
        Fix EXIF orientation on mobile-captured images before processing.
        Mobile uploads are frequently rotated 90/180/270 degrees.
        """
        try:
            pil_img = PIL.Image.open(io.BytesIO(image_data))
            pil_img = PIL.ImageOps.exif_transpose(pil_img)
            buf = io.BytesIO()
            pil_img.save(buf, format='JPEG')
            return buf.getvalue()
        except Exception as e:
            logger.warning(f"Could not fix EXIF orientation: {str(e)}. Proceeding with original.")
            return image_data

    def _detect_with_haar(self, gray_image: np.ndarray):
        """
        Fallback face detector using OpenCV's Haar Cascade.
        Used when HOG fails on particularly small or low-quality ID card photos.
        Returns locations in face_recognition format: (top, right, bottom, left)
        """
        cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = cascade.detectMultiScale(
            gray_image,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        if len(faces) == 0:
            return []
        # Convert OpenCV format (x, y, w, h) → face_recognition format (top, right, bottom, left)
        return [(y, x + w, y + h, x) for (x, y, w, h) in faces]

    def _get_largest_face(self, face_locations) -> Tuple[int, int, int, int]:
        """Return the largest face from detected faces"""
        if len(face_locations) == 1:
            return face_locations[0]
        
        # Calculate face areas and return the largest
        largest_face = None
        max_area = 0
        
        for face_location in face_locations:
            top, right, bottom, left = face_location
            area = (bottom - top) * (right - left)
            if area > max_area:
                max_area = area
                largest_face = face_location
        
        return largest_face
    
    def _calculate_detection_confidence(self, face_location: Tuple[int, int, int, int], image_shape: Tuple[int, int, int]) -> float:
        """Calculate confidence score based on face size relative to image"""
        top, right, bottom, left = face_location
        face_area = (bottom - top) * (right - left)
        image_area = image_shape[0] * image_shape[1]
        
        # Larger faces relative to image size get higher confidence
        size_ratio = face_area / image_area
        
        # Map to confidence score (0.0 to 1.0)
        if size_ratio > 0.05:  # Face covers more than 5% of image
            return min(1.0, size_ratio * 10)
        else:
            return size_ratio * 10
    
    def _store_face_encoding(self, student_id: str, encoding: np.ndarray, face_crop: str, image_shape: Tuple[int, int, int]) -> Dict[str, Any]:
        """Store face encoding in Milvus vault"""
        try:
            # Create storage record
            face_record = {
                "content": f"face_encoding_{student_id}",
                "metadata": {
                    "student_id": student_id,
                    "type": "face_encoding",
                    "encoding": encoding.tolist(),
                    "face_crop": face_crop,
                    "image_shape": image_shape,
                    "timestamp": str(np.datetime64('now')),
                    "encoding_length": len(encoding)
                }
            }
            
            # Store in vault
            success = store_in_vault([face_record])
            
            return {
                "success": success,
                "student_id": student_id,
                "encoding_length": len(encoding)
            }
            
        except Exception as e:
            logger.error(f"Failed to store face encoding: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_reference_encoding(self, student_id: str) -> Optional[np.ndarray]:
        """Retrieve stored face encoding for a student"""
        try:
            # get_face_encoding handles the prefix and np.array conversion internally
            return get_face_encoding(student_id)
        except Exception as e:
            logger.error(f"Failed to retrieve face encoding: {str(e)}")
            return None
    
    def verify_face_match(self, student_id: str, live_encoding: np.ndarray, tolerance: float = 0.6) -> Dict[str, Any]:
        """Verify live face against stored reference"""
        try:
            reference_encoding = self.get_reference_encoding(student_id)
            
            if reference_encoding is None:
                return {
                    "success": False,
                    "error": "No reference face found for student",
                    "verified": False,
                    "distance": None
                }
            
            # Compare faces
            distance = face_recognition.face_distance([reference_encoding], live_encoding)[0]
            verified = distance <= tolerance
            
            return {
                "success": True,
                "verified": verified,
                "distance": float(distance),
                "tolerance": tolerance,
                "confidence": max(0.0, (tolerance - distance) / tolerance) if verified else 0.0
            }
            
        except Exception as e:
            logger.error(f"Face verification failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "verified": False,
                "distance": None
            }

    def enhance_image(self, image: np.ndarray) -> np.ndarray:
        """
        Applies Unsharp Masking to improve edge clarity in slightly blurry images.
        """
        # 1. Convert to a sharper version using a Gaussian blur overlay
        gaussian_3 = cv2.GaussianBlur(image, (0, 0), 2.0)
        sharpened = cv2.addWeighted(image, 1.5, gaussian_3, -0.5, 0)
        
        # 2. Increase contrast slightly to help HOG detector
        lab = cv2.cvtColor(sharpened, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        final_image = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        
        return final_image


# Global instance
face_extractor = FaceExtractor()