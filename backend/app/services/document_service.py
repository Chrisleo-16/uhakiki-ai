from app.logic.ocr_fix import _prepare_for_ocr, _score_ocr_text
from app.logic.handheld_ocr import extract_text_handheld
"""
document_service.py  v4
Kenyan National ID — targeted extraction.

TWO strategies run in parallel, best result wins:
  A) MRZ crop  — crops bottom 30% of back image (white bg, monospace font)
                  → most reliable, used for back-of-card images
  B) Color mask — masks out the teal/green guilloche background on front
                  → used for front-of-card images
"""

import cv2, numpy as np, base64, logging, re
from typing import Optional
from datetime import datetime
from PIL import Image
import pytesseract
from app.logic.ocr_fix import _ocr_variants_improved
from app.logic.image_utils import ensure_bgr_image, ensure_gray_image, decode_image_safe

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
#  LOW-LEVEL HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _scale_up(img: np.ndarray, min_w: int = 1400) -> np.ndarray:
    h, w = img.shape[:2]
    if w < min_w:
        img = cv2.resize(img, None, fx=min_w/w, fy=min_w/w,
                         interpolation=cv2.INTER_CUBIC)
    return img


def _rotate(img: np.ndarray, angle: int) -> np.ndarray:
    if angle == 0:   return img
    if angle == 90:  return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    if angle == 180: return cv2.rotate(img, cv2.ROTATE_180)
    if angle == 270: return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return img


def _correct_rotation(bgr: np.ndarray) -> np.ndarray:
    gray = ensure_gray_image(bgr)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    best_angle, best_var = 0, -1.0
    for angle in (0, 90, 180, 270):
        var = float(np.var(np.sum(_rotate(binary, angle), axis=1).astype(float)))
        if var > best_var:
            best_var, best_angle = var, angle
    return _rotate(bgr, best_angle) if best_angle else bgr


def _real_word_score(text: str) -> float:
    """
    Score OCR text quality — higher = more likely real readable text.
    Uses ratio of real words + bonus for known Kenyan ID keywords.
    This replaces the old pure-alpha count which missed mixed words.
    """
    if not text or len(text) < 10:
        return 0.0
    words = text.split()
    if not words:
        return 0.0
    # Count words that are mostly letters (>60% alpha, length >= 2)
    real_words = sum(
        1 for w in words
        if len(w) >= 2 and sum(c.isalpha() for c in w) / len(w) > 0.6
    )
    # Bonus for known Kenyan ID keywords
    KEYWORDS = [
        "KENYA", "REPUBLIC", "NATIONAL", "IDENTITY", "SURNAME",
        "GIVEN", "MALE", "FEMALE", "SEX", "DATE", "BIRTH",
        "JAMHURI", "KITAMBULISHO", "KEN", "EXPIRY", "PLACE",
        "NUMBER", "NATIONALITY", "ISSUE", "EMBAKASI", "NJIRU",
    ]
    keyword_hits = sum(1 for kw in KEYWORDS if kw in text.upper())
    return (real_words / len(words)) * 100 + keyword_hits * 5


# ─────────────────────────────────────────────────────────────────────────────
#  OCR STRATEGIES
# ─────────────────────────────────────────────────────────────────────────────

def _ocr_mrz_region(bgr: np.ndarray) -> str:
    """
    Strategy A: crop the bottom 35% of the image where the MRZ lives.
    The MRZ is on a plain white background — very easy for Tesseract.
    """
    h, w  = bgr.shape[:2]
    crop  = bgr[int(h * 0.65):, :]          # bottom 35%
    gray  = _scale_up(ensure_gray_image(crop))
    # Simple binary threshold — white bg, black OCR font
    _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
    try:
        return pytesseract.image_to_string(
            Image.fromarray(thresh),
            config="--oem 3 --psm 6 -l eng"
        ).strip()
    except Exception:
        return ""


def _ocr_color_mask(bgr: np.ndarray) -> str:
    """
    Strategy B: mask out the teal/green guilloche background on the front.
    The printed text is very dark (near black) — threshold aggressively.
    """
    h, w  = bgr.shape[:2]
    scaled = cv2.resize(bgr, None, fx=1400/w, fy=1400/w,
                        interpolation=cv2.INTER_CUBIC)

    # Convert to LAB — L channel separates dark text from coloured background
    lab   = cv2.cvtColor(scaled, cv2.COLOR_BGR2LAB)
    l_ch  = lab[:, :, 0]

    # Dark pixels = text (L < 100 in LAB)
    _, dark_mask = cv2.threshold(l_ch, 100, 255, cv2.THRESH_BINARY_INV)

    # Clean up speckles
    kernel   = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    dark_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_OPEN, kernel)

    # Invert so text = black on white (Tesseract prefers this)
    result = cv2.bitwise_not(dark_mask)

    try:
        return pytesseract.image_to_string(
            Image.fromarray(result),
            config="--oem 3 --psm 6 -l eng"
        ).strip()
    except Exception:
        return ""


def _ocr_red_channel(bgr: np.ndarray) -> str:
    """
    Strategy C: red channel — good contrast for dark text on green bg.
    """
    h, w  = bgr.shape[:2]
    _, _, r = cv2.split(bgr)
    r_up  = _scale_up(r)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    r_enh = clahe.apply(r_up)
    _, r_otsu = cv2.threshold(r_enh, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    best, best_score = "", 0
    for psm in (6, 3, 4, 11):
        try:
            t = pytesseract.image_to_string(
                Image.fromarray(r_otsu),
                config=f"--oem 3 --psm {psm} -l eng"
            ).strip()
            s = _real_word_score(t)
            if s > best_score:
                best_score, best = s, t
        except Exception:
            pass
    return best



def _is_handheld_photo(bgr):
    try:
        h, w = bgr.shape[:2]
        hsv      = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        sat_var  = float(np.var(hsv[:, :, 1]))
        gray     = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        edges    = cv2.Canny(gray, 30, 100)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        largest  = max((cv2.contourArea(cnt) for cnt in contours), default=0)
        ratio    = largest / (h * w)
        result   = sat_var > 800 or ratio < 0.75
        logger.info(f"Image type: {'handheld' if result else 'flat'} sat_var={sat_var:.0f} ratio={ratio:.2f}")
        return result
    except Exception:
        return True

def _ocr_variants_improved(image) -> str:
    """
    Smart OCR dispatcher — auto-detects hand-held vs flat scan.
    Hand-held: perspective correction + shadow removal + deblur.
    Flat scan: morphological filtering pipeline.
    """
    from app.logic.image_utils import ensure_bgr_image
    bgr = ensure_bgr_image(image)

    if _is_handheld_photo(bgr):
        logger.info("Routing to handheld OCR pipeline")
        text = extract_text_handheld(bgr)
        if text and len(text) > 50:
            return text
        logger.info("Handheld returned short text, falling back to flat pipeline")

    logger.info("Routing to flat scan OCR pipeline")
    bgr = _correct_rotation(bgr)
    h, w = bgr.shape[:2]
    max_dim = max(h, w)
    if max_dim > 1600:
        bgr = cv2.resize(bgr, None, fx=1400/max_dim, fy=1400/max_dim,
                         interpolation=cv2.INTER_AREA)
    elif max_dim < 800:
        bgr = cv2.resize(bgr, None, fx=1400/max_dim, fy=1400/max_dim,
                         interpolation=cv2.INTER_CUBIC)

    variants = _prepare_for_ocr(bgr)
    configs  = [
        "--oem 3 --psm 6 -l eng",
        "--oem 3 --psm 3 -l eng",
        "--oem 3 --psm 11 -l eng",
        "--oem 3 --psm 6 -l eng+swa",
    ]
    best_text, best_score = "", 0.0
    for name, arr in variants:
        pil = Image.fromarray(arr)
        for cfg in configs:
            try:
                text  = pytesseract.image_to_string(pil, config=cfg).strip()
                score = _score_ocr_text(text)
                if score > best_score:
                    best_score = score
                    best_text  = text
            except Exception:
                pass
    try:
        rgb  = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        text = pytesseract.image_to_string(
            Image.fromarray(rgb), config="--oem 3 --psm 6 -l eng").strip()
        if _score_ocr_text(text) > best_score:
            best_text = text
    except Exception:
        pass

    logger.info(f"Flat OCR score: {best_score:.3f}  len: {len(best_text)}")
    return best_text


def _clean_text(text: str) -> str:
    lines = []
    for line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).strip()
        if line and not re.match(r"^[\W_]+$", line):
            lines.append(line)
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
#  MRZ PARSER  (most reliable source of truth)
# ─────────────────────────────────────────────────────────────────────────────

def _parse_mrz(text: str) -> dict:
    """
    Parse MRZ lines from Kenyan ID back.
    Line 1: IDKEN<ID_NUMBER><...>
    Line 2: YYMMDD<M<YYMMDD<KEN<...>
    Line 3: SURNAME<<GIVEN<NAMES<<...
    """
    fields: dict = {}
    # Normalise: remove spaces inside lines, fix common OCR substitutions
    lines = []
    for raw in text.split("\n"):
        # Remove spaces, fix common OCR errors in MRZ
        l = raw.strip()
        l = l.replace(" ", "").replace("O", "0") if re.search(r"[<\d]{5,}", l.replace(" ","")) else l.strip()
        # Restore alpha chars mistakenly converted
        l = raw.strip().replace("«", "<").replace("»", "<")
        lines.append(l)

    for line in lines:
        clean = re.sub(r"[^A-Z0-9<]", "", line.upper())

        # ── Line 1: starts with IDKEN ─────────────────────────────────────
        if clean.startswith("IDKEN") and len(clean) >= 14:
            id_raw = clean[5:14].replace("<", "")
            if re.fullmatch(r"\d{7,9}", id_raw):
                fields["id_number"] = id_raw
            logger.info(f"MRZ Line1: id={fields.get('id_number')}")

        # ── Line 2: YYMMDD + sex + YYMMDD + KEN ──────────────────────────
        m2 = re.search(r"(\d{6})([MF<])(\d{6})KEN", clean)
        if m2:
            dob_raw, sex_raw, exp_raw = m2.group(1), m2.group(2), m2.group(3)
            try:
                yy, mm, dd = int(dob_raw[:2]), int(dob_raw[2:4]), int(dob_raw[4:6])
                year = 1900+yy if yy > 30 else 2000+yy
                fields["date_of_birth"] = f"{dd:02d}.{mm:02d}.{year}"
            except Exception:
                pass
            try:
                yy2, mm2, dd2 = int(exp_raw[:2]), int(exp_raw[2:4]), int(exp_raw[4:6])
                year2 = 1900+yy2 if yy2 > 30 else 2000+yy2
                fields["expiry_date"] = f"{dd2:02d}.{mm2:02d}.{year2}"
            except Exception:
                pass
            if sex_raw == "M":
                fields["sex"] = "Male"
            elif sex_raw == "F":
                fields["sex"] = "Female"
            fields["nationality"] = "Kenyan"
            logger.info(f"MRZ Line2: dob={fields.get('date_of_birth')} exp={fields.get('expiry_date')}")

        # ── Line 3: SURNAME<<GIVEN<NAMES ─────────────────────────────────
        if "<<" in clean and re.search(r"[A-Z]{3,}", clean):
            parts = clean.split("<<")
            if parts and len(parts[0]) >= 2:
                surname = parts[0].replace("<", " ").strip().title()
                given   = parts[1].replace("<", " ").strip().title() if len(parts) > 1 else ""
                given   = re.sub(r"\s+", " ", given).strip()
                if surname:
                    fields["name"] = f"{surname} {given}".strip()
                    logger.info(f"MRZ Line3: name={fields['name']}")

    return fields


# ─────────────────────────────────────────────────────────────────────────────
#  REGEX FIELD EXTRACTORS  (fallback when MRZ not available)
# ─────────────────────────────────────────────────────────────────────────────

def _extract_id_number(text: str) -> str:
    m = re.search(r"(?:ID\s*(?:No|Number|Nambari|NUM)[.:\s]*|"
                  r"ID\s*NUMBER[.:\s]*)\s*(\d{7,9})", text, re.I)
    if m: return m.group(1)
    # Standalone line of only digits
    for line in text.split("\n"):
        s = re.sub(r"[\s.\-]", "", line)
        if re.fullmatch(r"\d{7,9}", s) and not (1900 <= int(s) <= 2100):
            return s
    # Anywhere
    for pat in (r"\b(\d{9})\b", r"\b(\d{8})\b", r"\b(\d{7})\b"):
        for m in re.finditer(pat, text):
            if not (1900 <= int(m.group(1)) <= 2100):
                return m.group(1)
    return ""


def _extract_dates(text: str):
    dates = []
    for m in re.finditer(r"\b(\d{1,2})[.\s/\-]+(\d{1,2})[.\s/\-]+(\d{4})\b", text):
        d, mo, yr = m.group(1), m.group(2), m.group(3)
        if 1<=int(d)<=31 and 1<=int(mo)<=12 and 1900<=int(yr)<=2100:
            dates.append((int(yr), f"{d.zfill(2)}.{mo.zfill(2)}.{yr}"))
    dates.sort(key=lambda x: x[0])
    return (dates[0][1] if dates else ""), (dates[-1][1] if len(dates)>=2 else "")


def _extract_sex(text: str) -> str:
    m = re.search(r"\bSEX[:\s]+([MF]\w*)", text, re.I)
    if m:
        v = m.group(1).upper()
        if v.startswith("F"): return "Female"
        if v.startswith("M"): return "Male"
    if re.search(r"\bFEMALE\b", text, re.I): return "Female"
    if re.search(r"\bMALE\b",   text, re.I): return "Male"
    return ""


def _extract_nationality(text: str) -> str:
    m = re.search(r"\bNATIONALITY[:\s]+([A-Z]{2,10})", text, re.I)
    if m:
        v = m.group(1).upper()
        return "Kenyan" if v in ("KEN","KENYAN","KENYA") else v.title()
    if re.search(r"\bKEN\b|\bKENYAN\b", text, re.I): return "Kenyan"
    return ""



def _extract_name_from_structured_ocr(text: str) -> str:
    """
    Handles real Kenyan ID OCR layout:
      SURNAME
      LEO               <- surname value
      <noise>           <- ignore
      GIVEN NAME
      CHRISBEN EVANS    <- given name value
    Returns: "Leo Chrisben Evans"
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    SKIP = {"REPUBLIC","KENYA","NATIONAL","IDENTITY","CARD","DATE","BIRTH",
            "SEX","MALE","FEMALE","NATIONALITY","PLACE","EXPIRY","ISSUE",
            "NUMBER","SERIAL","ID","JAMHURI","KITAMBULISHO","TAIFA","KEN"}

    surname_val = ""
    given_val   = ""

    for i, line in enumerate(lines):
        up = line.upper().strip()

        # Found SURNAME keyword — next clean line is surname value
        if up == "SURNAME" or up.startswith("SURNAME "):
            for j in range(i+1, min(i+4, len(lines))):
                cand  = re.sub(r"[^A-Za-z]", " ", lines[j]).strip()
                words = [w for w in cand.upper().split() if len(w) >= 2 and w not in SKIP]
                if words:
                    # Take only first 1-2 real words (surname is usually short)
                    surname_val = " ".join(words[:2])
                    break

        # Found GIVEN NAME keyword — next clean line is given name value
        if re.search(r"GIVEN\s*NAME", line, re.I):
            for k in range(i+1, min(i+4, len(lines))):
                cand  = re.sub(r"[^A-Za-z]", " ", lines[k]).strip()
                words = [w for w in cand.upper().split() if len(w) >= 2 and w not in SKIP]
                if len(words) >= 2:
                    given_val = " ".join(words)
                    break

    if given_val and surname_val:
        # Avoid duplication — if surname already in given name skip it
        if surname_val.upper().split()[0] not in given_val.upper():
            return f"{surname_val} {given_val}".title()
        return given_val.title()
    elif given_val:
        return given_val.title()
    elif surname_val and len(surname_val.split()) >= 2:
        return surname_val.title()
    return ""

def _extract_name(text: str) -> str:
    lines  = [l.strip() for l in text.split("\n") if l.strip()]
    joined = " ".join(lines)

    # ── Priority 0: line-by-line structured extraction ────────────────────
    # Handles real Kenyan ID OCR layout:
    #   SURNAME          GIVEN NAME
    #   LEO              CHRISBEN EVANS
    #   CEOS ty (noise)
    SKIP_W = {"REPUBLIC","KENYA","NATIONAL","IDENTITY","CARD","DATE","BIRTH",
              "SEX","MALE","FEMALE","NATIONALITY","PLACE","EXPIRY","ISSUE",
              "NUMBER","SERIAL","ID","JAMHURI","KITAMBULISHO","TAIFA","KEN",
              "GIVEN","SURNAME","DOB","NAMBA"}
    _surname, _given = "", ""
    for _i, _line in enumerate(lines):
        # Find GIVEN NAME label — most reliable anchor
        if re.search(r"GIVEN\s*NAME", _line, re.I):
            for _k in range(_i + 1, min(_i + 4, len(lines))):
                _gv = re.sub(r"[^A-Za-z]", " ", lines[_k]).strip()
                _gw = [w for w in _gv.upper().split()
                       if len(w) >= 2 and w not in SKIP_W]
                if len(_gw) >= 2:
                    _given = " ".join(_gw)
                    break
        # Find SURNAME label
        if _line.upper().strip() == "SURNAME":
            for _j in range(_i + 1, min(_i + 3, len(lines))):
                _sv = re.sub(r"[^A-Za-z]", " ", lines[_j]).strip()
                _sw = [w for w in _sv.upper().split()
                       if len(w) >= 2 and w not in SKIP_W]
                if _sw:
                    _surname = " ".join(_sw[:1])  # just first word of surname
                    break

    if _given:
        # Only use structured result if GIVEN NAME was on its own line
        # (not inline text like "SURNAME LEO GIVEN NAME CHRISBEN EVANS SEX")
        # Check: GIVEN NAME label must appear as a standalone line
        given_on_own_line = any(
            re.match(r"^\s*GIVEN\s*NAME\s*$", l, re.I) for l in lines
        )
        if given_on_own_line:
            if _surname and _surname.upper() not in _given.upper():
                _full = f"{_surname} {_given}".title()
            else:
                _full = _given.title()
            _words = _full.split()
            if len(_words) >= 2 and all(len(w) >= 2 for w in _words):
                return _full

    # Strategy A: SURNAME <val> GIVEN NAME <val>
    m = re.search(
        r"SURNAME[:\s]+([A-Z][A-Z\s]{1,30}?)\s+GIVEN\s*NAME[:\s]+"
        r"([A-Z][A-Z\s]{1,40}?)"
        r"(?=\s+(?:SEX|DATE|PLACE|ID|NATIONAL|DOB|KEN|\d)|$)",
        joined, re.I)
    if m: return f"{m.group(1).strip()} {m.group(2).strip()}".title()

    # Strategy A2: SURNAME <val> (no GIVEN NAME label)
    m = re.search(
        r"SURNAME[:\s]+([A-Z][A-Z\s]{1,60}?)"
        r"(?=\s+(?:GIVEN|SEX|DATE|PLACE|ID|NATIONAL|DOB|KEN|MALE|FEMALE|\d)|$)",
        joined, re.I)
    if m:
        val   = m.group(1).strip()
        words = [w for w in val.split() if len(w) >= 3]
        if 4 < len(val) < 60 and len(words) >= 2:
            return val.title().title()

    # Strategy B2: combine SURNAME value + GIVEN NAME value
    # Handles real Kenyan ID OCR: SURNAME on own line, value below, then GIVEN NAME
    SKIP_WORDS = {"REPUBLIC","KENYA","NATIONAL","IDENTITY","CARD","DATE",
                  "BIRTH","SEX","MALE","FEMALE","NATIONALITY","PLACE",
                  "EXPIRY","ISSUE","NUMBER","SERIAL","ID","JAMHURI",
                  "KITAMBULISHO","GIVEN","SURNAME","KEN","DOB"}
    for i, line in enumerate(lines):
        if "SURNAME" in line.upper():
            surname_val = ""
            given_val   = ""

            # Get surname value — first clean word(s) after SURNAME line
            for j in range(i+1, min(i+4, len(lines))):
                cand  = re.sub(r"[^A-Za-z]", " ", lines[j]).strip()
                words = [w for w in cand.upper().split()
                         if len(w) >= 2 and w not in SKIP_WORDS]
                if words:
                    surname_val = " ".join(words[:2])  # max 2 words for surname
                    break

            # Get given name — look for GIVEN NAME label then take next clean line
            for k in range(i+1, min(i+10, len(lines))):
                if re.search(r"GIVEN\s*NAME", lines[k], re.I):
                    for m in range(k+1, min(k+4, len(lines))):
                        gv    = re.sub(r"[^A-Za-z]", " ", lines[m]).strip()
                        words = [w for w in gv.upper().split()
                                 if len(w) >= 2 and w not in SKIP_WORDS]
                        if len(words) >= 2:
                            given_val = " ".join(words)
                            break
                    break

            # Build full name
            if given_val and surname_val:
                # Skip surname if already contained in given name
                if surname_val.upper().split()[0] not in given_val.upper():
                    full = f"{surname_val} {given_val}"
                else:
                    full = given_val
                return full.title()
            elif given_val:
                return given_val.title()
            elif surname_val and len(surname_val.split()) >= 2:
                return surname_val.title()
            
    # Strategy B: keyword on own line, value on next
    for i, line in enumerate(lines):
        if line.upper().strip() in ("SURNAME", "JINA LA UKOO"):
            sv = ""
            for j in range(i+1, min(i+4, len(lines))):
                c = re.sub(r"[^A-Za-z\s]", "", lines[j]).strip()
                if c and not re.match(
                    r"^(GIVEN\s*NAME|SEX|DATE|PLACE|NATIONAL|ID|SERIAL|EXPIRY)$",
                    c, re.I) and 2 < len(c) < 50:
                    sv = c; break
            gv = ""
            for k in range(i+1, min(i+8, len(lines))):
                if re.match(r"GIVEN\s*NAME", lines[k], re.I) and k+1 < len(lines):
                    gv = re.sub(r"[^A-Za-z\s]", "", lines[k+1]).strip()
                    break
            if sv: return f"{sv} {gv}".strip().title()

    # Strategy C: inline label
    m = re.search(r"SURNAME[:\s]+([A-Z][A-Z\s]{2,40})", joined, re.I)
    if m:
        val = re.split(
            r"\s+(?:GIVEN|SEX|DATE|PLACE|ID|NATIONAL|DOB|MALE|FEMALE|\d)",
            m.group(1).strip(), flags=re.I)[0].strip()
        if 2 < len(val) < 60: return val.title()

    return ""


def _extract_district(text: str) -> str:
    for pat in (
        r"(?:PLACE\s*OF\s*ISSUE|DISTRICT|PLACE\s*OF\s*BIRTH|COUNTY|"
        r"SUB-COUNTY|DIVISION|LOCATION)[:\s]+([A-Z][A-Z\s]{1,30})",
        r"(?:MAHALI\s*PA)[:\s]+([A-Z][A-Z\s]{1,30})",
    ):
        m = re.search(pat, text, re.I)
        if m:
            val = re.split(
                r"\s+(?:ID|DATE|SEX|NATIONAL|SERIAL|\d)",
                m.group(1).strip(), flags=re.I)[0].strip()
            if val: return val.title()
    PLACES = [
        "EMBAKASI","NJIRU","KASARANI","WESTLANDS","LANGATA","MAKADARA",
        "STAREHE","KIBRA","RUARAKA","ROYSAMBU","NAIROBI","MOMBASA",
        "KISUMU","NAKURU","ELDORET","THIKA","NYERI","MERU","MACHAKOS",
        "GARISSA","KAKAMEGA","KISII","KERICHO","BUNGOMA","MALINDI",
        "KITALE","NYAHURURU","EMBU","KISII","NYAMACHE","NYACHEKI",
        "BASSI","BORABU","ISENA",
    ]
    for p in PLACES:
        if re.search(r"\b" + p + r"\b", text.upper()):
            return p.title()
    return ""


def extract_kenyan_id_fields(text: str) -> dict:
    """
    Extract all fields. MRZ is tried first (most reliable),
    then regex fallbacks fill any gaps.
    """
    if not text:
        return {}
    t = _clean_text(text)

    # Start with MRZ — fills name, id_number, dob, expiry, sex, nationality
    f = _parse_mrz(t)

    # Fill gaps with regex extractors
    if not f.get("name"):
        name = _extract_name(t)
        if name:
            # Reject names that are too short or look like OCR noise
            # Real names have at least 2 words, each 3+ chars
            words = [w for w in name.split() if len(w) >= 3]
            if len(words) >= 2:
                f["name"] = " ".join(words)

    if not f.get("id_number"):
        idn = _extract_id_number(t)
        if idn: f["id_number"] = idn

    if not f.get("date_of_birth") or not f.get("expiry_date"):
        dob, exp = _extract_dates(t)
        if dob and not f.get("date_of_birth"):   f["date_of_birth"] = dob
        if exp and not f.get("expiry_date"):      f["expiry_date"]   = exp

    if not f.get("sex"):
        sex = _extract_sex(t)
        if sex: f["sex"] = sex

    if not f.get("nationality"):
        nat = _extract_nationality(t)
        if nat: f["nationality"] = nat

    dist = _extract_district(t)
    if dist: f["district"] = dist

    logger.info(f"Final fields: { {k:v for k,v in f.items() if v} }")
    return {k: v for k, v in f.items() if v}


# ─────────────────────────────────────────────────────────────────────────────
#  DOCUMENT SCANNING SERVICE
# ─────────────────────────────────────────────────────────────────────────────

class DocumentScanningService:

    def __init__(self):
        try:
            pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
        except Exception:
            logger.warning("Tesseract not found")

    def decode_base64_image(self, b64: str) -> Optional[np.ndarray]:
        try:
            if "," in b64: b64 = b64.split(",")[1]
            return decode_image_safe(base64.b64decode(b64), force_bgr=True)
        except Exception as e:
            logger.error(f"Decode error: {e}")
            return None

    def analyze_document_quality(self, image: np.ndarray) -> dict:
        try:
            bgr   = ensure_bgr_image(image)
            gray  = ensure_gray_image(bgr)
            lv    = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            noise = float(np.std(cv2.subtract(gray, cv2.GaussianBlur(gray,(5,5),0))))
            edges = cv2.Canny(gray, 50, 150)
            ed    = float(np.sum(edges>0) / (gray.shape[0]*gray.shape[1]))
            hsv   = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
            qs    = 0.0
            if lv>100:     qs+=0.4
            elif lv>50:    qs+=0.3
            elif lv>20:    qs+=0.2
            if noise<10:   qs+=0.2
            elif noise<20: qs+=0.1
            if ed>0.1:     qs+=0.4
            elif ed>0.05:  qs+=0.3
            elif ed>0.02:  qs+=0.2
            return {
                "sharpness": lv, "noise_level": noise,
                "brightness": float(np.mean(gray)),
                "contrast": float(np.std(gray)),
                "edge_density": ed,
                "color_variance": float(np.var(hsv)),
                "quality_score": min(qs, 1.0),
                "is_acceptable": bool(lv > 50 and ed > 0.05),
            }
        except Exception as e:
            logger.error(f"Quality error: {e}")
            return {}

    def detect_forgery_indicators(self, image: np.ndarray, text: str, doc_type: str) -> dict:
        try:
            bgr  = ensure_bgr_image(image)
            gray = ensure_gray_image(bgr)
            q    = self.analyze_document_quality(bgr)
            ind, risk = [], 0.0
            if q.get("sharpness",0) < 20:      ind.append("Low sharpness");     risk += 0.20
            if q.get("noise_level",0) > 30:    ind.append("High noise");        risk += 0.15
            if q.get("edge_density",0) < 0.02: ind.append("Low text density");  risk += 0.25
            if not text.strip():               ind.append("No text extracted");  risk += 0.30
            elif len(text) < 50:               ind.append("Insufficient text");  risk += 0.10
            if "SAMPLE" in text.upper() or "SPECIMEN" in text.upper():
                ind.append("Sample document"); risk += 0.40
            if doc_type == "national_id":
                f = extract_kenyan_id_fields(text)
                if not f.get("id_number"): ind.append("Missing ID number");  risk += 0.20
                if not f.get("name"):      ind.append("Missing name field"); risk += 0.15
            blurred = cv2.GaussianBlur(gray, (21,21), 0)
            if int(np.sum(np.abs(cv2.subtract(gray, blurred)) < 5)) > \
               gray.shape[0] * gray.shape[1] * 0.3:
                ind.append("Uniform areas detected"); risk += 0.20
            level = "high" if risk >= 0.7 else "medium" if risk >= 0.4 else "low"
            return {
                "indicators": ind, "risk_score": float(min(risk,1.0)),
                "risk_level": level, "quality_analysis": q,
                "text_length": len(text), "document_type": doc_type,
            }
        except Exception as e:
            logger.error(f"Forgery error: {e}")
            return {"indicators": ["Analysis failed"], "risk_score": 0.5, "risk_level": "medium"}

    def detect_document_type(self, text: str) -> str:
        tl = text.lower()
        if any(k in tl for k in ("national identity","id card","kitambulisho")): return "national_id"
        if "idken" in tl.replace(" ",""): return "national_id"   # MRZ line 1
        if "passport" in tl: return "passport"
        if "birth certificate" in tl: return "birth_certificate"
        if re.search(r"\b\d{8,9}\b", text) and \
           re.search(r"\b\d{2}[.\-/]\d{2}[.\-/]\d{4}\b", text):
            return "national_id"
        return "unknown"

    def _passport_fields(self, text: str) -> dict:
        f: dict = {}
        m = re.search(r"\b([A-Z]\d{7,8})\b", text)
        if m: f["passport_number"] = m.group()
        if re.search(r"\bKEN\b|\bKENYAN\b", text, re.I): f["nationality"] = "Kenyan"
        nm = re.search(r"(?:SURNAME|NAME)[:\s]+([A-Z][A-Z\s]{2,40})", text, re.I)
        if nm: f["name"] = nm.group(1).strip().title()
        mrz = re.search(r"P<KEN([A-Z<]+)", text)
        if mrz and "name" not in f:
            f["name"] = mrz.group(1).replace("<"," ").strip().title()
        dob, _ = _extract_dates(text)
        if dob: f["date_of_birth"] = dob
        return f

    def process_document(self, base64_image: str,
                         expected_type: Optional[str] = None) -> dict:
        try:
            image = self.decode_base64_image(base64_image)
            if image is None:
                return {"success": False, "error": "Invalid image format"}

            text     = _ocr_variants_improved(image)
            doc_type = expected_type or self.detect_document_type(text)
            fields   = (
                extract_kenyan_id_fields(text)
                if doc_type in ("national_id", "unknown")
                else self._passport_fields(text)
            )
            quality = self.analyze_document_quality(image)
            forgery = self.detect_forgery_indicators(image, text, doc_type)
            score   = (quality.get("quality_score",0) * 0.4 +
                       (1 - forgery.get("risk_score",0)) * 0.6)
            status  = ("PASS" if score > 0.7 else
                       "REQUIRES_REVIEW" if score > 0.4 else "FAIL")
            return {
                "success": True,
                "document_type": doc_type,
                "extracted_fields": fields,
                "quality_analysis": quality,
                "forgery_analysis": forgery,
                "overall_score": score,
                "verification_status": status,
                "extracted_text": text[:600] + "…" if len(text) > 600 else text,
                "processing_timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Processing error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
#  GLOBAL INSTANCE + PIPELINE HELPERS
# ─────────────────────────────────────────────────────────────────────────────

document_service = DocumentScanningService()


def detect_pixel_anomalies(image: np.ndarray) -> dict:
    try:
        text     = _ocr_variants_improved(image)
        doc_type = document_service.detect_document_type(text)
        forgery  = document_service.detect_forgery_indicators(image, text, doc_type)
        quality  = document_service.analyze_document_quality(image)
        return {
            "mse_score":           forgery.get("risk_score", 0.5),
            "is_forged":           forgery.get("risk_level") == "high",
            "anomaly_score":       forgery.get("risk_score", 0.5),
            "forgery_indicators":  forgery.get("indicators", []),
            "risk_level":          forgery.get("risk_level", "unknown"),
            "quality_analysis":    quality,
            "document_type":       doc_type,
            "extracted_text_length": len(text),
        }
    except Exception as e:
        logger.error(f"detect_pixel_anomalies: {e}")
        return {"mse_score": 0.0, "is_forged": False, "anomaly_score": 0.0, "error": str(e)}


def calculate_forgery_score(image: np.ndarray) -> float:
    return detect_pixel_anomalies(image).get("anomaly_score", 0.5)


def get_reconstruction(image: np.ndarray) -> np.ndarray:
    try:   return ensure_gray_image(image)
    except: return image


# ─────────────────────────────────────────────────────────────────────────────
#  SELF-TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys, base64 as b64mod

    print("=" * 60)
    print("document_service.py  v4 — self-test")
    print("=" * 60)

    # MRZ parser test
    mrz_sample = (
        "IDKEN9751626031<455<4781<<<<<<\n"
        "0709037M3509054KEN706184829041\n"
        "LEO<<CHRISBEN<EVANS<<<<<<<<<<<\n"
    )
    mrz_fields = _parse_mrz(mrz_sample)
    print("\n── MRZ parser ───────────────────────────────────────")
    for k, v in mrz_fields.items():
        print(f"  {k:<20} {v}")

    expected_mrz = {
        "id_number":    "975162603",
        "name":         "Leo Chrisben Evans",
        "sex":          "Male",
        "nationality":  "Kenyan",
        "date_of_birth": "07.09.2003",
        "expiry_date":   "05.09.2035",
    }
    all_pass = True
    print()
    for k, exp in expected_mrz.items():
        got = mrz_fields.get(k, "")
        ok  = got.lower() == exp.lower() if got else False
        if not ok: all_pass = False
        print(f"  {'✅' if ok else '❌'}  {k}: expected={exp!r}  got={got!r}")

    # Image test if paths exist
    import os
    for path, label in [
        ("data/forensics/original/IMG_20250924_121136_884~2.jpg", "FRONT"),
        ("data/forensics/original/IMG_20250924_121149_117~2.jpg", "BACK"),
    ]:
        if not os.path.exists(path):
            continue
        print(f"\n── {label}: {path.split('/')[-1]} ──────────────────")
        import cv2
        img = cv2.imread(path)
        text = _ocr_variants_improved(img)
        fields = extract_kenyan_id_fields(text)
        for k, v in fields.items():
            print(f"  {k:<20} {v}")
        if not fields:
            print("  (no fields extracted)")

    print()
    print("MRZ parser: " + ("✅ All passed" if all_pass else "❌ Some failed"))