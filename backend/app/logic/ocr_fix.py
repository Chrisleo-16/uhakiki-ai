
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
    from app.services.document_service import _correct_rotation

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
