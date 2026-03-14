"""
document_scanning_service.py  v3 (consolidated)
Place at:  app/services/document_scanning_service.py
           OR app/logic/forgery_detector.py  (whichever your imports use)

This single file replaces:
  - app/logic/forgery_detector.py  (old)
  - app/services/document_service.py  (old v1/v2)
  - app/logic/document_scanning_service.py  (old)
"""

import cv2, numpy as np, base64, logging, re
from typing import Dict, Optional
from datetime import datetime
from PIL import Image
import pytesseract
from app.logic.image_utils import ensure_bgr_image, ensure_gray_image, decode_image_safe

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
#  IMAGE / OCR HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _scale_up(gray: np.ndarray, min_w: int = 1400) -> np.ndarray:
    h, w = gray.shape[:2]
    if w < min_w:
        gray = cv2.resize(gray, None, fx=min_w/w, fy=min_w/w,
                          interpolation=cv2.INTER_CUBIC)
    return gray


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


def _ocr_variants(image: np.ndarray) -> str:
    bgr  = _correct_rotation(ensure_bgr_image(image))
    gray = _scale_up(ensure_gray_image(bgr))
    clahe    = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    _, otsu  = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    adapt    = cv2.adaptiveThreshold(enhanced, 255,
                 cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 13, 6)
    sharp    = cv2.filter2D(enhanced, -1, np.array([[0,-1,0],[-1,5,-1],[0,-1,0]]))

    combos = [
        (enhanced, "--oem 3 --psm 6 -l eng"),
        (otsu,     "--oem 3 --psm 6 -l eng"),
        (adapt,    "--oem 3 --psm 6 -l eng"),
        (enhanced, "--oem 3 --psm 3 -l eng"),
        (otsu,     "--oem 3 --psm 11 -l eng"),
        (sharp,    "--oem 3 --psm 6 -l eng"),
        (cv2.bitwise_not(otsu), "--oem 3 --psm 6 -l eng"),
        (enhanced, "--oem 3 --psm 4 -l eng"),
        (enhanced, "--oem 3 --psm 6 -l eng+swa"),
        (otsu,     "--oem 3 --psm 6 -l eng+swa"),
    ]
    best, best_len = "", 0
    for arr, cfg in combos:
        try:
            t = pytesseract.image_to_string(Image.fromarray(arr), config=cfg).strip()
            if len(t) > best_len:
                best_len, best = len(t), t
        except Exception:
            pass
    try:
        t = pytesseract.image_to_string(
            Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)),
            config="--oem 3 --psm 6 -l eng").strip()
        if len(t) > best_len:
            best = t
    except Exception:
        pass
    logger.info(f"OCR best length: {len(best)}")
    return best


def _clean_text(text: str) -> str:
    lines = []
    for line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).strip()
        if line and not re.match(r"^[\W_]+$", line):
            lines.append(line)
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
#  FIELD EXTRACTORS
# ─────────────────────────────────────────────────────────────────────────────

def _extract_id_number(text: str) -> str:
    m = re.search(
        r"(?:ID\s*(?:No|Number|Nambari|NUM)[.:\s]*|Serial\s*No[.:\s]*)\s*(\d{7,9})",
        text, re.I)
    if m: return m.group(1)
    for line in text.split("\n"):
        s = re.sub(r"[\s.\-]", "", line)
        if re.fullmatch(r"\d{7,9}", s) and not (1900 <= int(s) <= 2100):
            return s
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


def _extract_name(text: str) -> str:
    lines  = [l.strip() for l in text.split("\n") if l.strip()]
    joined = " ".join(lines)

    # A: inline "SURNAME <val> GIVEN NAME <val>"
    m = re.search(
        r"SURNAME[:\s]+([A-Z][A-Z\s]{1,30}?)\s+GIVEN\s*NAME[:\s]+([A-Z][A-Z\s]{1,40}?)"
        r"(?=\s+(?:SEX|DATE|PLACE|ID|NATIONAL|DOB|KEN|\d)|$)", joined, re.I)
    if m: return f"{m.group(1).strip()} {m.group(2).strip()}".title()

    # A2: inline without GIVEN NAME label
    m = re.search(
        r"SURNAME[:\s]+([A-Z][A-Z\s]{1,60}?)"
        r"(?=\s+(?:GIVEN|SEX|DATE|PLACE|ID|NATIONAL|DOB|KEN|MALE|FEMALE|\d)|$)",
        joined, re.I)
    if m:
        val = m.group(1).strip()
        if 4 < len(val) < 60: return val.title()

    # B: keyword on its own line
    for i, line in enumerate(lines):
        if line.upper().strip() in ("SURNAME", "JINA LA UKOO"):
            sv, gv = "", ""
            for j in range(i+1, min(i+4, len(lines))):
                c = re.sub(r"[^A-Za-z\s]", "", lines[j]).strip()
                if c and not re.match(
                    r"^(GIVEN\s*NAME|SEX|DATE|PLACE|NATIONAL|ID|SERIAL|EXPIRY)$", c, re.I
                ) and 2 < len(c) < 50:
                    sv = c; break
            for k in range(i+1, min(i+8, len(lines))):
                if re.match(r"GIVEN\s*NAME", lines[k], re.I):
                    if k+1 < len(lines):
                        gv = re.sub(r"[^A-Za-z\s]", "", lines[k+1]).strip()
                    break
            if sv: return f"{sv} {gv}".strip().title()

    # C: inline label anywhere
    m = re.search(r"SURNAME[:\s]+([A-Z][A-Z\s]{2,40})", joined, re.I)
    if m:
        val = re.split(
            r"\s+(?:GIVEN|SEX|DATE|PLACE|ID|NATIONAL|DOB|MALE|FEMALE|\d)",
            m.group(1).strip(), flags=re.I)[0].strip()
        if 2 < len(val) < 60: return val.title()

    # D: ALL-CAPS name lines (last resort)
    SKIP = {
        "REPUBLIC","KENYA","NATIONAL","IDENTITY","CARD","DATE","BIRTH",
        "SEX","MALE","FEMALE","NATIONALITY","PLACE","EXPIRY","ISSUE",
        "DISTRICT","NUMBER","SERIAL","ID","JAMHURI","KITAMBULISHO","TAIFA",
        "GIVEN","SURNAME","KEN","DOB","SO","ONE","OF","BY","IN","ON","AT",
        "TO","OR","AN","THE","AND","FOR","SECURE","DOCUMENT","VERIFIED",
        "SAMPLE","SPECIMEN","COUNTY","NAIROBI","MOMBASA","KISUMU",
    }
    cands = []
    for line in lines:
        clean = re.sub(r"[^A-Z\s]", "", line.upper()).strip()
        words = clean.split()
        if (2 <= len(words) <= 4
                and all(3 <= len(w) <= 20 for w in words)
                and not any(w in SKIP for w in words)):
            cands.append(clean)
    if cands:
        cands.sort(key=lambda x: (len(x.split()) not in (2,3), len(x)))
        return cands[0].title()
    return ""


def _extract_district(text: str) -> str:
    for pat in (
        r"(?:PLACE\s*OF\s*ISSUE|DISTRICT|PLACE\s*OF\s*BIRTH|COUNTY)[:\s]+([A-Z][A-Z\s]{1,30})",
        r"(?:MAHALI\s*PA)[:\s]+([A-Z][A-Z\s]{1,30})",
    ):
        m = re.search(pat, text, re.I)
        if m:
            val = re.split(
                r"\s+(?:ID|DATE|SEX|NATIONAL|SERIAL|\d)", m.group(1).strip(), flags=re.I
            )[0].strip()
            if val: return val.title()
    PLACES = [
        "EMBAKASI","NJIRU","KASARANI","WESTLANDS","LANGATA","MAKADARA",
        "STAREHE","KIBRA","RUARAKA","ROYSAMBU","NAIROBI","MOMBASA",
        "KISUMU","NAKURU","ELDORET","THIKA","NYERI","MERU","MACHAKOS",
        "GARISSA","KAKAMEGA","KISII","KERICHO","BUNGOMA","MALINDI",
        "KITALE","NYAHURURU","EMBU",
    ]
    for p in PLACES:
        if re.search(r"\b" + p + r"\b", text.upper()):
            return p.title()
    return ""


def extract_kenyan_id_fields(text: str) -> dict:
    if not text: return {}
    t = _clean_text(text)
    f: dict = {}
    name = _extract_name(t);         f["name"]          = name          if name     else None
    idn  = _extract_id_number(t);    f["id_number"]     = idn           if idn      else None
    dob, exp = _extract_dates(t);    f["date_of_birth"] = dob           if dob      else None
    f["expiry_date"]  = exp      if exp      else None
    sex  = _extract_sex(t);          f["sex"]           = sex           if sex      else None
    nat  = _extract_nationality(t);  f["nationality"]   = nat           if nat      else None
    dist = _extract_district(t);     f["district"]      = dist          if dist     else None
    logger.info(f"Extracted fields: { {k:v for k,v in f.items() if v} }")
    return {k: v for k, v in f.items() if v is not None}


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
            logger.error(f"Decode error: {e}"); return None

    def analyze_document_quality(self, image: np.ndarray) -> dict:
        try:
            bgr  = ensure_bgr_image(image)
            gray = ensure_gray_image(bgr)
            lv   = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            noise= float(np.std(cv2.subtract(gray, cv2.GaussianBlur(gray,(5,5),0))))
            edges= cv2.Canny(gray, 50, 150)
            ed   = float(np.sum(edges>0)/(gray.shape[0]*gray.shape[1]))
            hsv  = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
            qs   = 0.0
            if lv>100:    qs+=0.4
            elif lv>50:   qs+=0.3
            elif lv>20:   qs+=0.2
            if noise<10:  qs+=0.2
            elif noise<20:qs+=0.1
            if ed>0.1:    qs+=0.4
            elif ed>0.05: qs+=0.3
            elif ed>0.02: qs+=0.2
            return {
                "sharpness": lv, "noise_level": noise,
                "brightness": float(np.mean(gray)), "contrast": float(np.std(gray)),
                "edge_density": ed, "color_variance": float(np.var(hsv)),
                "quality_score": min(qs,1.0), "is_acceptable": bool(lv>50 and ed>0.05),
            }
        except Exception as e:
            logger.error(f"Quality error: {e}"); return {}

    def detect_forgery_indicators(self, image: np.ndarray, text: str, doc_type: str) -> dict:
        try:
            bgr  = ensure_bgr_image(image)
            gray = ensure_gray_image(bgr)
            q    = self.analyze_document_quality(bgr)
            ind, risk = [], 0.0
            if q.get("sharpness",0)<20:     ind.append("Low sharpness");     risk+=0.20
            if q.get("noise_level",0)>30:   ind.append("High noise");        risk+=0.15
            if q.get("edge_density",0)<0.02:ind.append("Low text density");  risk+=0.25
            if not text.strip():            ind.append("No text extracted");  risk+=0.30
            elif len(text)<50:              ind.append("Insufficient text");  risk+=0.10
            if "SAMPLE" in text.upper() or "SPECIMEN" in text.upper():
                ind.append("Sample document"); risk+=0.40
            if doc_type=="national_id":
                f=extract_kenyan_id_fields(text)
                if not f.get("id_number"): ind.append("Missing ID number");  risk+=0.20
                if not f.get("name"):      ind.append("Missing name field"); risk+=0.15
            blurred=cv2.GaussianBlur(gray,(21,21),0)
            if int(np.sum(np.abs(cv2.subtract(gray,blurred))<5))>gray.shape[0]*gray.shape[1]*0.3:
                ind.append("Uniform areas"); risk+=0.20
            level="high" if risk>=0.7 else "medium" if risk>=0.4 else "low"
            return {"indicators":ind,"risk_score":float(min(risk,1.0)),"risk_level":level,
                    "quality_analysis":q,"text_length":len(text),"document_type":doc_type}
        except Exception as e:
            logger.error(f"Forgery error: {e}")
            return {"indicators":["Analysis failed"],"risk_score":0.5,"risk_level":"medium"}

    def detect_document_type(self, text: str) -> str:
        tl=text.lower()
        if any(k in tl for k in ("national identity","id card","kitambulisho")): return "national_id"
        if "passport" in tl: return "passport"
        if "birth certificate" in tl: return "birth_certificate"
        if re.search(r"\b\d{8,9}\b",text) and re.search(r"\b\d{2}[.\-/]\d{2}[.\-/]\d{4}\b",text):
            return "national_id"
        return "unknown"

    def _passport_fields(self, text: str) -> dict:
        f: dict = {}
        m=re.search(r"\b([A-Z]\d{7,8})\b",text)
        if m: f["passport_number"]=m.group()
        if re.search(r"\bKEN\b|\bKENYAN\b",text,re.I): f["nationality"]="Kenyan"
        nm=re.search(r"(?:SURNAME|NAME)[:\s]+([A-Z][A-Z\s]{2,40})",text,re.I)
        if nm: f["name"]=nm.group(1).strip().title()
        mrz=re.search(r"P<KEN([A-Z<]+)",text)
        if mrz and "name" not in f:
            f["name"]=mrz.group(1).replace("<"," ").strip().title()
        dob,_=_extract_dates(text)
        if dob: f["date_of_birth"]=dob
        return f

    def process_document(self, base64_image: str, expected_type: Optional[str]=None) -> dict:
        try:
            image=self.decode_base64_image(base64_image)
            if image is None: return {"success":False,"error":"Invalid image format"}
            text    =_ocr_variants(image)
            doc_type=expected_type or self.detect_document_type(text)
            fields  =(extract_kenyan_id_fields(text)
                      if doc_type in ("national_id","unknown")
                      else self._passport_fields(text))
            quality =self.analyze_document_quality(image)
            forgery =self.detect_forgery_indicators(image,text,doc_type)
            score   =quality.get("quality_score",0)*0.4+(1-forgery.get("risk_score",0))*0.6
            status  ="PASS" if score>0.7 else "REQUIRES_REVIEW" if score>0.4 else "FAIL"
            return {
                "success":True,"document_type":doc_type,"extracted_fields":fields,
                "quality_analysis":quality,"forgery_analysis":forgery,
                "overall_score":score,"verification_status":status,
                "extracted_text":text[:600]+"…" if len(text)>600 else text,
                "processing_timestamp":datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Processing error: {e}",exc_info=True)
            return {"success":False,"error":str(e)}


# ─────────────────────────────────────────────────────────────────────────────
#  GLOBAL INSTANCE + PIPELINE HELPERS
# ─────────────────────────────────────────────────────────────────────────────

document_service = DocumentScanningService()


def detect_pixel_anomalies(image: np.ndarray) -> dict:
    svc=document_service
    try:
        text    =_ocr_variants(image)
        doc_type=svc.detect_document_type(text)
        forgery =svc.detect_forgery_indicators(image,text,doc_type)
        quality =svc.analyze_document_quality(image)
        return {
            "mse_score":forgery.get("risk_score",0.5),
            "is_forged":forgery.get("risk_level")=="high",
            "anomaly_score":forgery.get("risk_score",0.5),
            "forgery_indicators":forgery.get("indicators",[]),
            "risk_level":forgery.get("risk_level","unknown"),
            "quality_analysis":quality,"document_type":doc_type,
            "extracted_text_length":len(text),
        }
    except Exception as e:
        logger.error(f"detect_pixel_anomalies: {e}")
        return {"mse_score":0.0,"is_forged":False,"anomaly_score":0.0,"error":str(e)}


def calculate_forgery_score(image: np.ndarray) -> float:
    return detect_pixel_anomalies(image).get("anomaly_score",0.5)


def get_reconstruction(image: np.ndarray) -> np.ndarray:
    try:   return ensure_gray_image(image)
    except:return image


# ─────────────────────────────────────────────────────────────────────────────
#  SELF-TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cases = [
        ("SURNAME LEO GIVEN NAME CHRISBEN EVANS SEX MALE NATIONALITY KEN DATE OF BIRTH 03.09.2007",
         "Leo Chrisben Evans","Strategy A"),
        ("SURNAME LEO CHRISBEN EVANS SEX MALE","Leo Chrisben Evans","Strategy A2"),
        ("SURNAME\nLEO\nGIVEN NAME\nCHRISBEN EVANS\nSEX MALE","Leo Chrisben Evans","Strategy B"),
        ("So One\nSURNAME LEO CHRISBEN EVANS SEX MALE","Leo Chrisben Evans","Strategy D guard"),
        ("JAMHURI YA KENYA REPUBLIC OF KENYA KITAMBULISHO CHA TAIFA\n"
         "SURNAME LEO\nGIVEN NAME CHRISBEN EVANS\n"
         "SEX MALE NATIONALITY KEN DATE OF BIRTH 03. 09. 2007\n"
         "PLACE OF BIRTH EMBAKASI\nNUMBER 975162603\n"
         "DATE OF EXPIRY 05. 09. 2035\nPLACE OF ISSUE NJIRU",
         "Leo Chrisben Evans","Full realistic OCR dump"),
    ]
    print("="*60+"\ndocument_scanning_service.py — self-test\n"+"="*60)
    all_pass=True
    for raw,expected,label in cases:
        got=_extract_name(raw); ok=got.lower()==expected.lower()
        if not ok: all_pass=False
        print(f"\n{'✅ PASS' if ok else '❌ FAIL'}  [{label}]")
        if not ok: print(f"  Expected: {expected!r}\n  Got:      {got!r}")
    print("\n── Field extraction smoke test ──────────────────────")
    for k,v in extract_kenyan_id_fields(cases[-1][0]).items():
        print(f"  {k:<20} {v}")
    print("\n"+"All tests passed! ✅" if all_pass else "\nSome tests FAILED ❌")