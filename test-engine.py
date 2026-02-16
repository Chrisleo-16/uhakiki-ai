# This is a self-generate image which we will use it to test our OODA loop first before we get to the real sening of the images
import requests
import numpy as np
from PIL import Image
import io

# 1. GENERATE A SYNTHETIC "DOCUMENT" IMAGE
# We create a 1000x1000 white square to represent a clean document
data = np.full((1000, 1000, 3), 255, dtype=np.uint8)
img = Image.fromarray(data)
img_byte_arr = io.BytesIO()
img.save(img_byte_arr, format='JPEG')
img_byte_arr = img_byte_arr.getvalue()

# 2. SEND TO THE NEURAL ENGINE
url = "http://127.0.0.1:8000/api/v1/secure-ingest"
files = {'document_image': ('test_doc.jpg', img_byte_arr, 'image/jpeg')}
data = {'national_id': 'TEST-999'}

print("🚀 [OODA] Sending synthetic document to Neural Engine...")

try:
    response = requests.post(url, data=data, files=files)
    print(f"📡 [STATUS] {response.status_code}")
    print(f"🧠 [RESULT] {response.json()}")
except Exception as e:
    print(f"❌ [ERROR] Connection failed: {e}")