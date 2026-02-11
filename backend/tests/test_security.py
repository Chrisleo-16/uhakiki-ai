from app.core.security import encrypt_record, decrypt_record, strip_pii_from_logs

def test_encryption_cycle():
    original = "ID: 12345678"
    encrypted = encrypt_record(original)
    assert encrypted != original
    assert decrypt_record(encrypted) == original

def test_pii_masking():
    raw_log = "Processing student with ID 38445566 and phone 0712345678"
    masked = strip_pii_from_logs(raw_log)
    assert "38445566" not in masked
    assert "********" in masked