#!/bin/bash
# =============================================================
#  run_local_test.sh
#  Step-by-step local test for Uhakiki-AI document scanning
#
#  Run from project root:
#    cd ~/uhakiki-ai
#    bash run_local_test.sh
# =============================================================

G="\033[92m"; R="\033[91m"; Y="\033[93m"; C="\033[96m"; B="\033[1m"; X="\033[0m"
ok()   { echo -e "${G}  ✅ $*${X}"; }
fail() { echo -e "${R}  ❌ $*${X}"; }
warn() { echo -e "${Y}  ⚠️  $*${X}"; }
info() { echo -e "${C}  ➜  $*${X}"; }
hdr()  { echo -e "\n${B}${C}══════════════════════════════════════════\n  $*\n══════════════════════════════════════════${X}"; }

IMG1="/home/cb-fx/uhakiki-ai/backend/data/forensics/original/IMG_20250924_121149_117~2.jpg"
IMG2="/home/cb-fx/uhakiki-ai/backend/data/forensics/original/IMG_20250924_121136_884~2.jpg"
ROOT="/home/cb-fx/uhakiki-ai"


# ══════════════════════════════════════════════════════════════
# STEP 1 — ENVIRONMENT CHECK
# ══════════════════════════════════════════════════════════════
hdr "STEP 1 — Environment"

info "Python: $(which python)"
info "Pip:    $(which pip)"
info "Venv active: ${VIRTUAL_ENV:-NOT ACTIVE}"

if [ -z "$VIRTUAL_ENV" ]; then
    warn "Venv not active — activating now"
    source "$ROOT/venv/bin/activate" 2>/dev/null || {
        fail "Could not activate venv at $ROOT/venv"
        echo "Run: source ~/uhakiki-ai/venv/bin/activate"
        exit 1
    }
    ok "Venv activated: $VIRTUAL_ENV"
else
    ok "Venv already active: $VIRTUAL_ENV"
fi


# ══════════════════════════════════════════════════════════════
# STEP 2 — IMAGE FILES EXIST
# ══════════════════════════════════════════════════════════════
hdr "STEP 2 — Test images"

for img in "$IMG1" "$IMG2"; do
    if [ -f "$img" ]; then
        size=$(wc -c < "$img")
        ok "Found: $(basename $img)  ($size bytes)"
    else
        fail "Missing: $img"
    fi
done


# ══════════════════════════════════════════════════════════════
# STEP 3 — CORE DEPENDENCY CHECK
# ══════════════════════════════════════════════════════════════
hdr "STEP 3 — Core dependencies"

python - << 'PYCHECK'
import sys
deps = {
    "cv2":           "opencv-python",
    "numpy":         "numpy",
    "PIL":           "Pillow",
    "pytesseract":   "pytesseract",
    "torch":         "torch",
    "torchvision":   "torchvision",
}
missing = []
for mod, pkg in deps.items():
    try:
        m = __import__(mod)
        ver = getattr(m, '__version__', 'ok')
        print(f"  ✅ {pkg:<25} {ver}")
    except ImportError:
        print(f"  ❌ {pkg:<25} MISSING — pip install {pkg}")
        missing.append(pkg)

if missing:
    print(f"\n  Install missing: pip install {' '.join(missing)}")
    sys.exit(1)
else:
    print("\n  All core deps present")
PYCHECK
[ $? -ne 0 ] && fail "Fix missing dependencies first" && exit 1


# ══════════════════════════════════════════════════════════════
# STEP 4 — TESSERACT CHECK
# ══════════════════════════════════════════════════════════════
hdr "STEP 4 — Tesseract OCR"

if command -v tesseract &>/dev/null; then
    ok "Tesseract: $(tesseract --version 2>&1 | head -1)"
    # Check Swahili pack
    if tesseract --list-langs 2>/dev/null | grep -q "swa"; then
        ok "Swahili language pack (swa) installed"
    else
        warn "Swahili pack missing — install with: sudo apt install tesseract-ocr-swa"
        warn "English-only OCR will be used (still works, just less accurate)"
    fi
else
    fail "Tesseract not found — install: sudo apt install tesseract-ocr"
    exit 1
fi


# ══════════════════════════════════════════════════════════════
# STEP 5 — IMAGE UTILS TEST
# ══════════════════════════════════════════════════════════════
hdr "STEP 5 — image_utils channel safety"

cd "$ROOT/backend"
python - << 'PYCHECK'
import sys, numpy as np, cv2
sys.path.insert(0, '.')
try:
    from app.logic.image_utils import ensure_bgr_image, ensure_gray_image
    tests = [
        ("gray 2D",   np.zeros((100,100),      dtype=np.uint8)),
        ("HxWx1",     np.zeros((100,100,1),    dtype=np.uint8)),
        ("BGR 3ch",   np.zeros((100,100,3),    dtype=np.uint8)),
        ("BGRA 4ch",  np.zeros((100,100,4),    dtype=np.uint8)),
        ("float32",   np.zeros((100,100,3),    dtype=np.float32)),
    ]
    all_ok = True
    for name, arr in tests:
        try:
            out = ensure_bgr_image(arr)
            if out.shape == (100,100,3) and out.dtype == np.uint8:
                print(f"  ✅ ensure_bgr_image({name})")
            else:
                print(f"  ❌ ensure_bgr_image({name}) — wrong shape {out.shape}")
                all_ok = False
        except Exception as e:
            print(f"  ❌ ensure_bgr_image({name}) raised: {e}")
            all_ok = False
    if all_ok:
        print("  ✅ All channel variants handled correctly")
    else:
        sys.exit(1)
except ImportError as e:
    print(f"  ❌ Cannot import image_utils: {e}")
    print("     Copy image_utils.py → backend/app/logic/image_utils.py")
    sys.exit(1)
PYCHECK
[ $? -ne 0 ] && fail "Fix image_utils first" && exit 1


# ══════════════════════════════════════════════════════════════
# STEP 6 — DIRECT OCR ON BOTH IMAGES
# ══════════════════════════════════════════════════════════════
hdr "STEP 6 — Direct Tesseract OCR on test images"

python - "$IMG1" "$IMG2" << 'PYCHECK'
import sys, cv2, numpy as np
from PIL import Image
import pytesseract

images = sys.argv[1:]
for path in images:
    print(f"\n  Image: {path.split('/')[-1]}")
    img = cv2.imread(path)
    if img is None:
        print(f"  ❌ Could not read image")
        continue

    h, w = img.shape[:2]
    print(f"  Size: {w}x{h}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Scale up if small
    if w < 1400:
        scale = 1400 / w
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    clahe    = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    _, otsu  = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    best, best_len = "", 0
    for arr, cfg in [
        (enhanced, "--oem 3 --psm 6 -l eng"),
        (otsu,     "--oem 3 --psm 6 -l eng"),
        (enhanced, "--oem 3 --psm 3 -l eng"),
    ]:
        try:
            t = pytesseract.image_to_string(Image.fromarray(arr), config=cfg).strip()
            if len(t) > best_len:
                best_len, best = len(t), t
        except Exception as e:
            pass

    print(f"  OCR length: {best_len} chars")
    if best_len > 0:
        print(f"  OCR preview (first 200 chars):")
        print("  " + best[:200].replace("\n", "\n  "))
        print(f"  ✅ OCR working")
    else:
        print(f"  ❌ No text extracted — check image quality")
PYCHECK


# ══════════════════════════════════════════════════════════════
# STEP 7 — DOCUMENT SCANNING SERVICE ON BOTH IMAGES
# ══════════════════════════════════════════════════════════════
hdr "STEP 7 — DocumentScanningService full pipeline"

python - "$IMG1" "$IMG2" << 'PYCHECK'
import sys, base64, json
sys.path.insert(0, '.')

try:
    from app.services.document_scanning_service import document_service, extract_kenyan_id_fields
except ImportError as e:
    print(f"  ❌ Import failed: {e}")
    print("     Copy document_scanning_service.py → backend/app/services/document_scanning_service.py")
    sys.exit(1)

images = sys.argv[1:]
for path in images:
    print(f"\n  ── {path.split('/')[-1]} ─────────────────────────────")
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    result = document_service.process_document(b64)

    if not result.get("success"):
        print(f"  ❌ Failed: {result.get('error')}")
        continue

    print(f"  Document type     : {result.get('document_type')}")
    print(f"  Overall score     : {result.get('overall_score', 0):.3f}")
    print(f"  Verification      : {result.get('verification_status')}")

    q = result.get("quality_analysis", {})
    print(f"  Sharpness         : {q.get('sharpness', 0):.1f}")
    print(f"  Edge density      : {q.get('edge_density', 0):.3f}")
    print(f"  Quality score     : {q.get('quality_score', 0):.3f}")
    print(f"  Acceptable        : {q.get('is_acceptable')}")

    fa = result.get("forgery_analysis", {})
    print(f"  Risk score        : {fa.get('risk_score', 0):.3f}")
    print(f"  Risk level        : {fa.get('risk_level')}")
    if fa.get("indicators"):
        print(f"  Indicators        : {', '.join(fa['indicators'])}")

    fields = result.get("extracted_fields", {})
    print(f"  Extracted fields  :")
    if fields:
        for k, v in fields.items():
            if v:
                print(f"    {k:<20} {v}")
    else:
        print(f"    (none extracted — OCR may need tuning)")

    print(f"  Raw text preview  :")
    raw = result.get("extracted_text", "")
    print("    " + raw[:150].replace("\n", "\n    ") if raw else "    (empty)")

    print(f"  ✅ Pipeline completed")
PYCHECK


# ══════════════════════════════════════════════════════════════
# STEP 8 — SELF-TEST: NAME EXTRACTION LOGIC
# ══════════════════════════════════════════════════════════════
hdr "STEP 8 — Name extraction self-test"

python - << 'PYCHECK'
import sys
sys.path.insert(0, '.')
try:
    from app.services.document_scanning_service import _extract_name, extract_kenyan_id_fields
except ImportError as e:
    print(f"  ❌ Import failed: {e}")
    sys.exit(1)

cases = [
    ("SURNAME LEO GIVEN NAME CHRISBEN EVANS SEX MALE", "Leo Chrisben Evans"),
    ("SURNAME LEO CHRISBEN EVANS SEX MALE",            "Leo Chrisben Evans"),
    ("SURNAME\nLEO\nGIVEN NAME\nCHRISBEN EVANS",       "Leo Chrisben Evans"),
]
all_pass = True
for text, expected in cases:
    got = _extract_name(text)
    ok  = got.lower() == expected.lower()
    if not ok: all_pass = False
    print(f"  {'✅' if ok else '❌'}  expected={expected!r}  got={got!r}")

print()
if all_pass:
    print("  ✅ All name extraction tests passed")
else:
    print("  ❌ Some name extraction tests failed")
    sys.exit(1)
PYCHECK


# ══════════════════════════════════════════════════════════════
# STEP 9 — FORGERY DETECTION ON BOTH IMAGES
# ══════════════════════════════════════════════════════════════
hdr "STEP 9 — Forgery / anomaly detection"

python - "$IMG1" "$IMG2" << 'PYCHECK'
import sys, cv2, numpy as np
sys.path.insert(0, '.')

try:
    from app.services.document_scanning_service import detect_pixel_anomalies
except ImportError as e:
    print(f"  ❌ Import failed: {e}")
    sys.exit(1)

images = sys.argv[1:]
for path in images:
    img = cv2.imread(path)
    if img is None:
        print(f"  ❌ Could not read {path}")
        continue

    result = detect_pixel_anomalies(img)
    name   = path.split("/")[-1]
    print(f"\n  {name}")
    print(f"    is_forged    : {result.get('is_forged')}")
    print(f"    risk_level   : {result.get('risk_level')}")
    print(f"    anomaly_score: {result.get('anomaly_score', 0):.3f}")
    inds = result.get("forgery_indicators", [])
    if inds:
        print(f"    indicators   : {', '.join(inds)}")
    else:
        print(f"    indicators   : none (clean document)")
    print(f"  ✅ Anomaly detection completed")
PYCHECK


# ══════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════
hdr "ALL STEPS COMPLETE"
echo -e "${G}  If all steps showed ✅ your pipeline is working correctly.${X}"
echo -e "${Y}  If any step showed ❌ fix that step before starting the server.${X}"
echo ""
echo -e "  ${B}Next:${X} start the server with:"
echo -e "  ${C}  uvicorn backend.app.main:app --reload${X}"
echo ""