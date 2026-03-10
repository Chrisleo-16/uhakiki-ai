"""
Document Scanning Service — v3
Robust Kenyan National ID extraction.

KEY INSIGHT: Tesseract on real ID photos rarely produces clean keyword lines
like "SURNAME\\nLEO". Instead it produces noisy inline text such as:
  "SURNAME LEO GIVEN NAME CHRISBEN EVANS SEX MALE NATIONALITY KEN"
or mixed lines where labels and values appear on the same line.

Strategy: regex-first on the entire joined OCR text, not line-by-line.
Every field has its own targeted pattern that hunts the VALUE directly.
"""

import cv2
import numpy as np
import base64
import logging
from typing import Dict, List, Optional
from datetime import datetime
import re
from PIL import Image
import pytesseract

from app.logic.image_utils import ensure_bgr_image, ensure_gray_image, decode_image_safe

logger = logging.getLogger(__name__)


# ── Image / OCR utilities ─────────────────────────────────────────────────────

def _scale_up(gray: np.ndarray, min_width: int = 1400) -> np.ndarray:
    h, w = gray.shape[:2]
    if w < min_width:
        scale = min_width / w
        gray  = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    return gray


def _ocr_variants(image: np.ndarray) -> str:
    """
    Run multiple Tesseract preprocessing + config combos.
    Returns the text from whichever pass produced the most characters.
    """
    bgr  = ensure_bgr_image(image)
    gray = ensure_gray_image(bgr)
    gray = _scale_up(gray)

    clahe    = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    _, otsu = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    adapt   = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 13, 6
    )
    inv    = cv2.bitwise_not(otsu)
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharp  = cv2.filter2D(enhanced, -1, kernel)

    configs = [
        (enhanced, "--oem 3 --psm 6 -l eng"),
        (otsu,     "--oem 3 --psm 6 -l eng"),
        (adapt,    "--oem 3 --psm 6 -l eng"),
        (enhanced, "--oem 3 --psm 3 -l eng"),
        (otsu,     "--oem 3 --psm 11 -l eng"),
        (sharp,    "--oem 3 --psm 6 -l eng"),
        (inv,      "--oem 3 --psm 6 -l eng"),
        (enhanced, "--oem 3 --psm 4 -l eng"),
    ]

    best_text  = ""
    best_score = 0

    for img_arr, cfg in configs:
        try:
            text  = pytesseract.image_to_string(Image.fromarray(img_arr), config=cfg).strip()
            score = len(text)
            if score > best_score:
                best_score = score
                best_text  = text
        except Exception:
            pass

    # Also try on original (no preprocessing) — sometimes beats all of the above
    try:
        orig_rgb  = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        orig_text = pytesseract.image_to_string(
            Image.fromarray(orig_rgb), config="--oem 3 --psm 6 -l eng"
        ).strip()
        if len(orig_text) > best_score:
            best_text = orig_text
    except Exception:
        pass

    logger.info(f"OCR best length: {len(best_text)}")
    logger.debug(f"OCR raw:\n{best_text[:800]}")
    return best_text


def _clean(text: str) -> str:
    """Normalise whitespace; drop lines that are purely symbols."""
    lines = []
    for line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).strip()
        if line and not re.match(r"^[\W_]+$", line):
            lines.append(line)
    return "\n".join(lines)


# ── Field-level extractors ────────────────────────────────────────────────────

def _extract_id_number(text: str) -> str:
    """7–9 digit Kenyan ID number, excluding year-like values."""

    # Explicitly labelled
    m = re.search(
        r"(?:ID\s*(?:No|Number|Nambari|NUM)[.:\s]*|Serial\s*No[.:\s]*)\s*(\d{7,9})",
        text, re.IGNORECASE
    )
    if m:
        return m.group(1)

    # A standalone line that is ONLY 7–9 digits
    for line in text.split("\n"):
        stripped = re.sub(r"[\s.\-]", "", line)
        if re.fullmatch(r"\d{7,9}", stripped):
            val = int(stripped)
            if not (1900 <= val <= 2100):
                return stripped

    # Any 9-digit, then 8-digit, then 7-digit match anywhere
    for pat in [r"\b(\d{9})\b", r"\b(\d{8})\b", r"\b(\d{7})\b"]:
        for m in re.finditer(pat, text):
            val = int(m.group(1))
            if not (1900 <= val <= 2100):
                return m.group(1)

    return ""


def _extract_dates(text: str):
    """
    Return (dob, expiry).
    Handles: DD.MM.YYYY  DD. MM. YYYY  DD/MM/YYYY  DD-MM-YYYY
    Sort by year: smallest year = DOB, largest year = expiry.
    """
    pat = r"\b(\d{1,2})[.\s/\-]+(\d{1,2})[.\s/\-]+(\d{4})\b"
    dates = []
    for m in re.finditer(pat, text):
        d, mo, yr = m.group(1), m.group(2), m.group(3)
        if 1 <= int(d) <= 31 and 1 <= int(mo) <= 12 and 1900 <= int(yr) <= 2100:
            dates.append((int(yr), f"{d.zfill(2)}.{mo.zfill(2)}.{yr}"))
    dates.sort(key=lambda x: x[0])
    dob    = dates[0][1]  if len(dates) >= 1 else ""
    expiry = dates[-1][1] if len(dates) >= 2 else ""
    return dob, expiry


def _extract_sex(text: str) -> str:
    m = re.search(r"\bSEX[:\s]+([MF]\w*)", text, re.IGNORECASE)
    if m:
        v = m.group(1).upper()
        if v.startswith("F"): return "Female"
        if v.startswith("M"): return "Male"
    if re.search(r"\bFEMALE\b", text, re.I): return "Female"
    if re.search(r"\bMALE\b",   text, re.I): return "Male"
    return ""


def _extract_nationality(text: str) -> str:
    m = re.search(r"\bNATIONALITY[:\s]+([A-Z]{2,10})", text, re.IGNORECASE)
    if m:
        v = m.group(1).upper()
        return "Kenyan" if v in ("KEN", "KENYAN", "KENYA") else v.title()
    if re.search(r"\bKEN\b", text):         return "Kenyan"
    if re.search(r"\bKENYAN\b", text, re.I): return "Kenyan"
    return ""


def _extract_name(text: str) -> str:
    """
    Regex-first name extraction. Handles both inline-label and
    separate-line layouts from Tesseract output.
    """
    lines  = [l.strip() for l in text.split("\n") if l.strip()]
    joined = " ".join(lines)

    # ── A: "SURNAME <val> GIVEN NAME <val> SEX|DATE|..." (inline, single line) ──
    m = re.search(
        r"SURNAME[:\s]+([A-Z][A-Z\s]{1,30}?)\s+GIVEN\s*NAME[:\s]+([A-Z][A-Z\s]{1,40}?)"
        r"(?=\s+(?:SEX|DATE|PLACE|ID|NATIONAL|DOB|KEN|\d)|$)",
        joined, re.IGNORECASE
    )
    if m:
        return f"{m.group(1).strip()} {m.group(2).strip()}".title()

    # ── B: keyword line, value on next line ─────────────────────────────────
    for i, line in enumerate(lines):
        up = line.upper().strip()
        if up in ("SURNAME", "JINA LA UKOO"):
            if i + 1 < len(lines):
                val = re.sub(r"[^A-Za-z\s]", "", lines[i + 1]).strip()
                if 2 < len(val) < 50:
                    given = ""
                    for j in range(i + 2, min(i + 6, len(lines))):
                        if re.match(r"GIVEN\s*NAME", lines[j], re.I) and j + 1 < len(lines):
                            given = re.sub(r"[^A-Za-z\s]", "", lines[j + 1]).strip()
                            break
                    return (f"{val} {given}".strip()).title()

    # ── C: inline label anywhere in text ────────────────────────────────────
    m = re.search(r"(?:SURNAME)[:\s]+([A-Z][A-Z\s]{2,40})", joined, re.IGNORECASE)
    if m:
        val = m.group(1).strip()
        val = re.split(r"\s+(?:GIVEN|SEX|DATE|PLACE|ID|NATIONAL|DOB|\d)", val, flags=re.I)[0].strip()
        if 2 < len(val) < 60:
            return val.title()

    # ── D: ALL-CAPS name-like lines (2–4 capitalised words, no keywords) ────
    SKIP = {
        "REPUBLIC", "KENYA", "NATIONAL", "IDENTITY", "CARD", "DATE",
        "BIRTH", "SEX", "MALE", "FEMALE", "NATIONALITY", "PLACE",
        "EXPIRY", "ISSUE", "DISTRICT", "NUMBER", "SERIAL", "ID",
        "JAMHURI", "KITAMBULISHO", "TAIFA", "GIVEN", "SURNAME",
        "KEN", "DOB", "MAISHA", "NAMBA", "EMBAKASI", "NJIRU",
    }
    candidates = []
    for line in lines:
        clean = re.sub(r"[^A-Z\s]", "", line.upper()).strip()
        words = clean.split()
        if (
            2 <= len(words) <= 4
            and all(2 <= len(w) <= 20 for w in words)
            and not any(w in SKIP for w in words)
        ):
            candidates.append(clean)

    if candidates:
        candidates.sort(key=lambda x: (len(x.split()) not in (2, 3), len(x)))
        return candidates[0].title()

    return ""


def _extract_district(text: str) -> str:
    for pat in [
        r"(?:PLACE\s*OF\s*ISSUE|DISTRICT|PLACE\s*OF\s*BIRTH|COUNTY)[:\s]+([A-Z][A-Z\s]{1,30})",
        r"(?:MAHALI\s*PA)[:\s]+([A-Z][A-Z\s]{1,30})",
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            val = re.split(r"\s+(?:ID|DATE|SEX|NATIONAL|SERIAL|\d)", val, flags=re.I)[0].strip()
            if val:
                return val.title()

    PLACES = [
        "EMBAKASI", "NJIRU", "KASARANI", "WESTLANDS", "LANGATA", "MAKADARA",
        "STAREHE", "KIBRA", "RUARAKA", "ROYSAMBU", "NAIROBI", "MOMBASA",
        "KISUMU", "NAKURU", "ELDORET", "THIKA", "NYERI", "MERU", "MACHAKOS",
        "GARISSA", "KAKAMEGA", "KISII", "KERICHO", "BUNGOMA", "MALINDI",
        "KITALE", "NYAHURURU", "EMBU",
    ]
    text_up = text.upper()
    for p in PLACES:
        if re.search(r"\b" + p + r"\b", text_up):
            return p.title()
    return ""


def extract_kenyan_id_fields(text: str) -> dict:
    """Parse all fields from raw OCR text of a Kenyan National ID."""
    if not text:
        return {}
    text_c = _clean(text)
    fields: dict = {}

    name = _extract_name(text_c)
    if name:
        fields["name"] = name

    id_num = _extract_id_number(text_c)
    if id_num:
        fields["id_number"] = id_num

    dob, expiry = _extract_dates(text_c)
    if dob:
        fields["date_of_birth"] = dob
    if expiry:
        fields["expiry_date"] = expiry

    sex = _extract_sex(text_c)
    if sex:
        fields["sex"] = sex

    nat = _extract_nationality(text_c)
    if nat:
        fields["nationality"] = nat

    district = _extract_district(text_c)
    if district:
        fields["district"] = district

    logger.info(f"Extracted fields: {fields}")
    return fields


# ── DocumentScanningService ───────────────────────────────────────────────────

class DocumentScanningService:
    """Service for document scanning and forgery detection."""

    def __init__(self):
        try:
            pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
        except Exception:
            logger.warning("Tesseract not found")

    def decode_base64_image(self, base64_string: str) -> Optional[np.ndarray]:
        try:
            if "," in base64_string:
                base64_string = base64_string.split(",")[1]
            return decode_image_safe(base64.b64decode(base64_string), force_bgr=True)
        except Exception as e:
            logger.error(f"Decode error: {e}")
            return None

    def analyze_document_quality(self, image: np.ndarray) -> dict:
        try:
            bgr  = ensure_bgr_image(image)
            gray = ensure_gray_image(bgr)
            lv   = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            noise = float(np.std(cv2.subtract(gray, cv2.GaussianBlur(gray, (5,5), 0))))
            edges = cv2.Canny(gray, 50, 150)
            ed    = float(np.sum(edges > 0) / (gray.shape[0] * gray.shape[1]))
            hsv   = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

            qs = 0.0
            if lv > 100: qs += 0.4
            elif lv > 50: qs += 0.3
            elif lv > 20: qs += 0.2
            if noise < 10:  qs += 0.2
            elif noise < 20: qs += 0.1
            if ed > 0.1:  qs += 0.4
            elif ed > 0.05: qs += 0.3
            elif ed > 0.02: qs += 0.2

            return {
                "sharpness":      lv,
                "noise_level":    noise,
                "brightness":     float(np.mean(gray)),
                "contrast":       float(np.std(gray)),
                "edge_density":   ed,
                "color_variance": float(np.var(hsv)),
                "quality_score":  min(qs, 1.0),
                "is_acceptable":  bool(lv > 50 and ed > 0.05),
            }
        except Exception as e:
            logger.error(f"Quality error: {e}")
            return {}

    def detect_forgery_indicators(self, image: np.ndarray, text: str, doc_type: str) -> dict:
        try:
            bgr   = ensure_bgr_image(image)
            gray  = ensure_gray_image(bgr)
            q     = self.analyze_document_quality(bgr)
            ind   = []
            risk  = 0.0

            if q.get("sharpness", 0) < 20:    ind.append("Low sharpness");     risk += 0.2
            if q.get("noise_level", 0) > 30:  ind.append("High noise");        risk += 0.15
            if q.get("edge_density", 0) < 0.02: ind.append("Low text density"); risk += 0.25
            if not text.strip():               ind.append("No text extracted"); risk += 0.3
            elif len(text) < 50:               ind.append("Insufficient text"); risk += 0.1
            if "SAMPLE" in text.upper() or "SPECIMEN" in text.upper():
                ind.append("Sample document"); risk += 0.4

            if doc_type == "national_id":
                f = extract_kenyan_id_fields(text)
                if not f.get("id_number"): ind.append("Missing ID number");  risk += 0.2
                if not f.get("name"):       ind.append("Missing name field"); risk += 0.15

            blurred = cv2.GaussianBlur(gray, (21, 21), 0)
            uniform = int(np.sum(np.abs(cv2.subtract(gray, blurred)) < 5))
            if uniform > gray.shape[0] * gray.shape[1] * 0.3:
                ind.append("Uniform areas detected"); risk += 0.2

            level = "high" if risk >= 0.7 else "medium" if risk >= 0.4 else "low"
            return {
                "indicators":       ind,
                "risk_score":       float(min(risk, 1.0)),
                "risk_level":       level,
                "quality_analysis": q,
                "text_length":      len(text),
                "document_type":    doc_type,
            }
        except Exception as e:
            logger.error(f"Forgery error: {e}")
            return {"indicators": ["Analysis failed"], "risk_score": 0.5, "risk_level": "medium"}

    def detect_document_type(self, text: str) -> str:
        tl = text.lower()
        if any(k in tl for k in ("national identity", "id card", "kitambulisho")):
            return "national_id"
        if "passport" in tl:
            return "passport"
        if "birth certificate" in tl:
            return "birth_certificate"
        if re.search(r"\b\d{8,9}\b", text) and re.search(r"\b\d{2}[.\-/]\d{2}[.\-/]\d{4}\b", text):
            return "national_id"
        return "unknown"

    def process_document(self, base64_image: str, expected_type: Optional[str] = None) -> dict:
        try:
            image = self.decode_base64_image(base64_image)
            if image is None:
                return {"success": False, "error": "Invalid image format"}

            text     = _ocr_variants(image)
            doc_type = expected_type or self.detect_document_type(text)
            fields   = extract_kenyan_id_fields(text) if doc_type in ("national_id", "unknown") else self._passport_fields(text)

            quality  = self.analyze_document_quality(image)
            forgery  = self.detect_forgery_indicators(image, text, doc_type)

            score  = quality.get("quality_score", 0) * 0.4 + (1 - forgery.get("risk_score", 0)) * 0.6
            status = "PASS" if score > 0.7 else "REQUIRES_REVIEW" if score > 0.4 else "FAIL"

            return {
                "success":              True,
                "document_type":        doc_type,
                "extracted_fields":     fields,
                "quality_analysis":     quality,
                "forgery_analysis":     forgery,
                "overall_score":        score,
                "verification_status":  status,
                "extracted_text":       text[:600] + "…" if len(text) > 600 else text,
                "processing_timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Processing error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _passport_fields(self, text: str) -> dict:
        fields: dict = {}
        m = re.search(r"\b([A-Z]\d{7,8})\b", text)
        if m: fields["passport_number"] = m.group()
        if re.search(r"\bKEN\b|\bKENYAN\b", text, re.I): fields["nationality"] = "Kenyan"
        nm = re.search(r"(?:SURNAME|NAME)[:\s]+([A-Z][A-Z\s]{2,40})", text, re.I)
        if nm: fields["name"] = nm.group(1).strip().title()
        mrz = re.search(r"P<KEN([A-Z<]+)", text)
        if mrz and "name" not in fields:
            fields["name"] = mrz.group(1).replace("<", " ").strip().title()
        dob, _ = _extract_dates(text)
        if dob: fields["date_of_birth"] = dob
        return fields


# Global instance
document_service = DocumentScanningService()