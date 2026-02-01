import cv2

def is_high_quality(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    # Check if the document is sharp enough for our OODA loop
    variance = cv2.Laplacian(img, cv2.CV_64F).var()
    return variance > 100