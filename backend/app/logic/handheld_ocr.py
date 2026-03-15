"""
handheld_ocr.py
Place at: backend/app/logic/handheld_ocr.py

Handles the 5 real-world challenges of hand-held ID photos:
  1. Perspective distortion (card held at angle)
  2. Uneven lighting / shadows from fingers
  3. Motion blur from handheld shot
  4. Background clutter (walls, tables, clothing)
  5. Partial finger occlusion over text

Usage:
    from app.logic.handheld_ocr import extract_id_from_handheld
    fields = extract_id_from_handheld(bgr_image)
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image
import logging
import re

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
#  STEP 1 — CARD DETECTION & PERSPECTIVE CORRECTION
#  Finds the white/cream ID card rectangle even when held at angle
# ─────────────────────────────────────────────────────────────────────────────

def _find_card_contour(bgr: np.ndarray):
    """
    Find the ID card rectangle in a hand-held photo.
    Returns 4-point contour or None.
    """
    h, w = bgr.shape[:2]

    # Resize for faster processing
    scale  = 800 / max(h, w)
    small  = cv2.resize(bgr, None, fx=scale, fy=scale)
    sh, sw = small.shape[:2]

    gray   = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

    # Edge detection with blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges   = cv2.Canny(blurred, 30, 100)

    # Dilate edges to close gaps
    kernel  = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated = cv2.dilate(edges, kernel, iterations=2)

    contours, _ = cv2.findContours(
        dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    # Find largest roughly-rectangular contour
    best      = None
    best_area = 0
    min_area  = sh * sw * 0.15  # card should be at least 15% of frame

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue

        # Approximate to polygon
        peri   = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

        if len(approx) == 4 and area > best_area:
            best      = approx
            best_area = area

    if best is None:
        return None

    # Scale back to original image coordinates
    best = (best / scale).astype(np.float32)
    return best


def _order_points(pts: np.ndarray) -> np.ndarray:
    """Order 4 points: top-left, top-right, bottom-right, bottom-left."""
    pts  = pts.reshape(4, 2)
    rect = np.zeros((4, 2), dtype=np.float32)

    s         = pts.sum(axis=1)
    rect[0]   = pts[np.argmin(s)]   # top-left
    rect[2]   = pts[np.argmax(s)]   # bottom-right

    diff      = np.diff(pts, axis=1)
    rect[1]   = pts[np.argmin(diff)] # top-right
    rect[3]   = pts[np.argmax(diff)] # bottom-left

    return rect


def _perspective_correct(bgr: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """
    Apply perspective transform to get a flat, straight-on view of the card.
    Output is always landscape (wider than tall) at ~1400x880 px.
    """
    rect = _order_points(pts)
    tl, tr, br, bl = rect

    # Card dimensions — Kenyan ID is 85.6mm x 54mm (ISO/IEC 7810 ID-1)
    # Use aspect ratio to set output size
    w1 = np.linalg.norm(br - bl)
    w2 = np.linalg.norm(tr - tl)
    h1 = np.linalg.norm(tr - br)
    h2 = np.linalg.norm(tl - bl)

    out_w = int(max(w1, w2))
    out_h = int(max(h1, h2))

    # Ensure landscape
    if out_h > out_w:
        out_w, out_h = out_h, out_w
        rect = np.array([bl, tl, tr, br], dtype=np.float32)

    # Scale to target size
    target_w = 1400
    target_h = int(target_w * out_h / out_w) if out_w > 0 else 880
    target_h = max(target_h, 600)

    dst = np.array([
        [0,        0],
        [target_w, 0],
        [target_w, target_h],
        [0,        target_h],
    ], dtype=np.float32)

    M       = cv2.getPerspectiveTransform(rect, dst)
    warped  = cv2.warpPerspective(bgr, M, (target_w, target_h))
    return warped


def extract_card_region(bgr: np.ndarray) -> np.ndarray:
    """
    Try to detect and perspective-correct the card.
    Falls back to the original image if detection fails.
    """
    pts = _find_card_contour(bgr)
    if pts is not None:
        try:
            corrected = _perspective_correct(bgr, pts)
            logger.info("Card detected and perspective corrected")
            return corrected
        except Exception as e:
            logger.warning(f"Perspective correction failed: {e}")

    # Fallback: just resize and return
    h, w   = bgr.shape[:2]
    max_dim = max(h, w)
    if max_dim > 1600:
        scale = 1400 / max_dim
        bgr   = cv2.resize(bgr, None, fx=scale, fy=scale,
                           interpolation=cv2.INTER_AREA)
    logger.info("Card detection failed — using full image")
    return bgr


# ─────────────────────────────────────────────────────────────────────────────
#  STEP 2 — DEBLUR / SHARPEN
#  Wiener-like sharpening for motion blur common in handheld shots
# ─────────────────────────────────────────────────────────────────────────────

def _deblur(gray: np.ndarray) -> np.ndarray:
    """Apply unsharp masking to recover motion-blurred text."""
    # Measure blur level
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()

    if blur_score > 300:
        return gray  # already sharp enough

    # Progressive sharpening based on blur level
    if blur_score < 50:
        # Very blurry — aggressive sharpen
        kernel = np.array([
            [-1, -1, -1, -1, -1],
            [-1,  2,  2,  2, -1],
            [-1,  2,  8,  2, -1],
            [-1,  2,  2,  2, -1],
            [-1, -1, -1, -1, -1],
        ]) / 8.0
    else:
        # Moderate blur — gentle sharpen
        kernel = np.array([
            [ 0, -1,  0],
            [-1,  5, -1],
            [ 0, -1,  0],
        ])

    sharpened = cv2.filter2D(gray, -1, kernel)
    return sharpened


# ─────────────────────────────────────────────────────────────────────────────
#  STEP 3 — SHADOW / UNEVEN LIGHTING REMOVAL
#  Divides by background estimate to flatten illumination
# ─────────────────────────────────────────────────────────────────────────────

def _remove_shadows(gray: np.ndarray) -> np.ndarray:
    """
    Remove shadows and uneven lighting.
    Uses large-kernel blur as background estimate then divides.
    """
    # Large blur = background lighting estimate
    bg = cv2.GaussianBlur(gray, (61, 61), 0)

    # Divide by background (normalise illumination)
    norm = cv2.divide(gray.astype(np.float32),
                      bg.astype(np.float32) + 1e-6)

    # Scale to 0-255
    norm = cv2.normalize(norm, None, 0, 255, cv2.NORM_MINMAX)
    return norm.astype(np.uint8)


# ─────────────────────────────────────────────────────────────────────────────
#  STEP 4 — TEXT ISOLATION
#  Multiple strategies optimised for ID card colours
# ─────────────────────────────────────────────────────────────────────────────

def _build_variants(bgr: np.ndarray) -> list:
    """
    Build preprocessed image variants optimised for hand-held ID photos.
    """
    h, w   = bgr.shape[:2]
    gray   = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    # Apply shadow removal
    flat   = _remove_shadows(gray)

    # Deblur
    sharp  = _deblur(flat)

    # CLAHE
    clahe  = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enh    = clahe.apply(sharp)

    variants = []

    # 1. Adaptive threshold (best for uneven lighting)
    ada = cv2.adaptiveThreshold(
        enh, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 4
    )
    variants.append(("adaptive_shadow_removed", ada))

    # 2. Otsu on shadow-removed image
    _, ot = cv2.threshold(enh, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(("otsu_shadow_removed", ot))

    # 3. Blackhat morphology (isolates dark text on any background)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
    bhat   = cv2.morphologyEx(flat, cv2.MORPH_BLACKHAT, kernel)
    _, bh  = cv2.threshold(bhat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(("blackhat", bh))

    # 4. Tophat (bright text on dark background)
    toph   = cv2.morphologyEx(flat, cv2.MORPH_TOPHAT, kernel)
    _, tt  = cv2.threshold(toph, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(("tophat", tt))

    # 5. Green channel only (Kenyan ID teal background suppressed)
    green  = bgr[:, :, 1]
    green  = _remove_shadows(green)
    _, gr  = cv2.threshold(green, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(("green_channel", gr))

    # 6. Red channel (dark text on teal = high contrast in red)
    red    = bgr[:, :, 2]  # BGR so index 2 = red
    red    = _remove_shadows(red)
    _, rd  = cv2.threshold(red, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(("red_channel", rd))

    # 7. Bottom 65% — where all text fields live
    bottom = enh[int(h * 0.30):]
    ada_b  = cv2.adaptiveThreshold(
        bottom, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 4
    )
    variants.append(("bottom_adaptive", ada_b))

    # 8. Invert + threshold (sometimes helps)
    inv    = cv2.bitwise_not(enh)
    _, iv  = cv2.threshold(inv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(("inverted", iv))

    return variants


# ─────────────────────────────────────────────────────────────────────────────
#  STEP 5 — OCR SCORING
# ─────────────────────────────────────────────────────────────────────────────

KEYWORDS = [
    "KENYA", "REPUBLIC", "NATIONAL", "IDENTITY", "SURNAME",
    "GIVEN", "MALE", "FEMALE", "SEX", "DATE", "BIRTH",
    "JAMHURI", "KITAMBULISHO", "KEN", "EXPIRY", "PLACE",
    "NUMBER", "NATIONALITY", "ISSUE", "EMBAKASI", "NJIRU",
    "NAIROBI", "MOMBASA", "KISUMU", "NAKURU",
]


def _score(text: str) -> float:
    if not text or len(text) < 15:
        return 0.0
    words        = text.split()
    real_words   = sum(
        1 for w in words
        if len(w) >= 2 and sum(c.isalpha() for c in w) / len(w) > 0.55
    )
    keyword_hits = sum(1 for kw in KEYWORDS if kw in text.upper())
    return (real_words / max(len(words), 1)) * 100 + keyword_hits * 6


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def extract_text_handheld(bgr: np.ndarray) -> str:
    """
    Extract text from a hand-held ID card photo.

    Pipeline:
      1. Detect card rectangle and perspective-correct
      2. Remove shadows and uneven lighting
      3. Deblur if motion-blurred
      4. Try 8 preprocessing variants × 4 OCR configs
      5. Return best result by keyword score
    """
    from app.logic.image_utils import ensure_bgr_image

    bgr = ensure_bgr_image(bgr)

    # Step 1: Perspective correction
    card = extract_card_region(bgr)

    # Step 2-4: Build variants
    variants = _build_variants(card)

    configs = [
        "--oem 3 --psm 6 -l eng",
        "--oem 3 --psm 3 -l eng",
        "--oem 3 --psm 11 -l eng",
        "--oem 3 --psm 6 -l eng+swa",
    ]

    best_text, best_score = "", 0.0

    for name, arr in variants:
        # Add white padding — helps Tesseract at edges
        padded = cv2.copyMakeBorder(
            arr, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255
        )
        pil = Image.fromarray(padded)
        for cfg in configs:
            try:
                text  = pytesseract.image_to_string(pil, config=cfg).strip()
                score = _score(text)
                if score > best_score:
                    best_score = score
                    best_text  = text
                    logger.debug(f"New best: {name}/{cfg} score={score:.1f}")
            except Exception:
                pass

    # Also try original colour (sometimes beats binary)
    try:
        rgb   = cv2.cvtColor(card, cv2.COLOR_BGR2RGB)
        text  = pytesseract.image_to_string(
            Image.fromarray(rgb), config="--oem 3 --psm 6 -l eng"
        ).strip()
        score = _score(text)
        if score > best_score:
            best_score = score
            best_text  = text
    except Exception:
        pass

    logger.info(f"Handheld OCR best score: {best_score:.1f}  len: {len(best_text)}")
    return best_text


def extract_id_from_handheld(bgr: np.ndarray) -> dict:
    """
    Full pipeline: hand-held photo → extracted ID fields.
    Drop-in replacement for the standard pipeline.
    """
    from app.services.document_service import extract_kenyan_id_fields

    text   = extract_text_handheld(bgr)
    fields = extract_kenyan_id_fields(text)
    return fields


# ─────────────────────────────────────────────────────────────────────────────
#  SELF TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.path.insert(0, "backend")

    if len(sys.argv) < 2:
        print("Usage: python handheld_ocr.py path/to/id_photo.jpg")
        sys.exit(1)

    img = cv2.imread(sys.argv[1])
    if img is None:
        print(f"Cannot read: {sys.argv[1]}")
        sys.exit(1)

    h, w = img.shape[:2]
    print(f"Image: {w}x{h}")

    # Test card detection
    pts = _find_card_contour(img)
    if pts is not None:
        print(f"✅ Card detected — perspective correcting")
        card = _perspective_correct(img, pts)
        print(f"   Corrected size: {card.shape[1]}x{card.shape[0]}")
    else:
        print(f"⚠️  Card not detected — using full image")
        card = img

    # Run full pipeline
    fields = extract_id_from_handheld(img)
    print("\n=== EXTRACTED FIELDS ===")
    if fields:
        for k, v in fields.items():
            print(f"  {k:<20} {v}")
    else:
        print("  No fields extracted")
        print("  Tips: better lighting, card fills more of frame")