import qrcode
import hashlib
import time
import os

def generate_student_qr(national_id):
    """Generates a secure, hashed Dynamic QR for the Konza Vault."""
    
    # 1. Create a Sovereign Hash (SHA-256)
    # We add a salt or timestamp to ensure the QR is 'Dynamic'
    timestamp = str(int(time.time()))
    raw_data = f"{national_id}|{timestamp}|KNDC-UHAKIKI"
    secure_hash = hashlib.sha256(raw_data.encode()).hexdigest()
    
    # 2. Configure the QR (Professional Grade)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H, # High error correction
        box_size=10,
        border=4,
    )
    
    # The QR only points to the secure hash in our Milvus Vault
    qr.add_data(f"https://verify.konza.go.ke/v/{secure_hash[:16]}")
    qr.make(fit=True)

    # 3. Save to the persistent directory
    save_path = f"backend/data/qrs/id_{national_id}.png"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(save_path)
    
    return {
        "status": "QR_GENERATED",
        "hash": secure_hash,
        "path": save_path
    }