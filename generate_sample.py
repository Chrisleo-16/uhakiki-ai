import cv2
import numpy as np

def create_synthetic_id(output_path="sample_id.jpg"):
    # Create a blank 'ID Card' (Standard ID-1 size ratio: 1012x638)
    id_card = np.ones((638, 1012, 3), dtype=np.uint8) * 255
    
    # Add a 'Sovereign' Header
    cv2.rectangle(id_card, (0, 0), (1012, 100), (0, 100, 0), -1) # Green Header
    cv2.putText(id_card, "REPUBLIC OF KENYA - IDENTITY", (250, 65), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)

    # Add a 'Photo' Placeholder
    cv2.rectangle(id_card, (50, 150), (350, 550), (200, 200, 200), -1)
    cv2.putText(id_card, "PHOTO", (140, 360), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 2)

    # Add Fake National ID Data for the OCR
    cv2.putText(id_card, "ID NUMBER: 12345678", (400, 250), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(id_card, "NAME: TEST SUBJECT", (400, 350), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(id_card, "EXPIRY: 2030-01-01", (400, 450), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

    # Save the file
    cv2.imwrite(output_path, id_card)
    print(f"✅ Sample ID generated at: {output_path}")

if __name__ == "__main__":
    create_synthetic_id()