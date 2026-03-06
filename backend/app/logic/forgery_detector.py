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

# ── Central image utilities (fixes all "Bad number of channels" errors) ────────
from app.logic.image_utils import ensure_bgr_image, ensure_gray_image, decode_image_safe

logger = logging.getLogger(__name__)


# Global service instance
_forgery_service = None


def get_forgery_service():
    """Get or create the global forgery detector service"""
    global _forgery_service
    if _forgery_service is None:
        _forgery_service = DocumentScanningService()
    return _forgery_service


def detect_pixel_anomalies(image: np.ndarray) -> Dict:
    """
    Detect pixel-level anomalies in document images for forgery detection.
    This is the main entry point used by the verification pipeline.
    
    Args:
        image: Input image as numpy array (BGR format)
        
    Returns:
        Dictionary containing:
            - mse_score: Mean Squared Error from reconstruction
            - is_forged: Boolean indicating potential forgery
            - anomaly_score: Overall anomaly score (0-1)
            - details: Additional analysis details
    """
    service = get_forgery_service()
    
    try:
        # Preprocess the image
        processed = service.preprocess_document(image)
        
        # Extract text for analysis
        text = service.extract_text(processed)
        
        # Detect document type
        doc_type = service.detect_document_type(text)
        
        # Get forgery indicators
        forgery_results = service.detect_forgery_indicators(image, text, doc_type)
        
        # Also run quality analysis
        quality = service.analyze_document_quality(image)
        
        # Combine results
        return {
            "mse_score": forgery_results.get("risk_score", 0.5),
            "is_forged": forgery_results.get("risk_level") == "high",
            "anomaly_score": forgery_results.get("risk_score", 0.5),
            "forgery_indicators": forgery_results.get("indicators", []),
            "risk_level": forgery_results.get("risk_level", "unknown"),
            "quality_analysis": quality,
            "document_type": doc_type,
            "extracted_text_length": len(text)
        }
        
    except Exception as e:
        logger.error(f"Error in detect_pixel_anomalies: {e}")
        return {
            "mse_score": 0.0,
            "is_forged": False,
            "anomaly_score": 0.0,
            "error": str(e)
        }


def calculate_forgery_score(image: np.ndarray) -> float:
    """
    Calculate a forgery score for the given document image.
    
    Args:
        image: Input image as numpy array (BGR format)
        
    Returns:
        Forgery score between 0 (not forged) and 1 (definitely forged)
    """
    result = detect_pixel_anomalies(image)
    return result.get("anomaly_score", 0.5)


def get_reconstruction(image: np.ndarray) -> np.ndarray:
    """
    Get the reconstruction of the image from the autoencoder.
    For now, returns the preprocessed image as a placeholder.
    
    Args:
        image: Input image as numpy array (BGR format)
        
    Returns:
        Reconstructed image
    """
    service = get_forgery_service()
    try:
        processed = service.preprocess_document(image)
        return processed
    except Exception as e:
        logger.error(f"Error in get_reconstruction: {e}")
        return image


class DocumentScanningService:
    """Service for document scanning and forgery detection"""

    def __init__(self):
        try:
            pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
        except Exception:
            logger.warning("Tesseract not found - OCR functionality limited")

        self.document_patterns = {
            "national_id": {
                "patterns": [
                    r"\b\d{8}\b",
                    r"Republic of Kenya",
                    r"National Identity Card",
                    r"Date of Birth",
                    r"Serial No",
                ],
                "required_fields": ["id_number", "name", "date_of_birth"],
            },
            "passport": {
                "patterns": [
                    r"[A-Z]\d{7}",
                    r"Republic of Kenya",
                    r"Passport",
                    r"Date of Birth",
                    r"Place of Birth",
                ],
                "required_fields": ["passport_number", "name", "nationality"],
            },
        }

    # ── Image I/O ─────────────────────────────────────────────────────────────

    def decode_base64_image(self, base64_string: str) -> Optional[np.ndarray]:
        """Decode base64 image string → guaranteed 3-channel BGR ndarray."""
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

    # ── Pre-processing ────────────────────────────────────────────────────────

    def preprocess_document(self, image: np.ndarray) -> np.ndarray:
        """Pre-process document image for OCR analysis."""
        try:
            # Always work from a guaranteed-BGR image
            image = ensure_bgr_image(image)
            gray  = ensure_gray_image(image)

            denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

            clahe    = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)

            binary = cv2.adaptiveThreshold(
                enhanced, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
                11, 2,
            )

            kernel  = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

            edges     = cv2.Canny(cleaned, 50, 150)
            contours, _ = cv2.findContours(
                edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            if contours:
                largest = max(contours, key=cv2.contourArea)
                if cv2.contourArea(largest) > image.shape[0] * image.shape[1] * 0.5:
                    epsilon = 0.02 * cv2.arcLength(largest, True)
                    approx  = cv2.approxPolyDP(largest, epsilon, True)
                    if len(approx) == 4:
                        pts  = approx.reshape(4, 2).astype('float32')
                        rect = cv2.boundingRect(pts)
                        return cleaned[
                            rect[1]:rect[1] + rect[3],
                            rect[0]:rect[0] + rect[2],
                        ]

            return cleaned

        except Exception as e:
            logger.error(f"Document preprocessing error: {e}")
            return image

    # ── OCR ───────────────────────────────────────────────────────────────────

    def extract_text(self, image: np.ndarray) -> str:
        """Extract text from document using multi-pass OCR."""
        try:
            return self._multi_pass_ocr(image)
        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
            return ""

    def _multi_pass_ocr(self, image: np.ndarray, num_passes: int = 5) -> str:
        """
        Run multiple OCR passes with different pre-processing configs.
        Returns the pass that produced the most text.
        """
        best_text  = ""
        best_score = 0

        # Normalise once; work with gray + thresholded variants
        bgr  = ensure_bgr_image(image)
        gray = ensure_gray_image(bgr)

        clahe         = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced_gray = clahe.apply(gray)
        _, thresh     = cv2.threshold(
            enhanced_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        pil_enhanced = Image.fromarray(enhanced_gray)
        pil_thresh   = Image.fromarray(thresh)

        configs = [
            (pil_enhanced, '--oem 3 --psm 6 -l eng'),
            (pil_thresh,   '--oem 3 --psm 6 -l eng'),
            (pil_thresh,   '--oem 3 --psm 7 -l eng'),
            (pil_enhanced, '--oem 3 --psm 11 -l eng'),
            (pil_thresh,   '--oem 3 --psm 3 -l eng'),
        ]

        for pil_img, cfg in configs:
            try:
                text  = self._ocr_with_config(pil_img, cfg)
                score = len(text)
                if score > best_score:
                    best_score = score
                    best_text  = text
            except Exception:
                pass

        return best_text.strip()

    def _ocr_with_config(self, pil_image: Image.Image, config: str) -> str:
        return pytesseract.image_to_string(pil_image, config=config).strip()

    # ── Document type / field extraction ─────────────────────────────────────

    def detect_document_type(self, text: str) -> str:
        text_lower = text.lower()
        if "national identity" in text_lower or "id card" in text_lower:
            return "national_id"
        elif "passport" in text_lower:
            return "passport"
        elif "birth certificate" in text_lower:
            return "birth_certificate"
        return "unknown"

    def extract_document_fields(self, text: str, doc_type: str) -> Dict:
        """Extract specific fields from document text."""
        try:
            fields     = {}
            text_clean = self._clean_ocr_text(text)
            lines      = text_clean.split('\n')

            if doc_type == "national_id":
                # ── ID number ──────────────────────────────────────────────
                for m in re.findall(r'\b\d{8}\b', text_clean):
                    first_four = int(m[:4])
                    if not (1900 <= first_four <= 2100):
                        fields["id_number"] = m
                        break

                if "id_number" not in fields:
                    id_patterns = [
                        r'(?:ID No|ID Number|Serial No|Serial|No\.?|Number)[:\s\\.]*(\d{6,9})',
                        r'(\d{8})(?=\s|$|\n)',
                    ]
                    for pat in id_patterns:
                        m = re.search(pat, text_clean, re.IGNORECASE)
                        if m and len(m.group(1)) == 8:
                            fields["id_number"] = m.group(1)
                            break

                if "id_number" not in fields:
                    for i, line in enumerate(lines):
                        if any(kw in line.lower() for kw in ['id', 'number', 'serial', 'no']):
                            for j in range(max(0, i - 2), min(len(lines), i + 3)):
                                if i != j:
                                    m = re.search(r'\b\d{8}\b', lines[j])
                                    if m:
                                        fields["id_number"] = m.group()
                                        break

                # ── Name ──────────────────────────────────────────────────
                name_found = False
                for i, line in enumerate(lines):
                    if "name" in line.lower() and len(line) < 30:
                        if i + 1 < len(lines):
                            candidate = re.sub(r'[^a-zA-Z\s]', '', lines[i + 1].strip())
                            if 2 < len(candidate) < 50:
                                fields["name"] = candidate.title()
                                name_found = True
                                break

                if not name_found:
                    skip_words = {
                        'REPUBLIC', 'KENYA', 'NATIONAL', 'IDENTITY',
                        'CARD', 'DATE', 'BIRTH', 'SEX', 'MALE', 'FEMALE',
                        'PLACE', 'EXPIRY',
                    }
                    for line in lines:
                        line = line.strip()
                        if len(line) < 3 or line.isdigit():
                            continue
                        if line.isupper() and not any(w in line for w in skip_words):
                            clean = re.sub(r'[^a-zA-Z\s]', '', line)
                            if len(clean) > 3:
                                fields["name"] = clean.title()
                                break

                # ── Date of birth ─────────────────────────────────────────
                for pat in [
                    r'Date of Birth[:\s]*(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})',
                    r'DOB[:\s]*(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})',
                    r'(\d{1,2}[/.-]\d{1,2}[/.-]\d{4})(?=\s|$|\n)',
                ]:
                    m = re.search(pat, text_clean, re.IGNORECASE)
                    if m:
                        fields["date_of_birth"] = m.group(1)
                        break

                # ── Gender ────────────────────────────────────────────────
                text_upper = text_clean.upper()
                if "SEX" in text_upper or "GENDER" in text_upper:
                    m = re.search(r'(?:SEX|GENDER)[:\s]*([MF])', text_upper)
                    if m:
                        fields["gender"] = "Male" if m.group(1) == "M" else "Female"
                    elif "FEMALE" in text_upper:
                        fields["gender"] = "Female"
                    elif "MALE" in text_upper:
                        fields["gender"] = "Male"

                # ── Place of birth ────────────────────────────────────────
                m = re.search(
                    r'Place of Birth[:\s]*([A-Za-z\s]+?)(?=\n|$)', text_clean
                )
                if m:
                    fields["place_of_birth"] = m.group(1).strip()

                # ── Expiry ────────────────────────────────────────────────
                m = re.search(
                    r'(?:Expiry|Date of Expiry)[:\s]*(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})',
                    text_clean, re.IGNORECASE,
                )
                if m:
                    fields["expiry_date"] = m.group(1)

            elif doc_type == "passport":
                m = re.search(r'\b([A-Z]\d{7,8})\b', text_clean)
                if m:
                    fields["passport_number"] = m.group()
                if "Kenya" in text_clean:
                    fields["nationality"] = "Kenyan"
                m = re.search(
                    r'Name[:\s]*([A-Za-z\s]+?)(?=\n|$)', text_clean, re.IGNORECASE
                )
                if m:
                    fields["name"] = m.group(1).strip()

            return fields

        except Exception as e:
            logger.error(f"Field extraction error: {e}")
            return {}

    def _clean_ocr_text(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            if re.match(r'^[\W_]+$', line):
                continue
            lines.append(line)
        return '\n'.join(lines)

    # ── Quality analysis ──────────────────────────────────────────────────────

    def analyze_document_quality(self, image: np.ndarray) -> Dict:
        """Analyze document image quality metrics."""
        try:
            # Always normalise to BGR first, then derive gray
            bgr  = ensure_bgr_image(image)
            gray = ensure_gray_image(bgr)

            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            noise         = float(np.std(
                cv2.subtract(gray, cv2.GaussianBlur(gray, (5, 5), 0))
            ))
            brightness    = float(np.mean(gray))
            contrast      = float(np.std(gray))

            edges        = cv2.Canny(gray, 50, 150)
            edge_density = float(
                np.sum(edges > 0) / (gray.shape[0] * gray.shape[1])
            )

            # HSV requires BGR input – guaranteed above
            hsv            = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
            color_variance = float(np.var(hsv))

            return {
                "sharpness":      float(laplacian_var),
                "noise_level":    noise,
                "brightness":     brightness,
                "contrast":       contrast,
                "edge_density":   edge_density,
                "color_variance": color_variance,
                "quality_score":  self._calculate_quality_score(
                    laplacian_var, noise, edge_density
                ),
                "is_acceptable":  bool(laplacian_var > 50 and edge_density > 0.05),
            }

        except Exception as e:
            logger.error(f"Quality analysis error: {e}")
            return {}

    def _calculate_quality_score(
        self, sharpness: float, noise: float, edge_density: float
    ) -> float:
        score = 0.0
        if sharpness > 100:
            score += 0.4
        elif sharpness > 50:
            score += 0.3
        elif sharpness > 20:
            score += 0.2

        if noise < 10:
            score += 0.2
        elif noise < 20:
            score += 0.1

        if edge_density > 0.1:
            score += 0.4
        elif edge_density > 0.05:
            score += 0.3
        elif edge_density > 0.02:
            score += 0.2

        return min(score, 1.0)

    # ── Forgery detection ─────────────────────────────────────────────────────

    def detect_forgery_indicators(
        self, image: np.ndarray, text: str, doc_type: str
    ) -> Dict:
        """Detect potential forgery indicators."""
        try:
            # Normalise once; reuse bgr / gray throughout
            bgr  = ensure_bgr_image(image)
            gray = ensure_gray_image(bgr)

            indicators = []
            risk_score = 0.0

            quality = self.analyze_document_quality(bgr)

            if quality.get("sharpness", 0) < 20:
                indicators.append("Low image sharpness - possible photocopy")
                risk_score += 0.2

            if quality.get("noise_level", 0) > 30:
                indicators.append("High noise level - possible digital manipulation")
                risk_score += 0.15

            if quality.get("edge_density", 0) < 0.02:
                indicators.append("Low text density - possible blank document")
                risk_score += 0.25

            if not text.strip():
                indicators.append("No text extracted - possible fake document")
                risk_score += 0.3
            else:
                if len(text) < 50:
                    indicators.append("Insufficient text content")
                    risk_score += 0.1
                if "SAMPLE" in text.upper() or "SPECIMEN" in text.upper():
                    indicators.append("Sample document detected")
                    risk_score += 0.4
                if "TEMPLATE" in text.upper():
                    indicators.append("Template document detected")
                    risk_score += 0.3

            if doc_type == "national_id":
                fields = self.extract_document_fields(text, doc_type)
                if not fields.get("id_number"):
                    indicators.append("Missing ID number")
                    risk_score += 0.2
                if not fields.get("name"):
                    indicators.append("Missing name field")
                    risk_score += 0.15

            # Cloning / uniform-area check (works on gray)
            blurred      = cv2.GaussianBlur(gray, (21, 21), 0)
            uniform_areas = int(np.sum(
                np.abs(cv2.subtract(gray, blurred)) < 5
            ))
            if uniform_areas > gray.shape[0] * gray.shape[1] * 0.3:
                indicators.append("Unusually uniform areas detected")
                risk_score += 0.2

            return {
                "indicators":      indicators,
                "risk_score":      float(min(risk_score, 1.0)),
                "risk_level":      self._determine_risk_level(risk_score),
                "quality_analysis": quality,
                "text_length":     len(text),
                "document_type":   doc_type,
            }

        except Exception as e:
            logger.error(f"Forgery detection error: {e}")
            return {
                "indicators": ["Analysis failed"],
                "risk_score": 0.5,
                "risk_level": "medium",
                "error": str(e),
            }

    def _determine_risk_level(self, risk_score: float) -> str:
        if risk_score >= 0.7:
            return "high"
        elif risk_score >= 0.4:
            return "medium"
        return "low"

    # ── Main pipeline ─────────────────────────────────────────────────────────

    def process_document(
        self, base64_image: str, expected_type: Optional[str] = None
    ) -> Dict:
        """Complete document processing pipeline."""
        try:
            image = self.decode_base64_image(base64_image)
            if image is None:
                return {"success": False, "error": "Invalid image format"}

            processed_image = self.preprocess_document(image)
            text            = self.extract_text(processed_image)
            doc_type        = expected_type or self.detect_document_type(text)
            fields          = self.extract_document_fields(text, doc_type)

            # Use the original (BGR-guaranteed) image for quality / forgery
            quality          = self.analyze_document_quality(image)
            forgery_analysis = self.detect_forgery_indicators(image, text, doc_type)

            overall_score = (
                quality.get("quality_score", 0) * 0.4
                + (1 - forgery_analysis.get("risk_score", 0)) * 0.6
            )

            return {
                "success":           True,
                "document_type":     doc_type,
                "extracted_fields":  fields,
                "quality_analysis":  quality,
                "forgery_analysis":  forgery_analysis,
                "overall_score":     overall_score,
                "verification_status": (
                    "PASS" if overall_score > 0.7
                    else "REQUIRES_REVIEW" if overall_score > 0.4
                    else "FAIL"
                ),
                "extracted_text":    (
                    text[:500] + "..." if len(text) > 500 else text
                ),
                "processing_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Document processing error: {e}")
            return {"success": False, "error": str(e)}


# Global service instance
document_service = DocumentScanningService()