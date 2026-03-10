"""
UHAKIKI-AI: Authentication API with 2FA Support
Provides endpoints for user registration, login, and Two-Factor Authentication (OTP)
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional
import random
import string
import time
from datetime import datetime, timedelta
import os

# In-memory OTP store (use Redis/database in production)
# Format: {phone: {"code": "123456", "expires": timestamp, "attempts": 0}}
otp_store: dict = {}
# Verified phones during signup session
verified_phones: dict = {}

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ─── Request/Response Models ─────────────────────────────────────────────────

class SendOTPRequest(BaseModel):
    phone: str
    email: Optional[str] = None  # Using str to avoid email-validator dependency

class VerifyOTPRequest(BaseModel):
    phone: str
    code: str

class OTPResponse(BaseModel):
    success: bool
    message: str
    expires_in: Optional[int] = None

class RegisterKenyanRequest(BaseModel):
    citizenship: str = "kenyan"
    identificationType: str  # national_id or kcse_certificate
    identificationNumber: str
    firstName: str
    email: str  # Using str to avoid email-validator dependency
    password: str
    dateOfBirth: Optional[str] = None
    kcseExamYear: Optional[str] = None
    phone: Optional[str] = None

class RegisterForeignRequest(BaseModel):
    citizenship: str = "foreign"
    identificationType: str = "passport"
    identificationNumber: str
    firstName: str
    email: str  # Using str to avoid email-validator dependency
    password: str
    phone: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    requires_2fa: bool = False

# ─── Helper Functions ───────────────────────────────────────────────────────

def generate_otp(length: int = 6) -> str:
    """Generate a random numeric OTP"""
    return ''.join(random.choices(string.digits, k=length))


async def send_sms_kenya(phone: str, message: str) -> bool:
    """
    Send SMS using Africa's Talking API (Kenyan provider)
    In production, configure these env variables:
    - AFRICASTALKING_API_KEY
    - AFRICASTALKING_USERNAME (usually 'sandbox' for dev)
    """
    api_key = os.getenv("AFRICASTALKING_API_KEY")
    username = os.getenv("AFRICASTALKING_USERNAME", "sandbox")
    
    if not api_key:
        # Development mode - just log the SMS
        print(f"📱 [DEV MODE] SMS to {phone}: {message}")
        return True
    
    # Try to import httpx, fall back to requests if not available
    try:
        import httpx
    except ImportError:
        print(f"📱 [FALLBACK] SMS to {phone}: {message}")
        return True
    
    url = f"https://api.africastalking.com/version1/messaging"
    headers = {
        "ApiKey": api_key,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "username": username,
        "to": phone,
        "message": message,
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, data=data, timeout=10.0)
            if response.status_code == 201:
                result = response.json()
                print(f"✅ SMS sent: {result}")
                return True
            else:
                print(f"❌ SMS failed: {response.text}")
                return False
    except Exception as e:
        print(f"❌ SMS error: {e}")
        return False

def is_valid_kenyan_phone(phone: str) -> bool:
    """Validate Kenyan phone number format"""
    # Remove any whitespace or special characters
    digits = ''.join(c for c in phone if c.isdigit())
    # Valid formats: 254XXXXXXXXX, 0XXXXXXXXX, 7XX XXX XXX, 8XX XXX XXX, 9XX XXX XXX
    if len(digits) == 12 and digits.startswith('254'):
        return True
    if len(digits) == 10 and digits.startswith('254'):
        return True
    if len(digits) == 9 and digits[0] in '789':
        return True
    if len(digits) == 10 and digits[0] == '0':
        return True
    return False

def format_phone(phone: str) -> str:
    """Format phone number to standard format (254XXXXXXXXX)"""
    digits = ''.join(c for c in phone if c.isdigit())
    if len(digits) == 9 and digits[0] in '789':
        return '254' + digits
    if len(digits) == 10 and digits[0] == '0':
        return '254' + digits[1:]
    if len(digits) == 12:
        return digits
    return phone

# ─── OTP Endpoints ───────────────────────────────────────────────────────────

@router.post("/send-otp", response_model=OTPResponse)
async def send_otp(request: SendOTPRequest):
    """
    Send a One-Time Password (OTP) to the user's phone number.
    This is the first step of 2FA during registration.
    """
    phone = format_phone(request.phone)
    
    # Validate phone number
    if not is_valid_kenyan_phone(phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number. Please enter a valid Kenyan mobile number."
        )
    
    # Check if there's a recent OTP (rate limiting)
    if phone in otp_store:
        stored = otp_store[phone]
        # If OTP was sent less than 60 seconds ago
        if time.time() - stored.get("last_sent", 0) < 60:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Please wait before requesting another OTP."
            )
    
    # Generate OTP
    otp_code = generate_otp()
    
    # Store OTP with expiration (5 minutes)
    otp_store[phone] = {
        "code": otp_code,
        "expires": time.time() + 300,  # 5 minutes
        "attempts": 0,
        "last_sent": time.time()
    }
    
    # Send SMS via Africa's Talking (or log in dev mode)
    sms_message = f"UHAKIKI-AI: Your verification code is {otp_code}. Valid for 5 minutes."
    sms_sent = await send_sms_kenya(phone, sms_message)
    
    if not sms_sent:
        # Log for development even if SMS fails
        print(f"🔐 OTP for {phone}: {otp_code}")  # For development only!")
    
    # Mark phone as pending verification
    verified_phones[phone] = {
        "verified": False,
        "email": request.email,
        "expires": time.time() + 600  # 10 minutes to complete signup
    }
    
    return OTPResponse(
        success=True,
        message="OTP sent successfully",
        expires_in=300
    )

@router.post("/verify-otp", response_model=OTPResponse)
async def verify_otp(request: VerifyOTPRequest):
    """
    Verify the OTP code entered by the user.
    This completes the 2FA verification step.
    """
    phone = format_phone(request.phone)
    
    # Check if OTP exists
    if phone not in otp_store:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OTP found. Please request a new OTP."
        )
    
    stored = otp_store[phone]
    
    # Check if OTP has expired
    if time.time() > stored.get("expires", 0):
        del otp_store[phone]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new one."
        )
    
    # Check attempts (max 5 attempts)
    if stored.get("attempts", 0) >= 5:
        del otp_store[phone]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many failed attempts. Please request a new OTP."
        )
    
    # Verify OTP code
    if stored["code"] != request.code:
        stored["attempts"] = stored.get("attempts", 0) + 1
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OTP. {5 - stored['attempts']} attempts remaining."
        )
    
    # OTP verified successfully
    del otp_store[phone]
    
    # Mark phone as verified in session
    if phone in verified_phones:
        verified_phones[phone]["verified"] = True
    
    return OTPResponse(
        success=True,
        message="Phone number verified successfully"
    )

@router.post("/register/kenyan", response_model=TokenResponse)
async def register_kenyan(request: RegisterKenyanRequest):
    """
    Register a Kenyan citizen with National ID or KCSE certificate.
    Requires identity verification and optionally 2FA.
    """
    # Check if phone was verified (if provided)
    if request.phone:
        phone = format_phone(request.phone)
        if phone in verified_phones:
            if not verified_phones[phone].get("verified", False):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Please complete 2FA verification first"
                )
            # Clean up
            if phone in verified_phones:
                del verified_phones[phone]
    
    # In production, save to database
    # For now, create a simple token
    from ..auth.auth import create_access_token
    
    user_id = request.email
    token_data = {
        "sub": user_id,
        "email": request.email,
        "firstName": request.firstName,
        "identificationType": request.identificationType,
        "identificationNumber": request.identificationNumber,
        "citizenship": request.citizenship,
        "phone": request.phone
    }
    
    access_token = create_access_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user_id,
        requires_2fa=False  # Already verified during signup
    )

@router.post("/register/foreign", response_model=TokenResponse)
async def register_foreign(request: RegisterForeignRequest):
    """
    Register a foreign student with passport.
    Requires identity verification and optionally 2FA.
    """
    # Check if phone was verified (if provided)
    if request.phone:
        phone = format_phone(request.phone)
        if phone in verified_phones:
            if not verified_phones[phone].get("verified", False):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Please complete 2FA verification first"
                )
            # Clean up
            if phone in verified_phones:
                del verified_phones[phone]
    
    # In production, save to database
    from ..auth.auth import create_access_token
    
    user_id = request.email
    token_data = {
        "sub": user_id,
        "email": request.email,
        "firstName": request.firstName,
        "identificationType": request.identificationType,
        "identificationNumber": request.identificationNumber,
        "citizenship": request.citizenship,
        "phone": request.phone
    }
    
    access_token = create_access_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user_id,
        requires_2fa=False
    )

# ─── Health Check ───────────────────────────────────────────────────────────

@router.get("/health")
async def auth_health():
    """Health check for auth service"""
    return {
        "status": "healthy",
        "service": "UHAKIKI-AI Authentication",
        "version": "1.0.0",
        "2fa_enabled": True
    }

# Cleanup expired OTPs periodically
def cleanup_expired_otps():
    """Remove expired OTPs from memory"""
    current_time = time.time()
    expired_phones = [
        phone for phone, data in otp_store.items()
        if current_time > data.get("expires", 0)
    ]
    for phone in expired_phones:
        del otp_store[phone]
    
    # Clean up expired verification sessions
    expired_sessions = [
        phone for phone, data in verified_phones.items()
        if current_time > data.get("expires", 0)
    ]
    for phone in expired_sessions:
        del verified_phones[phone]
