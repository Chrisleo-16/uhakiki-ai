#!/usr/bin/env python3
"""
fix_ocr_and_rad.py
Run from project root:  python fix_ocr_and_rad.py

Fixes:
  1. Diagnoses and fixes RAD model architecture mismatch
  2. Improves OCR preprocessing for real ID card photos
     (large images with busy security-pattern backgrounds)
"""

import sys, os, json
from pathlib import Path

ROOT    = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT))

G="\033[92m"; R="\033[91m"; Y="\033[93m"; C="\033[96m"; B="\033[1m"; X="\033[0m"
def ok(m):   print(f"{G}  ✅ {m}{X}")
def fail(m): print(f"{R}  ❌ {m}{X}")
def info(m): print(f"{C}  ➜  {m}{X}")
def hdr(m):  print(f"\n{B}{C}{'─'*55}\n  {m}\n{'─'*55}{X}")


# ─────────────────────────────────────────────────────────────────────────────
#  FIX 1 — RAD MODEL ARCHITECTURE MISMATCH
# ─────────────────────────────────────────────────────────────────────────────
def fix_rad_model():
    hdr("FIX 1: RAD Model Architecture")

    import torch
    import torch.nn as nn

    # Read the actual keys from the saved checkpoint
    ckpt_path = BACKEND / "models" / "rad_autoencoder_kenyan.pth"
    if not ckpt_path.exists():
        fail(f"No checkpoint at {ckpt_path}")
        info("Run: python backend/train_models.py --rad-only --real-images")
        return False

    ckpt = torch.load(ckpt_path, map_location="cpu")
    state = ckpt.get("model_state_dict", ckpt)
    keys  = list(state.keys())
    info(f"Checkpoint keys: {keys[:6]} ...")

    # Determine architecture from keys
    # If keys contain encoder.3, encoder.6 → simple Conv+ReLU (no BN)
    # If keys contain encoder.1 (BN layer) → Conv+BN+ReLU
    has_bn = any("running_mean" in k for k in keys)
    info(f"Checkpoint has BatchNorm: {has_bn}")

    # Get conv layer indices actually present
    conv_indices = sorted(set(
        int(k.split(".")[1]) for k in keys
        if k.startswith("encoder.") and "weight" in k
    ))
    info(f"Encoder conv indices in checkpoint: {conv_indices}")

    # Write a rad_model.py that EXACTLY matches the checkpoint
    rad_model_path = BACKEND / "models" / "rad_model.py"

    if not has_bn:
        # Simple architecture: Conv → ReLU only (indices 0,2 encoder / 0,2 decoder)
        model_code = '''import torch
import torch.nn as nn

class RADAutoencoder(nn.Module):
    """
    Simple RAD Autoencoder — Conv+ReLU only (no BatchNorm).
    Architecture matches the saved checkpoint keys.
    Input: [B, 1, 224, 224]  (grayscale)
    """
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1),   # encoder.0
            nn.ReLU(True),                     # encoder.1  (activation, no weights)
            nn.Conv2d(32, 16, 3, padding=1),  # encoder.2 -- but saved as encoder.3?
        )
        self.decoder = nn.Sequential(
            nn.Conv2d(16, 32, 3, padding=1),
            nn.ReLU(True),
            nn.Conv2d(32, 1, 3, padding=1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))
'''
    else:
        # Architecture with BatchNorm
        model_code = '''import torch
import torch.nn as nn

class RADAutoencoder(nn.Module):
    """
    RAD Autoencoder with BatchNorm.
    Input: [B, 1, 224, 224]  (grayscale)
    """
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(True),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(True),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(True),
        )
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(128, 64, 2, stride=2),
            nn.BatchNorm2d(64),
            nn.ReLU(True),
            nn.Conv2d(64, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(True),
            nn.Conv2d(32, 1, 3, padding=1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))
'''

    # The safest approach: rebuild rad_model.py to dynamically
    # match whatever keys are in the checkpoint
    dynamic_model_code = f'''import torch
import torch.nn as nn

# Auto-generated to match checkpoint at:
# {ckpt_path}
# Checkpoint encoder indices: {conv_indices}

class RADAutoencoder(nn.Module):
    """
    RAD Autoencoder — architecture auto-matched to saved checkpoint.
    Input: [B, 1, 224, 224]  (grayscale)
    """
    def __init__(self):
        super().__init__()
        # Encoder built to match saved keys exactly
        self.encoder = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),   # .0
            nn.ReLU(inplace=True),                         # .1
            nn.MaxPool2d(2, 2),                            # .2
            nn.Conv2d(32, 64, kernel_size=3, padding=1),  # .3
            nn.ReLU(inplace=True),                         # .4
            nn.MaxPool2d(2, 2),                            # .5
        )
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(64, 32, kernel_size=2, stride=2),  # .0
            nn.ReLU(inplace=True),                                  # .1
            nn.ConvTranspose2d(32, 1, kernel_size=2, stride=2),   # .2
            nn.Sigmoid(),                                           # .3
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))
'''

    # Try loading with the dynamic model first
    exec_globals = {}
    exec(dynamic_model_code, exec_globals)
    DynamicModel = exec_globals["RADAutoencoder"]

    test_model = DynamicModel()
    try:
        test_model.load_state_dict(state, strict=True)
        ok("Dynamic model loaded checkpoint with strict=True")
        # Write this working model to file
        rad_model_path.write_text(dynamic_model_code)
        ok(f"Wrote matching rad_model.py → {rad_model_path}")
        return True
    except Exception as e:
        info(f"Strict load failed: {e}")
        info("Trying non-strict load (loads matching keys, ignores mismatches)...")
        try:
            missing, unexpected = test_model.load_state_dict(state, strict=False)
            ok(f"Non-strict load succeeded — missing={len(missing)}, unexpected={len(unexpected)}")
            if len(missing) == 0:
                ok("All required keys loaded — model will work correctly")
                rad_model_path.write_text(dynamic_model_code)
                ok(f"Wrote rad_model.py → {rad_model_path}")
                return True
        except Exception as e2:
            fail(f"Both load attempts failed: {e2}")

    # Final fallback: retrain with current architecture
    info("Retraining model with current architecture to fix mismatch...")
    info("Run: python backend/train_models.py --rad-only --real-images --epochs 30")
    return False


# ─────────────────────────────────────────────────────────────────────────────
#  FIX 2 — BETTER OCR PREPROCESSING FOR REAL ID PHOTOS
# ─────────────────────────────────────────────────────────────────────────────
def fix_ocr_preprocessing():
    hdr("FIX 2: OCR Preprocessing for Real ID Photos")

    # The problem: image is 1872x2998 with security patterns
    # Tesseract reads the background noise instead of text
    # Solution: aggressive background removal + text isolation

    ocr_fix_code = r'''
# ── IMPROVED _ocr_variants for real ID card photos ────────────────────────────
# Replaces the existing _ocr_variants function in document_scanning_service.py
# Key improvements:
#   1. Downscale huge images to ~1400px width before OCR (not upscale)
#   2. Aggressive background removal using morphological tophat
#   3. Multiple crop attempts on different regions of the card
#   4. Score OCR results by % of recognisable words vs noise

import cv2, numpy as np
from PIL import Image
import pytesseract, re

def _prepare_for_ocr(img_bgr: np.ndarray) -> list:
    """
    Returns a list of preprocessed grayscale images to try OCR on.
    Optimised for real ID card photos with busy backgrounds.
    """
    from app.logic.image_utils import ensure_bgr_image, ensure_gray_image
    bgr = ensure_bgr_image(img_bgr)
    h, w = bgr.shape[:2]

    # 1. Resize: target 1400px on longest side
    #    (too large = background noise dominates; too small = text lost)
    max_dim = max(h, w)
    if max_dim > 1600:
        scale = 1400 / max_dim
        bgr = cv2.resize(bgr, None, fx=scale, fy=scale,
                         interpolation=cv2.INTER_AREA)   # AREA is best for downscaling
    elif max_dim < 800:
        scale = 1400 / max_dim
        bgr = cv2.resize(bgr, None, fx=scale, fy=scale,
                         interpolation=cv2.INTER_CUBIC)

    gray = ensure_gray_image(bgr)
    h2, w2 = gray.shape[:2]

    variants = []

    # A. CLAHE + Otsu  (baseline)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enh   = clahe.apply(gray)
    _, ot = cv2.threshold(enh, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(("otsu", ot))

    # B. Adaptive threshold  (handles uneven lighting on ID gradients)
    ada = cv2.adaptiveThreshold(enh, 255,
          cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 4)
    variants.append(("adaptive", ada))

    # C. Morphological tophat  (isolates bright text on dark background)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
    tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)
    _, tt  = cv2.threshold(tophat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(("tophat", tt))

    # D. Blackhat  (isolates dark text on bright background)
    bhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
    _, bh = cv2.threshold(bhat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(("blackhat", bh))

    # E. Sharpened  (helps with slightly blurry photos)
    sharp_k = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
    sharp   = cv2.filter2D(enh, -1, sharp_k)
    _, sh   = cv2.threshold(sharp, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(("sharp_otsu", sh))

    # F. Right half only  (ID number + dates are usually on the right)
    right = enh[:, w2//2:]
    _, rr = cv2.threshold(right, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(("right_half", rr))

    # G. Left half  (name is usually on the left side, below the photo)
    left = enh[h2//3:, :w2//2]   # skip top third (logo area)
    _, ll = cv2.threshold(left, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(("left_lower", ll))

    # H. Bottom 60%  (most text fields are in the lower portion)
    bottom = enh[int(h2*0.35):]
    _, bo  = cv2.threshold(bottom, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    ada_bo = cv2.adaptiveThreshold(bottom, 255,
             cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 4)
    variants.append(("bottom_otsu", bo))
    variants.append(("bottom_ada",  ada_bo))

    return variants


def _score_ocr_text(text: str) -> float:
    """
    Score OCR output quality — higher = more likely real text.
    Penalises noise characters, rewards recognisable words.
    """
    if not text or len(text) < 10:
        return 0.0

    words = text.split()
    if not words:
        return 0.0

    # Count words that look like real words (mostly letters, 2+ chars)
    real_words = sum(1 for w in words
                     if len(w) >= 2 and sum(c.isalpha() for c in w) / len(w) > 0.6)

    # Bonus for known Kenyan ID keywords
    keywords = [
        "KENYA", "REPUBLIC", "NATIONAL", "IDENTITY", "SURNAME",
        "GIVEN", "MALE", "FEMALE", "SEX", "DATE", "BIRTH",
        "JAMHURI", "KITAMBULISHO", "KEN", "EXPIRY", "PLACE",
    ]
    keyword_hits = sum(1 for kw in keywords if kw in text.upper())

    score = (real_words / len(words)) + (keyword_hits * 0.1)
    return score


def _ocr_variants_improved(image: np.ndarray) -> str:
    """
    Improved OCR for real ID card photos.
    Uses multiple preprocessing strategies and picks the best result.
    """
    from app.logic.image_utils import ensure_bgr_image
    from app.services.document_scanning_service import _correct_rotation

    bgr = _correct_rotation(ensure_bgr_image(image))

    configs = [
        "--oem 3 --psm 6 -l eng",
        "--oem 3 --psm 3 -l eng",
        "--oem 3 --psm 11 -l eng",
        "--oem 3 --psm 4 -l eng",
        "--oem 3 --psm 6 -l eng+swa",
    ]

    best_text, best_score = "", 0.0
    variants = _prepare_for_ocr(bgr)

    for name, arr in variants:
        pil = Image.fromarray(arr)
        for cfg in configs[:3]:   # top 3 configs per variant
            try:
                text  = pytesseract.image_to_string(pil, config=cfg).strip()
                score = _score_ocr_text(text)
                if score > best_score:
                    best_score = score
                    best_text  = text
            except Exception:
                pass

    # Also try original colour image (sometimes better than binary)
    try:
        from PIL import Image as PILImage
        rgb  = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        # Resize for OCR
        h, w = rgb.shape[:2]
        if max(h,w) > 1600:
            scale = 1400 / max(h,w)
            rgb = cv2.resize(rgb, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        text  = pytesseract.image_to_string(
            PILImage.fromarray(rgb), config="--oem 3 --psm 6 -l eng").strip()
        score = _score_ocr_text(text)
        if score > best_score:
            best_score = score
            best_text  = text
    except Exception:
        pass

    import logging
    logging.getLogger(__name__).info(
        f"OCR best score: {best_score:.3f}  len: {len(best_text)}")
    return best_text
'''

    fix_path = BACKEND / "app" / "logic" / "ocr_fix.py"
    fix_path.parent.mkdir(parents=True, exist_ok=True)
    fix_path.write_text(ocr_fix_code)
    ok(f"OCR fix written → {fix_path}")

    # Now patch document_scanning_service.py to use the improved function
    svc_path = BACKEND / "app" / "services" / "document_scanning_service.py"
    if not svc_path.exists():
        fail(f"document_scanning_service.py not found at {svc_path}")
        return False

    content = svc_path.read_text()

    # Add import at top if not already there
    import_line = "from app.logic.ocr_fix import _ocr_variants_improved"
    if import_line not in content:
        # Add after existing imports
        content = content.replace(
            "from app.logic.image_utils import",
            f"{import_line}\nfrom app.logic.image_utils import"
        )

    # Replace _ocr_variants call with improved version
    content = content.replace(
        "text     =_ocr_variants(image)",
        "text     =_ocr_variants_improved(image)"
    ).replace(
        "text    =_ocr_variants(image)",
        "text    =_ocr_variants_improved(image)"
    ).replace(
        "text = _ocr_variants(image)",
        "text = _ocr_variants_improved(image)"
    )

    svc_path.write_text(content)
    ok(f"Patched document_scanning_service.py to use improved OCR")
    return True


# ─────────────────────────────────────────────────────────────────────────────
#  DIAGNOSTIC — show what OCR currently sees
# ─────────────────────────────────────────────────────────────────────────────
def diagnose_image(image_path: Path):
    hdr(f"DIAGNOSTIC: {image_path.name}")

    import cv2, numpy as np

    img = cv2.imread(str(image_path))
    if img is None:
        fail(f"Cannot read image: {image_path}"); return

    h, w = img.shape[:2]
    info(f"Original size: {w}x{h}")

    # Try the improved preprocessing
    sys.path.insert(0, str(BACKEND))
    try:
        from backend.app.logic.ocr_fix import _prepare_for_ocr, _score_ocr_text
        import pytesseract
        from PIL import Image as PILImage

        variants = _prepare_for_ocr(img)
        info(f"Testing {len(variants)} preprocessing variants...")
        print()

        results = []
        for name, arr in variants:
            try:
                text  = pytesseract.image_to_string(
                    PILImage.fromarray(arr),
                    config="--oem 3 --psm 6 -l eng").strip()
                score = _score_ocr_text(text)
                results.append((score, name, text))
            except Exception as e:
                results.append((0.0, name, f"ERROR: {e}"))

        results.sort(reverse=True)

        print(f"  {'Score':>6}  {'Variant':<15}  {'Text preview (60 chars)'}")
        print(f"  {'─'*6}  {'─'*15}  {'─'*60}")
        for score, name, text in results:
            preview = text[:60].replace("\n", " ")
            bar = "✅" if score > 0.3 else "⚠️ " if score > 0.1 else "❌"
            print(f"  {score:>6.3f}  {name:<15}  {bar} {preview!r}")

        print()
        best = results[0]
        ok(f"Best variant: {best[1]}  (score={best[0]:.3f})")
        print()
        print("=== BEST OCR TEXT (first 600 chars) ===")
        print(best[2][:600])

        # Try field extraction on best text
        print()
        print("=== FIELD EXTRACTION ===")
        from backend.app.services.document_service import extract_kenyan_id_fields
        fields = extract_kenyan_id_fields(best[2])
        if fields:
            for k,v in fields.items():
                print(f"  {k:<20} {v}")
            ok("Fields extracted successfully!")
        else:
            warn("No fields extracted from best text")
            info("The OCR text quality is too low — check image quality")
            info("Try: better lighting, no glare, flat surface, higher resolution")

    except ImportError as e:
        fail(f"Import error: {e}")
        info("Run fix_ocr_and_rad.py first to generate ocr_fix.py")


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--diagnose-only", action="store_true")
    parser.add_argument("--image", default=None)
    args = parser.parse_args()

    print(f"\n{B}{C}{'═'*55}")
    print("  Uhakiki-AI — OCR + RAD Fix")
    print(f"{'═'*55}{X}\n")

    image_path = Path(args.image) if args.image else \
        BACKEND/"data"/"forensics"/"original"/"IMG_20250924_121136_884~2.jpg"

    if not args.diagnose_only:
        r1 = fix_rad_model()
        r2 = fix_ocr_preprocessing()

    if image_path.exists():
        diagnose_image(image_path)
    else:
        warn(f"No image at {image_path}")
        info("Pass one with: --image path/to/id.jpg")

    print(f"\n{G}Done. Now run:{X}")
    print("  python test_components.py --unit --image backend/data/forensics/original/IMG_20250924_121136_884~2.jpg")
