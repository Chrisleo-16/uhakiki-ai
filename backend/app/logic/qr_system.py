import qrcode
import time

def generate_student_qr(national_id):
    # Data is ID + Timestamp to make it 'Dynamic'
    timestamp = int(time.time())
    secure_data = f"UHAKIKI|{national_id}|{timestamp}"
    
    qr = qrcode.make(secure_data)
    qr.save(f"backend/data/qrs/id_{national_id}.png")
    return f"QR Generated for {national_id}"