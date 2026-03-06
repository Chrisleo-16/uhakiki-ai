#!/usr/bin/env python3
"""
Simple script to run the document OCR model and extract text from an image.
This demonstrates how to process a document and get the extracted text output.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import cv2
import numpy as np
from PIL import Image
import base64

def extract_text_from_image(image_path: str):
    """
    Extract text from an image using the DocumentScanningService.
    
    Args:
        image_path: Path to the image file to process
        
    Returns:
        Dictionary containing extracted text and fields
    """
    from app.services.document_service import DocumentScanningService
    
    # Initialize the service
    service = DocumentScanningService()
    
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image from {image_path}")
        return None
    
    print(f"✅ Loaded image: {image_path}")
    print(f"   Image shape: {image.shape}")
    
    # Preprocess the document
    processed_image = service.preprocess_document(image)
    print("✅ Preprocessed document")
    
    # Extract text using OCR
    text = service.extract_text(processed_image)
    print(f"✅ Extracted text ({len(text)} characters)")
    
    # Detect document type
    doc_type = service.detect_document_type(text)
    print(f"✅ Detected document type: {doc_type}")
    
    # Extract specific fields
    fields = service.extract_document_fields(text, doc_type)
    print(f"✅ Extracted fields: {fields}")
    
    # Analyze quality
    quality = service.analyze_document_quality(image)
    print(f"✅ Quality score: {quality.get('quality_score', 'N/A')}")
    
    # Detect forgery indicators
    forgery = service.detect_forgery_indicators(image, text, doc_type)
    print(f"✅ Risk score: {forgery.get('risk_score', 'N/A')}")
    
    return {
        "document_type": doc_type,
        "extracted_text": text,
        "extracted_fields": fields,
        "quality_analysis": quality,
        "forgery_analysis": forgery
    }


def extract_text_from_base64(base64_string: str):
    """
    Extract text from a base64-encoded image string.
    
    Args:
        base64_string: Base64-encoded image string (with or without data URL prefix)
        
    Returns:
        Dictionary containing extracted text and fields
    """
    from app.services.document_service import DocumentScanningService
    
    # Initialize the service
    service = DocumentScanningService()
    
    # Decode the base64 image
    image = service.decode_base64_image(base64_string)
    if image is None:
        print("Error: Could not decode base64 image")
        return None
    
    print(f"✅ Decoded base64 image")
    print(f"   Image shape: {image.shape}")
    
    # Preprocess the document
    processed_image = service.preprocess_document(image)
    print("✅ Preprocessed document")
    
    # Extract text using OCR
    text = service.extract_text(processed_image)
    print(f"✅ Extracted text ({len(text)} characters)")
    
    # Detect document type
    doc_type = service.detect_document_type(text)
    print(f"✅ Detected document type: {doc_type}")
    
    # Extract specific fields
    fields = service.extract_document_fields(text, doc_type)
    print(f"✅ Extracted fields: {fields}")
    
    return {
        "document_type": doc_type,
        "extracted_text": text,
        "extracted_fields": fields
    }


def process_with_ocr_engine(image_path: str):
    """
    Alternative method using the OCR engine directly.
    
    Args:
        image_path: Path to the image file to process
        
    Returns:
        Dictionary containing extracted ID and raw text
    """
    from app.logic.ocr_engine import OCRModel
    
    # Load image as bytes
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    # Extract and validate
    result = OCRModel.extract_and_validate(image_bytes)
    
    print(f"✅ OCR Engine extracted:")
    print(f"   ID: {result.get('extracted_id')}")
    print(f"   Is Academic: {result.get('is_academic')}")
    print(f"   Raw text length: {len(result.get('raw_text', ''))}")
    
    return result


def main():
    """Main function to demonstrate document text extraction."""
    print("=" * 60)
    print("UHAKIKI AI - Document Text Extraction")
    print("=" * 60)
    
    # Test with a sample image if available
    test_images = [
        "/home/cb-fx/uhakiki-ai/backend/data/forensics/original/IMG_20250924_121136_884~2.jpg",
        "/home/cb-fx/uhakiki-ai/sample_id.jpg",
        "/home/cb-fx/uhakiki-ai/backend/temp_resaved.jpg",
    ]
    
    # Find first available image
    image_path = None
    for path in test_images:
        if os.path.exists(path):
            image_path = path
            break
    
    if image_path:
        print(f"\n📄 Processing: {image_path}")
        print("-" * 60)
        
        # Method 1: Using DocumentScanningService (full pipeline)
        print("\n🔍 Method 1: DocumentScanningService (Full Pipeline)")
        print("-" * 40)
        result1 = extract_text_from_image(image_path)
        
        if result1:
            print("\n📋 Results:")
            print(f"   Document Type: {result1['document_type']}")
            print(f"   Extracted Fields: {result1['extracted_fields']}")
            print(f"\n📄 Full Extracted Text:")
            print("-" * 40)
            print(result1['extracted_text'][:500] if result1['extracted_text'] else "(No text extracted)")
            print("-" * 40)
        
        # Method 2: Using OCR Engine directly
        print("\n🔍 Method 2: OCR Engine (Direct)")
        print("-" * 40)
        result2 = process_with_ocr_engine(image_path)
        
    else:
        print("\n⚠️ No test images found. Please provide an image path.")
        print("\nUsage:")
        print("  python test_extract_text.py <image_path>")
        print("\nExample:")
        print("  python test_extract_text.py /path/to/your/document.jpg")
        
        # Allow passing image path as argument
        if len(sys.argv) > 1:
            image_path = sys.argv[1]
            if os.path.exists(image_path):
                print(f"\n📄 Processing: {image_path}")
                result = extract_text_from_image(image_path)
                if result:
                    print("\n📋 Results:")
                    print(f"   Document Type: {result['document_type']}")
                    print(f"   Extracted Fields: {result['extracted_fields']}")
                    print(f"\n📄 Full Extracted Text:")
                    print("-" * 40)
                    print(result['extracted_text'][:500] if result['extracted_text'] else "(No text extracted)")
            else:
                print(f"Error: File not found: {image_path}")
    
    print("\n" + "=" * 60)
    print("✅ Text extraction complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
