#!/usr/bin/env python3
"""
test_components.py  —  Uhakiki-AI component test suite
Run from project root:

    python test_components.py                    # all tests
    python test_components.py --unit             # unit tests only (no server needed)
    python test_components.py --api              # API tests (server must be running)
    python test_components.py --image path/to/id.jpg   # real image test
    python test_components.py --quick            # fastest smoke test

Results saved to:  ~/uhakiki-ai/test_results/
"""

from typing import Optional
import sys, os, argparse, traceback, json, time, base64
from pathlib import Path
from datetime import datetime

# ── colour helpers ─────────────────────────────────────────────────────────────
G="\033[92m"; R="\033[91m"; Y="\033[93m"; C="\033[96m"; B="\033[1m"; X="\033[0m"
def ok(m):    print(f"{G}  ✅ {m}{X}")
def fail(m):  print(f"{R}  ❌ {m}{X}")
def warn(m):  print(f"{Y}  ⚠️  {m}{X}")
def info(m):  print(f"{C}  ➜  {m}{X}")
def hdr(m):   print(f"\n{B}{C}{'─'*55}\n  {m}\n{'─'*55}{X}")
def skip(m):  print(f"{Y}  ⏭  SKIP: {m}{X}")

PASS = FAIL_COUNT = 0

def check(cond, pass_msg, fail_msg):
    global PASS, FAIL_COUNT
    if cond:
        ok(pass_msg); PASS += 1
    else:
        fail(fail_msg); FAIL_COUNT += 1
    return cond

# ── paths ──────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).resolve().parent
BACKEND     = ROOT / "backend"
RESULTS_DIR = ROOT / "test_results"
RESULTS_DIR.mkdir(exist_ok=True)
REPORT_FILE = RESULTS_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT))

results = {}   # collected per-section


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 1 — DEPENDENCIES
# ══════════════════════════════════════════════════════════════════════════════
def test_dependencies():
    hdr("1. Dependencies")
    deps = {
        "cv2":               "opencv-python",
        "numpy":             "numpy",
        "torch":             "torch",
        "PIL":               "Pillow",
        "pytesseract":       "pytesseract",
        "torchvision":       "torchvision",
        "fastapi":           "fastapi",
        "uvicorn":           "uvicorn",
        "pymilvus":          "pymilvus",
        "sklearn":           "scikit-learn",
        "sentence_transformers": "sentence-transformers",
    }
    missing = []
    for mod, pkg in deps.items():
        try:
            __import__(mod)
            ok(pkg)
        except ImportError:
            fail(f"{pkg}  →  pip install {pkg}")
            missing.append(pkg)

    # Optional
    for mod, pkg in [("face_recognition","face_recognition"),
                     ("librosa","librosa"),
                     ("tensorflow","tensorflow")]:
        try:
            __import__(mod); ok(f"{pkg} (optional)")
        except ImportError:
            warn(f"{pkg} not installed (optional)")

    results["dependencies"] = {"missing": missing, "ok": len(deps)-len(missing)}
    return len(missing) == 0


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 2 — IMAGE UTILITIES
# ══════════════════════════════════════════════════════════════════════════════
def test_image_utils():
    hdr("2. image_utils.py")
    import numpy as np

    try:
        from app.logic.image_utils import (
            ensure_bgr_image, ensure_gray_image, decode_image_safe
        )
        ok("image_utils imported")
    except ImportError as e:
        fail(f"Cannot import image_utils: {e}")
        info("Copy image_utils.py → backend/app/logic/image_utils.py")
        results["image_utils"] = "IMPORT_FAILED"
        return False

    import cv2
    variants = [
        ("grayscale 2D",  np.zeros((100,100),       dtype=np.uint8)),
        ("HxWx1",         np.zeros((100,100,1),      dtype=np.uint8)),
        ("BGR 3-ch",      np.zeros((100,100,3),      dtype=np.uint8)),
        ("BGRA 4-ch",     np.zeros((100,100,4),      dtype=np.uint8)),
        ("float32 [0,1]", np.zeros((100,100,3),      dtype=np.float32)),
        ("float32 [0,255]",np.full((100,100,3),128.0,dtype=np.float32)),
    ]

    passed = 0
    for name, arr in variants:
        try:
            out = ensure_bgr_image(arr)
            if check(out.shape==(100,100,3) and out.dtype==np.uint8,
                     f"ensure_bgr_image({name})",
                     f"ensure_bgr_image({name}) → wrong shape/dtype {out.shape} {out.dtype}"):
                passed += 1
        except Exception as e:
            fail(f"ensure_bgr_image({name}) raised: {e}"); FAIL_COUNT+=1

    g = ensure_gray_image(np.zeros((100,100,3),dtype=np.uint8))
    check(g.ndim==2 and g.shape==(100,100),
          "ensure_gray_image returns 2D",
          f"ensure_gray_image wrong shape {g.shape}")

    # decode_image_safe with a real PNG in memory
    import io
    from PIL import Image as PILImage
    buf = io.BytesIO()
    PILImage.fromarray(np.zeros((50,50,3),dtype=np.uint8)).save(buf, format="PNG")
    decoded = decode_image_safe(buf.getvalue())
    check(decoded is not None and decoded.shape==(50,50,3),
          "decode_image_safe works on PNG bytes",
          "decode_image_safe returned None or wrong shape")

    results["image_utils"] = f"{passed}/{len(variants)} variants OK"
    return passed == len(variants)


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 3 — OCR ENGINE
# ══════════════════════════════════════════════════════════════════════════════
def test_ocr():
    hdr("3. OCR Engine")

    # Check tesseract binary
    import subprocess
    try:
        r = subprocess.run(["tesseract","--version"], capture_output=True, text=True)
        ver = r.stdout.split("\n")[0]
        ok(f"Tesseract binary: {ver}")
    except FileNotFoundError:
        fail("Tesseract not found — sudo apt install tesseract-ocr")
        results["ocr"] = "TESSERACT_MISSING"
        return False

    # Check Swahili language pack
    r2 = subprocess.run(["tesseract","--list-langs"], capture_output=True, text=True)
    langs = r2.stdout + r2.stderr
    if "swa" in langs:
        ok("Swahili language pack installed")
    else:
        warn("Swahili pack missing — sudo apt install tesseract-ocr-swa")

    # Test field extractors directly
    try:
        from app.services.document_service import (
            extract_kenyan_id_fields, _extract_name, _extract_id_number,
            _extract_dates, _extract_sex, _extract_nationality
        )
        ok("document_scanning_service imported")
    except ImportError as e:
        fail(f"Import failed: {e}")
        results["ocr"] = "IMPORT_FAILED"
        return False

    # Name extraction tests
    name_cases = [
        ("SURNAME LEO GIVEN NAME CHRISBEN EVANS SEX MALE NATIONALITY KEN",
         "Leo Chrisben Evans", "inline with GIVEN NAME"),
        ("SURNAME LEO CHRISBEN EVANS SEX MALE",
         "Leo Chrisben Evans", "inline without GIVEN NAME"),
        ("SURNAME\nLEO\nGIVEN NAME\nCHRISBEN EVANS\nSEX MALE",
         "Leo Chrisben Evans", "keyword on separate line"),
        ("So One\nSURNAME LEO CHRISBEN EVANS SEX MALE",
         "Leo Chrisben Evans", "OCR noise guard"),
    ]

    name_pass = 0
    for raw, expected, label in name_cases:
        got = _extract_name(raw)
        if check(got.lower()==expected.lower(),
                 f"Name [{label}] → {got!r}",
                 f"Name [{label}] expected {expected!r}, got {got!r}"):
            name_pass += 1

    # ID number tests
    id_cases = [
        ("NUMBER 975162603\nDATE 01.01.2000", "975162603"),
        ("ID No. 12345678", "12345678"),
        ("Serial No 7654321", "7654321"),
    ]
    for text, expected in id_cases:
        got = _extract_id_number(text)
        check(got==expected,
              f"ID extract {expected!r}",
              f"ID expected {expected!r}, got {got!r}")

    # Date extraction
    dob, exp = _extract_dates("DATE OF BIRTH 03.09.2007 DATE OF EXPIRY 05.09.2035")
    check(dob=="03.09.2007", f"DOB extracted: {dob}", f"DOB wrong: {dob}")
    check(exp=="05.09.2035", f"Expiry extracted: {exp}", f"Expiry wrong: {exp}")

    # Sex
    check(_extract_sex("SEX MALE")=="Male",   "Sex: Male",   "Sex extract failed")
    check(_extract_sex("SEX FEMALE")=="Female","Sex: Female", "Sex extract failed")

    # Nationality
    check(_extract_nationality("NATIONALITY KEN")=="Kenyan",
          "Nationality: Kenyan", "Nationality extract failed")

    # Full field extraction on realistic dump
    full_ocr = (
        "JAMHURI YA KENYA REPUBLIC OF KENYA KITAMBULISHO CHA TAIFA\n"
        "SURNAME LEO\nGIVEN NAME CHRISBEN EVANS\n"
        "SEX MALE NATIONALITY KEN DATE OF BIRTH 03. 09. 2007\n"
        "PLACE OF BIRTH EMBAKASI\nNUMBER 975162603\n"
        "DATE OF EXPIRY 05. 09. 2035\nPLACE OF ISSUE NJIRU"
    )
    fields = extract_kenyan_id_fields(full_ocr)
    info(f"Full extraction: {fields}")
    check(bool(fields.get("name")),      f"name: {fields.get('name')}", "name missing")
    check(bool(fields.get("id_number")), f"id_number: {fields.get('id_number')}", "id_number missing")
    check(bool(fields.get("date_of_birth")), f"dob: {fields.get('date_of_birth')}", "dob missing")

    results["ocr"] = f"name {name_pass}/{len(name_cases)}, fields {fields}"
    return name_pass == len(name_cases)


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 4 — RAD MODEL
# ══════════════════════════════════════════════════════════════════════════════
def test_rad_model():
    hdr("4. RAD Autoencoder Model")
    import numpy as np

    try:
        import torch
        ok(f"PyTorch {torch.__version__}")
        check(torch.__version__ >= "2.4",
              "PyTorch >= 2.4",
              f"PyTorch {torch.__version__} < 2.4 — pip install torch --upgrade")
    except ImportError:
        fail("PyTorch not installed"); results["rad_model"]="NO_TORCH"; return False

    # Check model weights exist
    model_paths = [
        BACKEND/"models"/"rad_autoencoder_kenyan.pth",
        BACKEND/"models"/"rad_autoencoder.pth",
    ]
    found_weights = next((p for p in model_paths if p.exists()), None)
    if found_weights:
        ok(f"Model weights found: {found_weights.name}  ({found_weights.stat().st_size//1024} KB)")
    else:
        warn("No model weights found")
        info("Run: python backend/train_models.py")
        results["rad_model"] = "NO_WEIGHTS"

    # Load ModelManager
    try:
        from backend.models.model_loader import ModelManager
        mm    = ModelManager()
        model = mm.load_rad_autoencoder()
        ok("ModelManager loaded")
    except Exception as e:
        fail(f"ModelManager failed: {e}")
        results["rad_model"] = f"LOAD_FAILED: {e}"
        return False

    # Probe input channels
    dummy3 = torch.zeros(1,3,224,224)
    dummy1 = torch.zeros(1,1,224,224)
    in_ch  = None
    for d, ch in [(dummy3,3),(dummy1,1)]:
        try:
            with torch.no_grad(): out = model(d)
            check(out.shape==d.shape, f"Forward pass {ch}ch → {out.shape}", "Shape mismatch")
            in_ch = ch; break
        except Exception:
            pass
    if in_ch is None:
        fail("Model forward pass failed for both 1ch and 3ch")
        results["rad_model"] = "FORWARD_FAILED"
        return False

    # predict_document_authenticity
    try:
        dummy = torch.zeros(1,in_ch,224,224)
        mse, is_forged = mm.predict_document_authenticity(dummy)
        check(isinstance(mse,float),
              f"predict_document_authenticity → mse={mse:.6f}, forged={is_forged}",
              "predict_document_authenticity failed")
    except Exception as e:
        fail(f"predict_document_authenticity error: {e}")

    # Threshold config
    cfg_path = BACKEND/"models"/"kenyan_threshold_config.json"
    if cfg_path.exists():
        cfg = json.loads(cfg_path.read_text())
        ok(f"Threshold config: {cfg.get('threshold',0):.6f}")
    else:
        warn("No kenyan_threshold_config.json — run training first")

    results["rad_model"] = f"OK, {in_ch}ch, mse={mse:.6f}"
    return True


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 5 — DOCUMENT SCANNING SERVICE
# ══════════════════════════════════════════════════════════════════════════════
def test_document_service():
    hdr("5. DocumentScanningService")
    import numpy as np, cv2

    try:
        from app.services.document_service import (
            DocumentScanningService, detect_pixel_anomalies,
            calculate_forgery_score, get_reconstruction
        )
        svc = DocumentScanningService()
        ok("DocumentScanningService instantiated")
    except Exception as e:
        fail(f"Import/init failed: {e}")
        results["document_service"] = f"FAILED: {e}"
        return False

    # Quality analysis on every channel variant
    from app.logic.image_utils import ensure_bgr_image
    variants = [
        np.zeros((200,200),       dtype=np.uint8),
        np.zeros((200,200,1),     dtype=np.uint8),
        np.zeros((200,200,3),     dtype=np.uint8),
        np.zeros((200,200,4),     dtype=np.uint8),
        np.zeros((200,200,3),     dtype=np.float32),
    ]
    for i, arr in enumerate(variants):
        try:
            q = svc.analyze_document_quality(arr)
            check("sharpness" in q,
                  f"analyze_quality variant-{i}",
                  f"analyze_quality variant-{i} missing sharpness")
        except Exception as e:
            fail(f"analyze_quality variant-{i}: {e}"); FAIL_COUNT+=1

    # Forgery detection
    dummy = np.zeros((200,200,3), dtype=np.uint8)
    res   = svc.detect_forgery_indicators(dummy, "test text republic of kenya", "national_id")
    check("risk_score" in res, "detect_forgery_indicators runs", "missing risk_score")

    # detect_pixel_anomalies
    r2 = detect_pixel_anomalies(dummy)
    check("anomaly_score" in r2, "detect_pixel_anomalies runs", "missing anomaly_score")

    # process_document via base64
    import io
    from PIL import Image as PILImage
    buf = io.BytesIO()
    PILImage.fromarray(dummy).save(buf, format="JPEG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    result = svc.process_document(b64)
    check(result.get("success"), "process_document returns success=True",
          f"process_document failed: {result.get('error')}")
    check("verification_status" in result,
          f"verification_status: {result.get('verification_status')}",
          "missing verification_status")

    results["document_service"] = "OK"
    return True


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 6 — BIOMETRIC SERVICE
# ══════════════════════════════════════════════════════════════════════════════
def test_biometric_service():
    hdr("6. BiometricLivenessService")
    import numpy as np

    try:
        from app.services.biometric_service import BiometricLivenessService
        bio = BiometricLivenessService()
        ok("BiometricLivenessService instantiated")
    except Exception as e:
        fail(f"Import failed: {e}")
        results["biometric"] = f"FAILED: {e}"
        return False

    # detect_face on blank frames (expect no face, but no crash)
    variants = [
        np.zeros((480,640),     dtype=np.uint8),   # grayscale
        np.zeros((480,640,1),   dtype=np.uint8),   # HxWx1
        np.zeros((480,640,3),   dtype=np.uint8),   # BGR
        np.zeros((480,640,4),   dtype=np.uint8),   # BGRA
    ]
    for i, arr in enumerate(variants):
        try:
            found, region = bio.detect_face(arr)
            check(isinstance(found, bool),
                  f"detect_face variant-{i} → found={found}",
                  f"detect_face variant-{i} returned non-bool")
        except Exception as e:
            fail(f"detect_face variant-{i} raised: {e}"); FAIL_COUNT+=1

    # generate_new_challenge
    challenge = bio.generate_new_challenge()
    check(isinstance(challenge, str) and len(challenge)>0,
          f"generate_new_challenge → {challenge}",
          "generate_new_challenge failed")

    # process_mbic_frame
    frame = np.zeros((480,640,3), dtype=np.uint8)
    r     = bio.process_mbic_frame(frame)
    check("status" in r and "liveness_score" in r,
          f"process_mbic_frame → status={r.get('status')}",
          "process_mbic_frame missing keys")

    # decode_base64_image
    import io
    from PIL import Image as PILImage
    buf = io.BytesIO()
    PILImage.fromarray(frame).save(buf, format="JPEG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    decoded = bio.decode_base64_image(b64)
    check(decoded is not None and decoded.shape==(480,640,3),
          "decode_base64_image works",
          "decode_base64_image failed")

    results["biometric"] = "OK"
    return True


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 7 — MILVUS / VAULT
# ══════════════════════════════════════════════════════════════════════════════
def test_milvus():
    hdr("7. Milvus Vector Store")
    try:
        from app.db.milvus_client import store_in_vault, search_vault
        ok("milvus_client imported")

        # Try a store + search roundtrip
        test_doc = [{
            "content": f"test_doc_{int(time.time())}",
            "metadata": {"test": True, "ts": str(time.time())}
        }]
        stored = store_in_vault(test_doc)
        check(stored, "store_in_vault succeeded", "store_in_vault failed")

        hits = search_vault("test_doc", limit=1)
        check(isinstance(hits, list),
              f"search_vault returned {len(hits)} result(s)",
              "search_vault failed")

        results["milvus"] = "OK"
        return True
    except Exception as e:
        fail(f"Milvus error: {e}")
        info("Ensure Milvus is running: docker-compose up -d")
        results["milvus"] = f"FAILED: {e}"
        return False


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 8 — REAL IMAGE TEST
# ══════════════════════════════════════════════════════════════════════════════
def test_real_image(image_path: Path):
    hdr(f"8. Real Image Test: {image_path.name}")

    if not image_path.exists():
        warn(f"Image not found: {image_path}")
        info("Pass one with:  python test_components.py --image path/to/id.jpg")
        results["real_image"] = "NO_IMAGE"
        return False

    info(f"Size: {image_path.stat().st_size//1024} KB")

    import numpy as np, cv2, torch
    from PIL import Image as PILImage
    from torchvision import transforms

    # 1. Load and check
    img_bgr = cv2.imread(str(image_path))
    check(img_bgr is not None, f"cv2.imread succeeded {img_bgr.shape}", "imread failed")

    # 2. RAD model prediction
    try:
        from backend.models.model_loader import ModelManager
        mm     = ModelManager()
        pre    = transforms.Compose([transforms.Resize((224,224)), transforms.ToTensor()])
        pil    = PILImage.open(image_path).convert("L")
        tensor = pre(pil).unsqueeze(0)
        mse, is_forged = mm.predict_document_authenticity(tensor)
        confidence = max(0.0, (1.0 - mse) * 100)
        ok(f"RAD → mse={mse:.6f}  forged={is_forged}  confidence={confidence:.1f}%")
        results["rad_real"] = {"mse": mse, "forged": is_forged, "confidence": confidence}
    except Exception as e:
        fail(f"RAD on real image: {e}")

    # 3. OCR
    try:
        from app.services.document_service import (
            _ocr_variants_improved as _ocr_variants, extract_kenyan_id_fields
        )
        text   = _ocr_variants(img_bgr)
        fields = extract_kenyan_id_fields(text)
        info(f"OCR length: {len(text)} chars")
        info(f"Fields extracted: {list(fields.keys())}")
        if fields.get("name"):      ok(f"  name:          {fields['name']}")
        else:                       warn("  name:          not found")
        if fields.get("id_number"): ok(f"  id_number:     {fields['id_number']}")
        else:                       warn("  id_number:     not found")
        if fields.get("date_of_birth"): ok(f"  date_of_birth: {fields['date_of_birth']}")
        else:                           warn("  date_of_birth: not found")
        results["real_ocr"] = fields
    except Exception as e:
        fail(f"OCR on real image: {e}")

    # 4. Full pipeline via process_document
    try:
        from app.services.document_service import document_service
        with open(image_path,"rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        result = document_service.process_document(b64)
        check(result.get("success"),
              f"process_document → status={result.get('verification_status')}  "
              f"score={result.get('overall_score',0):.2f}",
              f"process_document failed: {result.get('error')}")
        results["real_pipeline"] = {
            "status": result.get("verification_status"),
            "score":  result.get("overall_score"),
            "fields": result.get("extracted_fields",{}),
        }
    except Exception as e:
        fail(f"Full pipeline on real image: {e}")
        traceback.print_exc()

    return True


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 9 — LIVE API TESTS
# ══════════════════════════════════════════════════════════════════════════════
def test_api(image_path: Optional[Path] = None):
    hdr("9. Live API Tests  (http://localhost:8000)")
    try:
        import requests
    except ImportError:
        fail("pip install requests"); return False

    BASE = "http://localhost:8000"

    # Health
    try:
        r = requests.get(f"{BASE}/api/v1/health", timeout=5)
        check(r.status_code==200,
              f"GET /api/v1/health → {r.json()}",
              f"Health check failed {r.status_code}")
    except requests.exceptions.ConnectionError:
        warn("Server not running — start with: uvicorn backend.app.main:app --reload")
        results["api"] = "SERVER_DOWN"
        return False

    # Metrics
    r = requests.get(f"{BASE}/api/v1/metrics", timeout=5)
    check(r.status_code==200, "GET /api/v1/metrics", f"metrics failed {r.status_code}")

    # Auth — register test user
    test_email = f"test_{int(time.time())}@test.com"
    reg_payload = {
        "email": test_email, "password": "TestPass123!",
        "firstName": "Test", "citizenship": "kenyan",
        "identificationType": "national_id",
        "identificationNumber": f"9999{int(time.time())%9999:04d}",
    }
    r = requests.post(f"{BASE}/api/v1/auth/register/kenyan",
                      data=reg_payload, timeout=10)
    check(r.status_code in (200,201,400),
          f"POST /auth/register/kenyan → {r.status_code}",
          f"Register unexpected status {r.status_code}: {r.text[:100]}")

    token = None
    if r.status_code in (200,201):
        token = r.json().get("access_token")
        ok(f"Token obtained: {token[:20]}...")

        # Get profile
        r2 = requests.get(f"{BASE}/api/v1/user/profile",
                          headers={"Authorization":f"Bearer {token}"}, timeout=5)
        check(r2.status_code==200,
              f"GET /user/profile → {r2.status_code}",
              f"Profile failed {r2.status_code}")

    # Document upload
    if image_path and image_path.exists():
        with open(image_path,"rb") as f:
            files = {"file": (image_path.name, f, "image/jpeg")}
            r = requests.post(f"{BASE}/api/v1/document/verify",
                              files=files, timeout=30)
        check(r.status_code==200,
              f"POST /document/verify → {r.json().get('authentic')}",
              f"Document verify failed {r.status_code}: {r.text[:100]}")

        # Debug OCR endpoint
        with open(image_path,"rb") as f:
            files = {"document": (image_path.name, f, "image/jpeg")}
            r = requests.post(f"{BASE}/api/v1/document/debug/ocr",
                              files=files, timeout=30)
        if r.status_code==200:
            data = r.json()
            ok(f"DEBUG OCR → best_config={data.get('best_config')} "
               f"len={len(data.get('best_text',''))}")
            info(f"OCR preview: {data.get('best_text','')[:120]!r}")
        else:
            warn(f"Debug OCR {r.status_code} (endpoint may not exist)")

    results["api"] = "OK"
    return True


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 10 — QUICK SMOKE TEST
# ══════════════════════════════════════════════════════════════════════════════
def test_quick():
    hdr("Quick Smoke Test")
    import numpy as np

    checks = []

    # image_utils
    try:
        from app.logic.image_utils import ensure_bgr_image
        out = ensure_bgr_image(np.zeros((100,100),dtype=np.uint8))
        checks.append(("image_utils", out.shape==(100,100,3)))
    except Exception as e:
        checks.append(("image_utils", False))

    # document service
    try:
        from app.services.document_service import extract_kenyan_id_fields
        f = extract_kenyan_id_fields("SURNAME LEO GIVEN NAME CHRISBEN EVANS SEX MALE")
        checks.append(("ocr_extract", bool(f.get("name"))))
    except Exception as e:
        checks.append(("ocr_extract", False))

    # pytorch
    try:
        import torch
        t = torch.zeros(1,3,224,224)
        checks.append(("pytorch", t.shape==(1,3,224,224)))
    except Exception as e:
        checks.append(("pytorch", False))

    # milvus import
    try:
        from app.db.milvus_client import store_in_vault
        checks.append(("milvus_import", True))
    except Exception as e:
        checks.append(("milvus_import", False))

    for name, passed in checks:
        check(passed, name, f"{name} FAILED")

    return all(p for _,p in checks)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--unit",   action="store_true", help="Unit tests only")
    parser.add_argument("--api",    action="store_true", help="Include live API tests")
    parser.add_argument("--quick",  action="store_true", help="Quick smoke test only")
    parser.add_argument("--image",  default=None,        help="Path to a real ID image")
    args = parser.parse_args()

    image_path = Path(args.image) if args.image else \
        BACKEND/"data"/"forensics"/"original"/"IMG_20250924_121136_884~2.jpg"

    print(f"\n{B}{C}{'═'*55}")
    print("  Uhakiki-AI — Component Test Suite")
    print(f"{'═'*55}{X}\n")
    info(f"Project root : {ROOT}")
    info(f"Test image   : {image_path}")
    info(f"Results dir  : {RESULTS_DIR}\n")

    if args.quick:
        test_quick()
    else:
        test_dependencies()
        test_image_utils()
        test_ocr()
        if not args.unit:
            test_rad_model()
        test_document_service()
        test_biometric_service()
        if not args.unit:
            test_milvus()
        if image_path.exists():
            test_real_image(image_path)
        elif args.image:
            warn(f"Image not found: {image_path}")
        if args.api:
            test_api(image_path if image_path.exists() else None)

    # ── summary ───────────────────────────────────────────────────────────────
    total = PASS + FAIL_COUNT
    print(f"\n{B}{C}{'═'*55}{X}")
    print(f"  Passed : {G}{PASS}/{total}{X}")
    print(f"  Failed : {R}{FAIL_COUNT}/{total}{X}")

    # Save JSON report
    report = {
        "timestamp": datetime.now().isoformat(),
        "passed": PASS, "failed": FAIL_COUNT, "total": total,
        "sections": results,
    }
    REPORT_FILE.write_text(json.dumps(report, indent=2, default=str))
    info(f"Report saved: {REPORT_FILE}")

    if FAIL_COUNT == 0:
        print(f"\n{G}{B}  🎉 All checks passed!{X}\n")
    else:
        print(f"\n{R}  Fix the ❌ items above then re-run.{X}")
        print(f"\n{Y}  Quick fixes:{X}")
        print("    pip install torch torchvision --upgrade")
        print("    sudo apt install tesseract-ocr tesseract-ocr-swa")
        print("    python backend/train_models.py --rad-only")
        print("    docker-compose up -d   # for Milvus\n")

    sys.exit(0 if FAIL_COUNT==0 else 1)

if __name__ == "__main__":
    main()
