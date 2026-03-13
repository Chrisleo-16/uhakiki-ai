import cv2
import pytesseract
import re
import numpy as np
from typing import Optional


class OCRModel:
    """
    Improved OCR engine for Kenyan National ID cards.
    Handles colored backgrounds, noise, and field-specific extraction.
    """

    # --- Tesseract configs ---
    # PSM 6 = Assume a uniform block of text (good for ID fields)
    # PSM 7 = Single text line (good for individual fields)
    _CONFIG_BLOCK = "--oem 3 --psm 6 -l eng"
    _CONFIG_LINE  = "--oem 3 --psm 7 -l eng"

    # --- Kenyan ID field regions (as fraction of card width/height) ---
    # These are approximate crops targeting specific label areas.
    # Tune these ratios against your actual card image dimensions.
    _REGIONS = {
        "surname":     (0.30, 0.10, 0.85, 0.25),   # (x1, y1, x2, y2) relative
        "first_name":  (0.30, 0.22, 0.85, 0.38),
        "sex":         (0.30, 0.35, 0.55, 0.50),
        "nationality": (0.55, 0.35, 0.90, 0.50),
        "dob":         (0.55, 0.48, 0.90, 0.62),
        "id_number":   (0.30, 0.55, 0.85, 0.70),
        "expiry":      (0.30, 0.68, 0.85, 0.82),
        "place_issue": (0.30, 0.80, 0.85, 0.95),
    }

    # ------------------------------------------------------------------ #
    #  PUBLIC API                                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def extract_and_validate(image_content: bytes) -> dict:
        """
        Main entry point. Accepts raw image bytes, returns structured dict.
        """
        img = OCRModel._decode_image(image_content)
        preprocessed = OCRModel._preprocess(img)

        # Full-card OCR (fallback / raw text)
        raw_text = pytesseract.image_to_string(
            preprocessed, config=OCRModel._CONFIG_BLOCK
        ).upper()

        # Field-level OCR using region crops
        fields = OCRModel._extract_fields(preprocessed)

        # Post-process & validate each field
        result = OCRModel._build_result(raw_text, fields)
        return result

    # ------------------------------------------------------------------ #
    #  IMAGE LOADING                                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _decode_image(image_content: bytes) -> np.ndarray:
        nparr = np.frombuffer(image_content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image bytes.")
        # Ensure BGR (3-channel)
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        return img

    # ------------------------------------------------------------------ #
    #  PRE-PROCESSING PIPELINE                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _preprocess(img: np.ndarray) -> np.ndarray:
        """
        Multi-step pipeline designed for colored ID cards:
          1. Upscale  — Tesseract works best at ~300 DPI; small crops need upscaling
          2. Denoise  — removes JPEG / scan noise before thresholding
          3. Grayscale
          4. CLAHE    — adaptive contrast (handles uneven lighting on ID gradients)
          5. Adaptive threshold — much better than Otsu on colored/gradient backgrounds
          6. Deskew   — straighten slightly rotated scans
        """
        # 1. Upscale if the image is small
        h, w = img.shape[:2]
        scale = max(1, 1000 // max(h, w))   # target ~1000px on longest side
        if scale > 1:
            img = cv2.resize(img, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)

        # 2. Fast non-local means denoising
        denoised = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)

        # 3. Grayscale
        gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)

        # 4. CLAHE for adaptive contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # 5. Adaptive thresholding (handles gradients that break Otsu)
        thresh = cv2.adaptiveThreshold(
            enhanced, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=15,   # moderate block size for better detail preservation
            C=5
        )

        # 6. Morphological cleanup — remove tiny specks
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        # 7. Deskew
        cleaned = OCRModel._deskew(cleaned)

        return cleaned

    @staticmethod
    def _deskew(img: np.ndarray) -> np.ndarray:
        """Rotate image to correct small skew angles."""
        coords = np.column_stack(np.where(img < 128))   # dark pixels
        if len(coords) < 5:
            return img
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        if abs(angle) < 0.5:    # skip trivial rotations
            return img
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            img, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        return rotated

    # ------------------------------------------------------------------ #
    #  REGION-BASED OCR                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _extract_fields(preprocessed: np.ndarray) -> dict:
        """Crop each labeled region and OCR it separately."""
        h, w = preprocessed.shape[:2]
        fields = {}
        for field, (x1r, y1r, x2r, y2r) in OCRModel._REGIONS.items():
            x1, y1 = int(x1r * w), int(y1r * h)
            x2, y2 = int(x2r * w), int(y2r * h)
            crop = preprocessed[y1:y2, x1:x2]
            if crop.size == 0:
                fields[field] = ""
                continue
            # Add white border padding — helps Tesseract at edges
            crop = cv2.copyMakeBorder(crop, 10, 10, 10, 10,
                                      cv2.BORDER_CONSTANT, value=255)
            text = pytesseract.image_to_string(
                crop, config=OCRModel._CONFIG_LINE
            ).strip().upper()
            fields[field] = OCRModel._clean(text)
        return fields

    # ------------------------------------------------------------------ #
    #  POST-PROCESSING & VALIDATION                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _clean(text: str) -> str:
        """Remove OCR junk characters, keep alphanumeric + spaces + dots."""
        return re.sub(r"[^A-Z0-9 ./\-]", "", text).strip()

    @staticmethod
    def _extract_id_number(text: str) -> Optional[str]:
        """Find an 8-digit Kenyan ID number."""
        match = re.search(r'\b\d{8}\b', text)
        return match.group(0) if match else None

    @staticmethod
    def _extract_date(text: str) -> Optional[str]:
        """Find dates in DD.MM.YYYY or DD/MM/YYYY format."""
        match = re.search(r'\b(\d{2}[./]\d{2}[./]\d{4})\b', text)
        return match.group(1) if match else None

    @staticmethod
    def _extract_sex(text: str) -> Optional[str]:
        if "MALE" in text:
            return "MALE"
        if "FEMALE" in text:
            return "FEMALE"
        return None

    @staticmethod
    def _extract_nationality(text: str) -> Optional[str]:
        match = re.search(r'\b(KEN|KENYA|KENYAN)\b', text)
        return "KEN" if match else None

    @staticmethod
    def _build_result(raw_text: str, fields: dict) -> dict:
        """Combine field-level and full-text extraction into final output."""

        # Try field-level first, fall back to full raw_text scan
        def field_or_raw(field_key, extractor_fn=None):
            val = fields.get(field_key, "")
            if val and extractor_fn:
                result = extractor_fn(val)
                if result:
                    return result
            # Fallback to full raw text
            if extractor_fn:
                return extractor_fn(raw_text)
            return val or None

        id_number = field_or_raw("id_number", OCRModel._extract_id_number)
        dob        = field_or_raw("dob",       OCRModel._extract_date)
        expiry     = field_or_raw("expiry",    OCRModel._extract_date)
        sex        = OCRModel._extract_sex(raw_text)
        nationality = OCRModel._extract_nationality(raw_text)

        return {
            # Structured fields
            "full_name":    f"{fields.get('surname', '')} {fields.get('first_name', '')}".strip() or None,
            "surname":      fields.get("surname") or None,
            "first_name":   fields.get("first_name") or None,
            "id_number":    id_number,
            "date_of_birth": dob,
            "expiry_date":  expiry,
            "sex":          sex,
            "nationality":  nationality,
            "place_of_issue": fields.get("place_issue") or None,

            # Meta
            "raw_text":     raw_text,
            "is_kenyan_id": "REPUBLIC OF KENYA" in raw_text or "JAMHURI YA KENYA" in raw_text,
            "is_academic":  "CERTIFICATE" in raw_text or "EXAMINATION" in raw_text,
        }