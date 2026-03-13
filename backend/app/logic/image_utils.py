"""
image_utils.py
Centralized image normalization utilities.
All OpenCV operations in this project should call ensure_bgr_image() or
ensure_gray_image() BEFORE touching the pixel data.
"""

import cv2
import numpy as np
from typing import Optional


def ensure_bgr_image(image: np.ndarray, source_is_rgb: bool = False) -> np.ndarray:
    """
    Guarantee the returned image is 3-channel uint8 BGR.

    Handles every shape/dtype variant that can arrive from:
      - cv2.imdecode (already BGR, but may be BGRA from PNGs)
      - PIL → numpy conversions (RGB or L or RGBA)
      - Single-channel arrays from grayscale PNGs
      - Float32 tensors accidentally passed in
    """
    # ... existing dtype normalisation ...
    if image.dtype != np.uint8:
        # Float images in [0,1] → scale to [0,255]
        if image.dtype in (np.float32, np.float64):
            if image.max() <= 1.0:
                image = (image * 255).clip(0, 255).astype(np.uint8)
            else:
                image = image.clip(0, 255).astype(np.uint8)
        else:
            image = image.astype(np.uint8)

    # ── shape normalisation ───────────────────────────────────────────────────
    ndim = image.ndim

    if ndim == 2:
        # True grayscale → BGR
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    if ndim == 3:
        channels = image.shape[2]

        if channels == 1:
            # Single-channel packed as HxWx1 → BGR
            return cv2.cvtColor(image[:, :, 0], cv2.COLOR_GRAY2BGR)

        if channels == 3:
            # Assume BGR already (cv2.imdecode default); return as-is
            if source_is_rgb:
                return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            return image   # assume BGR (cv2.imdecode default)

        if channels == 4:
            # BGRA (e.g. PNG with alpha) → BGR
            return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

    raise ValueError(
        f"ensure_bgr_image: unexpected image shape {image.shape} / dtype {image.dtype}"
    )
    if image is None:
        raise ValueError("ensure_bgr_image received None")

    # ── dtype normalisation ───────────────────────────────────────────────────
    if image.dtype != np.uint8:
        # Float images in [0,1] → scale to [0,255]
        if image.dtype in (np.float32, np.float64):
            if image.max() <= 1.0:
                image = (image * 255).clip(0, 255).astype(np.uint8)
            else:
                image = image.clip(0, 255).astype(np.uint8)
        else:
            image = image.astype(np.uint8)

    # ── shape normalisation ───────────────────────────────────────────────────
    ndim = image.ndim

    if ndim == 2:
        # True grayscale → BGR
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    if ndim == 3:
        channels = image.shape[2]

        if channels == 1:
            # Single-channel packed as HxWx1 → BGR
            return cv2.cvtColor(image[:, :, 0], cv2.COLOR_GRAY2BGR)

        if channels == 3:
            # Assume BGR already (cv2.imdecode default); return as-is
            return image

        if channels == 4:
            # BGRA (e.g. PNG with alpha) → BGR
            return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

    raise ValueError(
        f"ensure_bgr_image: unexpected image shape {image.shape} / dtype {image.dtype}"
    )


def ensure_gray_image(image: np.ndarray) -> np.ndarray:
    """
    Guarantee the returned image is single-channel uint8 grayscale.
    Accepts any shape/dtype variant.
    """
    if image is None:
        raise ValueError("ensure_gray_image received None")

    # Normalise to BGR first, then convert once
    bgr = ensure_bgr_image(image)
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)


def decode_image_safe(
    data: bytes,
    flag: int = cv2.IMREAD_COLOR,
    force_bgr: bool = True,
) -> Optional[np.ndarray]:
    """
    Decode raw bytes (JPEG/PNG/etc.) to an OpenCV image.

    Args:
        data:      Raw file bytes.
        flag:      cv2.IMREAD_* flag.
        force_bgr: When True (default) always returns a 3-channel BGR image
                   regardless of the source format.

    Returns:
        np.ndarray or None on failure.
    """
    nparr = np.frombuffer(data, np.uint8)
    image = cv2.imdecode(nparr, flag)
    if image is None:
        return None
    return ensure_bgr_image(image) if force_bgr else image