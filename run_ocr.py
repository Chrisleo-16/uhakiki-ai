#!/usr/bin/env python3
"""
Simple OCR text extraction for documents.
This version aggressively extracts ID and fields from noisy OCR output.
"""

import sys
import os
import cv2
import re
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def extract_fields_from_image(image_path: str):
    """
    Extract document fields from image using OCR.
    Uses aggressive pattern matching to handle noisy OCR output.
    """
    import pytesseract
    from PIL import Image
    
    print(f"📄 Processing: {image_path}")
    print("-" * 60)
    
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Error: Could not load image")
        return
    
    print(f"✅ Image loaded: {img.shape}")
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply denoising
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    
    # Apply CLAHE for contrast
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    enhanced = clahe.apply(denoised)
    
    # Apply thresholding
    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Try multiple OCR configurations
    all_text = ""
    
    # First try on the enhanced (non-thresholded) image
    for config in ['--oem 3 --psm 6 -l eng', '--oem 3 --psm 3 -l eng', '--oem 3 --psm 11 -l eng', '--oem 3 --psm 4 -l eng']:
        try:
            text = pytesseract.image_to_string(enhanced, config=config)
            if len(text) > len(all_text):
                all_text = text
        except:
            pass
    
    # Also try on the thresholded image
    for config in ['--oem 3 --psm 6 -l eng', '--oem 3 --psm 3 -l eng']:
        try:
            text = pytesseract.image_to_string(thresh, config=config)
            if len(text) > len(all_text):
                all_text = text
        except:
            pass
    
    # Clean the text
    lines = all_text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)
    text_clean = '\n'.join(cleaned_lines)
    text_upper = text_clean.upper()
    
    print(f"✅ OCR completed ({len(text_clean)} chars)")
    
    # Initialize fields
    fields = {
        "name": "Unknown",
        "id_number": "N/A",
        "date_of_birth": "N/A",
        "gender": "N/A",
        "issuing_county": "N/A",
        "place_of_birth": "N/A",
        "expiry_date": "N/A"
    }
    
    # --- Extract ID Number ---
    # Look for any 6-9 digit numbers that could be IDs
    all_numbers = re.findall(r'\b\d{6,9}\b', text_clean)
    
    # Also look for numbers that might have OCR errors (like 16260 or 39304)
    # Try to find 8-digit sequences even with spaces or OCR errors
    fragmented_ids = re.findall(r'\b\d{4,9}\b', text_clean.replace(' ', ''))
    all_numbers.extend(fragmented_ids)
    
    # Filter out likely non-IDs (years, dates)
    valid_ids = []
    for num in all_numbers:
        # Skip if starts with year-like number
        if num[:4].isdigit() and 1900 <= int(num[:4]) <= 2100:
            continue
        # Skip if it looks like a phone number (starts with 07)
        if num.startswith('07') and len(num) == 10:
            continue
        # Skip if shorter than 6 digits
        if len(num) < 6:
            continue
        valid_ids.append(num)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_ids = []
    for x in valid_ids:
        if x not in seen:
            seen.add(x)
            unique_ids.append(x)
    valid_ids = unique_ids
    
    print(f"📊 Found potential IDs: {valid_ids[:5]}")
    
    # Also look for patterns near ID keyword
    id_patterns = [
        r'ID[:\s]*(\d{6,9})',
        r'NO[:\s]*(\d{6,9})',
        r'NUMBER[:\s]*(\d{6,9})',
    ]
    for pattern in id_patterns:
        match = re.search(pattern, text_clean, re.IGNORECASE)
        if match:
            valid_ids.insert(0, match.group(1))
            break
    
    # Use the first valid ID
    if valid_ids:
        fields["id_number"] = valid_ids[0]
        print(f"✅ Found ID: {valid_ids[0]}")
    
    # --- Extract Name ---
    # Look for the name - usually in uppercase, not in skip words
    skip_words = ['REPUBLIC', 'KENYA', 'NATIONAL', 'IDENTITY', 'CARD', 'DATE', 'BIRTH', 
                 'SEX', 'GENDER', 'PLACE', 'EXPIRY', 'COUNTY', 'ISSUING', 'JAMHURIYA', 
                 'TAIFA', 'ATAMBULISHO', 'AUTHORITY']
    
    name_candidates = []
    for line in lines:
        line = line.strip()
        # Skip short lines
        if len(line) < 3:
            continue
        # Skip lines with too many numbers
        if sum(c.isdigit() for c in line) > len(line) * 0.3:
            continue
        # Skip common keywords
        line_upper = line.upper()
        if any(word in line_upper for word in skip_words):
            continue
        # Clean the line
        clean = re.sub(r'[^a-zA-Z\s]', '', line)
        if len(clean) >= 3 and len(clean) <= 50:
            name_candidates.append(clean.title())
    
    if name_candidates:
        fields["name"] = name_candidates[0]
        print(f"✅ Found Name: {name_candidates[0]}")
    
    # --- Extract Date of Birth ---
    dob_patterns = [
        r'DATE.*?(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})',
        r'DOB[:\s]*(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})',
        r'(\d{1,2}[/.-]\d{1,2}[/.-]\d{4})',
    ]
    for pattern in dob_patterns:
        match = re.search(pattern, text_clean, re.IGNORECASE)
        if match:
            fields["date_of_birth"] = match.group(1)
            print(f"✅ Found DOB: {match.group(1)}")
            break
    
    # --- Extract Gender ---
    if "MALE" in text_upper:
        fields["gender"] = "Male"
        print(f"✅ Found Gender: Male")
    elif "FEMALE" in text_upper:
        fields["gender"] = "Female"
        print(f"✅ Found Gender: Female")
    
    # --- Extract Issuing County ---
    county_match = re.search(r'COUNTY[:\s]*([A-Za-z]+)', text_clean, re.IGNORECASE)
    if county_match:
        fields["issuing_county"] = county_match.group(1).strip().title()
        print(f"✅ Found County: {fields['issuing_county']}")
    
    # --- Extract Place of Birth ---
    pob_match = re.search(r'PLACE[:\s]*([A-Za-z]+(?:\s+[A-Za-z]+)?)', text_clean, re.IGNORECASE)
    if pob_match:
        fields["place_of_birth"] = pob_match.group(1).strip().title()
        print(f"✅ Found POB: {fields['place_of_birth']}")
    
    # --- Extract Expiry Date ---
    expiry_patterns = [
        r'EXPIRY[:\s]*(\d{4}-\d{2}-\d{2})',
        r'EXPIRES[:\s]*(\d{4}-\d{2}-\d{2})',
        r'VALID UNTIL[:\s]*(\d{4}-\d{2}-\d{2})',
    ]
    for pattern in expiry_patterns:
        match = re.search(pattern, text_clean, re.IGNORECASE)
        if match:
            fields["expiry_date"] = match.group(1)
            print(f"✅ Found Expiry: {fields['expiry_date']}")
            break
    
    # Print results
    print("\n" + "=" * 60)
    print("📋 EXTRACTED FIELDS:")
    print("=" * 60)
    print(f"Name:            {fields['name']}")
    print(f"ID Number:       {fields['id_number']}")
    print(f"Date of Birth:   {fields['date_of_birth']}")
    print(f"Gender:          {fields['gender']}")
    print(f"Issuing County:  {fields['issuing_county']}")
    print(f"Place of Birth:  {fields['place_of_birth']}")
    print(f"Expiry Date:     {fields['expiry_date']}")
    print("=" * 60)
    
    # Show some extracted text
    print("\n📄 SAMPLE EXTRACTED TEXT:")
    print("-" * 60)
    for i, line in enumerate(lines[:30]):  # Show first 30 lines
        line = line.strip()
        if line and len(line) > 2:
            print(line)
    print("-" * 60)
    
    return fields


def main():
    print("=" * 60)
    print("UHAKIKI AI - Document Field Extraction")
    print("=" * 60)
    
    # Default test image
    test_images = [
        "/home/cb-fx/uhakiki-ai/backend/data/forensics/original/IMG_20250924_121136_884~2.jpg",
        "/home/cb-fx/uhakiki-ai/sample_id.jpg",
    ]
    
    # Find first available
    image_path = None
    for path in test_images:
        if os.path.exists(path):
            image_path = path
            break
    
    # Or use command line argument
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    
    if not image_path:
        print("Usage: python run_ocr.py <image_path>")
        return
    
    result = extract_fields_from_image(image_path)
    
    print("\n✅ Extraction complete!")
    return result


if __name__ == "__main__":
    main()
