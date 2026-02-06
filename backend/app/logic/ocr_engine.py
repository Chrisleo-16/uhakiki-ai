import cv2
import pytesseract
import re
import numpy as np

class OCRModel:
    @staticmethod
    def extract_and_validate(image_content: bytes):
        # 1. Decode bytes to OpenCV
        nparr = np.frombuffer(image_content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # 2. Pre-process for Tesseract (Grayscale + Threshold)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        
        # 3. OCR Extraction
        text = pytesseract.image_to_string(thresh).upper()
        
        # 4. Regex for Kenyan ID/Index Number (8-10 digits)
        id_pattern = r'\b\d{8,10}\b'
        match = re.search(id_pattern, text)
        extracted_id = match.group(0) if match else None
        
        return {
            "extracted_id": extracted_id,
            "raw_text": text,
            "is_academic": "CERTIFICATE" in text or "EXAMINATION" in text
        }