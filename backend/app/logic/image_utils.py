"""
image_utils.py  —  centralised image normalisation utilities.
Place at:  app/logic/image_utils.py
"""
import cv2
import numpy as np
from typing import Optional


def ensure_bgr_image(image: np.ndarray, source_is_rgb: bool = False) -> np.ndarray:
    if image is None:
        raise ValueError("ensure_bgr_image received None")
    if image.dtype != np.uint8:
        if image.dtype in (np.float32, np.float64):
            image = (image * 255 if image.max() <= 1.0 else image).clip(0, 255).astype(np.uint8)
        else:
            image = image.astype(np.uint8)
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    if image.ndim == 3:
        ch = image.shape[2]
        if ch == 1: return cv2.cvtColor(image[:, :, 0], cv2.COLOR_GRAY2BGR)
        if ch == 3: return cv2.cvtColor(image, cv2.COLOR_RGB2BGR) if source_is_rgb else image
        if ch == 4: return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    raise ValueError(f"ensure_bgr_image: unexpected shape {image.shape} / dtype {image.dtype}")


def ensure_gray_image(image: np.ndarray) -> np.ndarray:
    if image is None:
        raise ValueError("ensure_gray_image received None")
    return cv2.cvtColor(ensure_bgr_image(image), cv2.COLOR_BGR2GRAY)


def decode_image_safe(data: bytes, flag: int = cv2.IMREAD_COLOR,
                      force_bgr: bool = True) -> Optional[np.ndarray]:
    nparr = np.frombuffer(data, np.uint8)
    image = cv2.imdecode(nparr, flag)
    if image is None:
        return None
    return ensure_bgr_image(image) if force_bgr else image