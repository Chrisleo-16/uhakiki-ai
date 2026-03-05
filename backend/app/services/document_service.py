"""
Document Scanning Service
Handles document upload, processing, and forgery detection
"""

import cv2
import numpy as np
import base64
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import os
import json
from PIL import Image
import pytesseract
import re

from app.logic.image_utils import ensure_bgr_image, ensure_gray_image, decode_image_safe

logger = logging.getLogger(__name__)

class DocumentScanningService:
    """Service for document scanning and forgery detection"""
    
    def __init__(self):
        # Initialize OCR
        try:
            pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
        except:
            logger.warning("Tesseract not found - OCR functionality limited")
        
        # Document patterns for Kenyan documents
        self.document_patterns = {
            "national_id": {
                "patterns": [
                    r"\b\d{8}\b",  # 8-digit ID number
                    r"Republic of Kenya",
                    r"National Identity Card",
                    r"Date of Birth",
                    r"Serial No"
                ],
                "required_fields": ["id_number", "name", "date_of_birth"]
            },
            "passport": {
                "patterns": [
                    r"[A-Z]\d{7}",  # Passport number format
                    r"Republic of Kenya",
                    r"Passport",
                    r"Date of Birth",
                    r"Place of Birth"
                ],
                "required_fields": ["passport_number", "name", "nationality"]
            }
        }
    
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
            
            # Ensure image is 3-channel BGR (handle grayscale PNGs)
            image = ensure_bgr_image(image)
            
            return image
        except Exception as e:
            logger.error(f"Error decoding base64 image: {e}")
            return None
    
    def preprocess_document(self, image: np.ndarray) -> np.ndarray:
        """Preprocess document image for analysis"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Noise reduction
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # Perspective correction (simplified)
            # In production, would use more sophisticated edge detection
            edges = cv2.Canny(enhanced, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Find largest contour (assumed to be document)
                largest_contour = max(contours, key=cv2.contourArea)
                if cv2.contourArea(largest_contour) > image.shape[0] * image.shape[1] * 0.5:
                    # Approximate rectangle and apply perspective transform
                    epsilon = 0.02 * cv2.arcLength(largest_contour, True)
                    approx = cv2.approxPolyDP(largest_contour, epsilon, True)
                    
                    if len(approx) == 4:
                        # Apply perspective correction
                        pts = approx.reshape(4, 2).astype('float32')
                        rect = cv2.boundingRect(pts)
                        corrected = enhanced[rect[1]:rect[1]+rect[3], rect[0]:rect[0]+rect[2]]
                        return corrected
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Document preprocessing error: {e}")
            return image
    
    def extract_text(self, image: np.ndarray) -> str:
        """Extract text from document using OCR"""
        try:
            # Use PIL for better OCR results
            pil_image = Image.fromarray(image)
            
            # Configure Tesseract for better results
            custom_config = r'--oem 3 --psm 6 -l eng'
            text = pytesseract.image_to_string(pil_image, config=custom_config)
            
            return text.strip()
        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
            return ""
    
    def detect_document_type(self, text: str) -> str:
        """Detect document type based on extracted text"""
        text_lower = text.lower()
        
        if "national identity" in text_lower or "id card" in text_lower:
            return "national_id"
        elif "passport" in text_lower:
            return "passport"
        elif "birth certificate" in text_lower:
            return "birth_certificate"
        else:
            return "unknown"
    
    def extract_document_fields(self, text: str, doc_type: str) -> Dict:
        """Extract specific fields from document text"""
        try:
            fields = {}
            
            if doc_type == "national_id":
                # Extract ID number
                id_match = re.search(r"\b\d{8}\b", text)
                if id_match:
                    fields["id_number"] = id_match.group()
                
                # Extract name (simplified - would need more sophisticated NLP)
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    if "Name" in line or "name" in line:
                        if i + 1 < len(lines):
                            fields["name"] = lines[i + 1].strip()
                        break
                
                # Extract date of birth
                dob_match = re.search(r"(\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})", text)
                if dob_match:
                    fields["date_of_birth"] = dob_match.group()
            
            elif doc_type == "passport":
                # Extract passport number
                passport_match = re.search(r"[A-Z]\d{7}", text)
                if passport_match:
                    fields["passport_number"] = passport_match.group()
                
                # Extract nationality
                if "Kenya" in text or "kenya" in text:
                    fields["nationality"] = "Kenyan"
            
            return fields
            
        except Exception as e:
            logger.error(f"Field extraction error: {e}")
            return {}
    
    def analyze_document_quality(self, image: np.ndarray) -> Dict:
        """Analyze document image quality"""
        try:
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
            
            # Calculate quality metrics
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Sharpness (Laplacian variance)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Noise estimation
            noise = np.std(cv2.subtract(gray, cv2.GaussianBlur(gray, (5, 5), 0)))
            
            # Brightness and contrast
            brightness = np.mean(gray)
            contrast = np.std(gray)
            
            # Edge density (text presence)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (gray.shape[0] * gray.shape[1])
            
            # Color analysis (for security features)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            color_variance = np.var(hsv)
            
            return {
                "sharpness": float(laplacian_var),
                "noise_level": float(noise),
                "brightness": float(brightness),
                "contrast": float(contrast),
                "edge_density": float(edge_density),
                "color_variance": float(color_variance),
                "quality_score": self._calculate_quality_score(laplacian_var, noise, edge_density),
                "is_acceptable": bool(laplacian_var > 50 and edge_density > 0.05)
            }
            
        except Exception as e:
            logger.error(f"Quality analysis error: {e}")
            return {}
    
    def _calculate_quality_score(self, sharpness: float, noise: float, edge_density: float) -> float:
        """Calculate overall document quality score"""
        score = 0.0
        
        # Sharpness (40%)
        if sharpness > 100:
            score += 0.4
        elif sharpness > 50:
            score += 0.3
        elif sharpness > 20:
            score += 0.2
        
        # Noise level (20%)
        if noise < 10:
            score += 0.2
        elif noise < 20:
            score += 0.1
        
        # Edge density (40%)
        if edge_density > 0.1:
            score += 0.4
        elif edge_density > 0.05:
            score += 0.3
        elif edge_density > 0.02:
            score += 0.2
        
        return min(score, 1.0)
    
    def detect_forgery_indicators(self, image: np.ndarray, text: str, doc_type: str) -> Dict:
        """Detect potential forgery indicators"""
        try:
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
            
            indicators = []
            risk_score = 0.0
            
            # Analyze image quality
            quality = self.analyze_document_quality(image)
            
            # Check for quality issues
            if quality.get("sharpness", 0) < 20:
                indicators.append("Low image sharpness - possible photocopy")
                risk_score += 0.2
            
            if quality.get("noise_level", 0) > 30:
                indicators.append("High noise level - possible digital manipulation")
                risk_score += 0.15
            
            if quality.get("edge_density", 0) < 0.02:
                indicators.append("Low text density - possible blank document")
                risk_score += 0.25
            
            # Check text consistency
            if not text.strip():
                indicators.append("No text extracted - possible fake document")
                risk_score += 0.3
            else:
                # Check for common forgery patterns in text
                if len(text) < 50:
                    indicators.append("Insufficient text content")
                    risk_score += 0.1
                
                # Check for suspicious patterns
                if "SAMPLE" in text.upper() or "SPECIMEN" in text.upper():
                    indicators.append("Sample document detected")
                    risk_score += 0.4
                
                if "TEMPLATE" in text.upper():
                    indicators.append("Template document detected")
                    risk_score += 0.3
            
            # Document-specific checks
            if doc_type == "national_id":
                fields = self.extract_document_fields(text, doc_type)
                if not fields.get("id_number"):
                    indicators.append("Missing ID number")
                    risk_score += 0.2
                
                if not fields.get("name"):
                    indicators.append("Missing name field")
                    risk_score += 0.15
            
            # Check for digital manipulation signs
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Check for uniform areas (possible cloning)
            uniform_areas = np.sum(np.abs(cv2.subtract(gray, cv2.GaussianBlur(gray, (21, 21), 0))) < 5)
            if uniform_areas > image.shape[0] * image.shape[1] * 0.3:
                indicators.append("Unusually uniform areas detected")
                risk_score += 0.2
            
            return {
                "indicators": indicators,
                "risk_score": min(risk_score, 1.0),
                "risk_level": self._determine_risk_level(risk_score),
                "quality_analysis": quality,
                "text_length": len(text),
                "document_type": doc_type
            }
            
        except Exception as e:
            logger.error(f"Forgery detection error: {e}")
            return {
                "indicators": ["Analysis failed"],
                "risk_score": 0.5,
                "risk_level": "medium",
                "error": str(e)
            }
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level based on score"""
        if risk_score >= 0.7:
            return "high"
        elif risk_score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def process_document(self, base64_image: str, expected_type: Optional[str] = None) -> Dict:
        """Complete document processing pipeline"""
        try:
            # Decode image
            image = self.decode_base64_image(base64_image)
            if image is None:
                return {
                    "success": False,
                    "error": "Invalid image format"
                }
            
            # Preprocess
            processed_image = self.preprocess_document(image)
            
            # Extract text
            text = self.extract_text(processed_image)
            
            # Detect document type
            doc_type = expected_type or self.detect_document_type(text)
            
            # Extract fields
            fields = self.extract_document_fields(text, doc_type)
            
            # Analyze quality - use original image, not preprocessed (which is grayscale)
            quality = self.analyze_document_quality(image)
            
            # Detect forgery - use original image, not preprocessed (which is grayscale)
            forgery_analysis = self.detect_forgery_indicators(image, text, doc_type)
            
            # Overall assessment
            overall_score = (quality.get("quality_score", 0) * 0.4) + ((1 - forgery_analysis.get("risk_score", 0)) * 0.6)
            
            return {
                "success": True,
                "document_type": doc_type,
                "extracted_fields": fields,
                "quality_analysis": quality,
                "forgery_analysis": forgery_analysis,
                "overall_score": overall_score,
                "verification_status": "PASS" if overall_score > 0.7 else "REQUIRES_REVIEW" if overall_score > 0.4 else "FAIL",
                "extracted_text": text[:500] + "..." if len(text) > 500 else text,  # Truncate for response
                "processing_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Document processing error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Global service instance
document_service = DocumentScanningService()
