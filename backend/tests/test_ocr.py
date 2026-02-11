import pytest
from app.logic.ocr_engine import OCRModel

def test_ocr_extraction():
    # Load a sample image bytes (you can use a real small image file here)
    with open("tests/sample_id.jpg", "rb") as f:
        content = f.read()
    
    results = OCRModel.extract_and_validate(content)
    assert "extracted_id" in results
    assert results["extracted_id"] is not None # If it's a valid ID image