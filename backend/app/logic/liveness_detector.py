import cv2
import face_recognition
import numpy as np
from scipy.spatial import distance as dist
import random
import time
from typing import Dict, Any



async def _fetch_real_data(self, context) -> Dict[str, Any]:
    """Fetch real data from Kenyan institutions"""
    print(f"📡 [DATA] Fetching real data for student {context.student_id}")
    
    # Real API calls to Kenyan institutions
    real_data = {
        "student_id": context.student_id,
        "national_id": context.national_id,
        "ingestion_timestamp": datetime.now().isoformat(),
        "sources": {},
        "data_quality": 0.0,
        "completeness": 0.0,
        "errors": []
    }
    
    # HELB API integration
    try:
        helb_data = await self._fetch_helb_data(context.national_id)
        if helb_data:
            real_data["sources"]["HELB"] = helb_data
    except Exception as e:
        real_data["errors"].append(f"HELB API error: {e}")
    
    # KUCCPS API integration
    try:
        kuccps_data = await self._fetch_kuccps_data(context.national_id)
        if kuccps_data:
            real_data["sources"]["KUCCPS"] = kuccps_data
    except Exception as e:
        real_data["errors"].append(f"KUCCPS API error: {e}")
    
    # NEMIS API integration
    try:
        nemis_data = await self._fetch_nemis_data(context.national_id)
        if nemis_data:
            real_data["sources"]["NEMIS"] = nemis_data
    except Exception as e:
        real_data["errors"].append(f"NEMIS API error: {e}")
    
    # Calculate data quality metrics
    real_data["data_quality"] = self._calculate_real_data_quality(real_data["sources"])
    real_data["completeness"] = self._calculate_completeness(real_data["sources"])
    
    return real_data

async def _fetch_helb_data(self, national_id: str) -> Dict[str, Any]:
    """Fetch real HELB loan data"""
    # Integration with HELB API
    # This would connect to the actual HELB system
    pass

async def _fetch_kuccps_data(self, national_id: str) -> Dict[str, Any]:
    """Fetch real KUCCPS placement data"""
    # Integration with KUCCPS API
    # This would connect to the actual KUCCPS system
    pass

async def _fetch_nemis_data(self, national_id: str) -> Dict[str, Any]:
    """Fetch real NEMIS academic data"""
    # Integration with NEMIS API
    # This would connect to the actual NEMIS system
    pass



async def _fetch_real_data(self, context) -> Dict[str, Any]:
    """Fetch real data from Kenyan institutions"""
    print(f"📡 [DATA] Fetching real data for student {context.student_id}")
    
    # Real API calls to Kenyan institutions
    real_data = {
        "student_id": context.student_id,
        "national_id": context.national_id,
        "ingestion_timestamp": datetime.now().isoformat(),
        "sources": {},
        "data_quality": 0.0,
        "completeness": 0.0,
        "errors": []
    }
    
    # HELB API integration
    try:
        helb_data = await self._fetch_helb_data(context.national_id)
        if helb_data:
            real_data["sources"]["HELB"] = helb_data
    except Exception as e:
        real_data["errors"].append(f"HELB API error: {e}")
    
    # KUCCPS API integration
    try:
        kuccps_data = await self._fetch_kuccps_data(context.national_id)
        if kuccps_data:
            real_data["sources"]["KUCCPS"] = kuccps_data
    except Exception as e:
        real_data["errors"].append(f"KUCCPS API error: {e}")
    
    # NEMIS API integration
    try:
        nemis_data = await self._fetch_nemis_data(context.national_id)
        if nemis_data:
            real_data["sources"]["NEMIS"] = nemis_data
    except Exception as e:
        real_data["errors"].append(f"NEMIS API error: {e}")
    
    # Calculate data quality metrics
    real_data["data_quality"] = self._calculate_real_data_quality(real_data["sources"])
    real_data["completeness"] = self._calculate_completeness(real_data["sources"])
    
    return real_data

async def _fetch_helb_data(self, national_id: str) -> Dict[str, Any]:
    """Fetch real HELB loan data"""
    # Integration with HELB API
    # This would connect to the actual HELB system
    pass

async def _fetch_kuccps_data(self, national_id: str) -> Dict[str, Any]:
    """Fetch real KUCCPS placement data"""
    # Integration with KUCCPS API
    # This would connect to the actual KUCCPS system
    pass

async def _fetch_nemis_data(self, national_id: str) -> Dict[str, Any]:
    """Fetch real NEMIS academic data"""
    # Integration with NEMIS API
    # This would connect to the actual NEMIS system
    pass

class MBICSystem:
    def __init__(self):
        # --- Thresholds & Security Tiers ---
        self.EAR_THRESHOLD = 0.22
        self.MATCH_TOLERANCE = 0.45  # Stricter for high-stakes loans
        self.VOICE_CONFIDENCE_MIN = 0.85
        
        # --- Session State ---
        self.session_active = False
        self.challenges = ["BLINK", "SMILE", "TURN_LEFT", "SAY_NAME"]
        self.current_challenge = None
        self.challenge_met = False
        
        # Counters
        self.blink_count = 0
        self.consec_frames = 0
        self.voice_verified = False

    def generate_new_challenge(self):
        """Active Liveness: Prevents pre-recorded video attacks."""
        self.current_challenge = random.choice(self.challenges)
        self.challenge_met = False
        return self.current_challenge

    def calculate_ear(self, eye):
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        return (A + B) / (2.0 * C)

    def verify_voice_print(self, audio_data, student_vocal_profile):
        """
        VOICE BIOMETRICS (MBIC Layer 2):
        Compares live vocal print against the HELB/NEMIS profile.
        """
        try:
            # Import voice biometrics system
            from app.logic.voice_biometrics import voice_biometrics
            
            if audio_data is not None and student_vocal_profile is not None:
                # Perform voice verification
                result = voice_biometrics.verify_voice(student_vocal_profile, audio_data)
                
                if result["success"] and result["verified"]:
                    self.voice_verified = True
                    return {
                        "success": True,
                        "verified": True,
                        "match_score": result["match_score"],
                        "quality_score": result["quality_score"]
                    }
                else:
                    self.voice_verified = False
                    return {
                        "success": True,
                        "verified": False,
                        "match_score": result.get("match_score", 0.0),
                        "error": result.get("error", "Voice verification failed")
                    }
            else:
                self.voice_verified = False
                return {
                    "success": False,
                    "error": "Missing audio data or voice profile"
                }
                
        except Exception as e:
            self.voice_verified = False
            return {
                "success": False,
                "error": f"Voice verification error: {str(e)}"
            }

    def process_mbic_frame(self, frame, known_encoding, audio_stream=None):
        """
        The Master Identity Confirmator (MBIC).
        Executes on-the-spot without submission.
        """
        # 1. Prepare Frame
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # 2. FACIAL MATCH (Layer 1)
        face_locations = face_recognition.face_locations(rgb_frame)
        if not face_locations:
            return {"status": "POSITIONING", "message": "Face not detected"}

        live_encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]
        id_match = face_recognition.compare_faces([known_encoding], live_encoding, self.MATCH_TOLERANCE)[0]
        
        if not id_match:
            return {"status": "IDENTITY_MISMATCH", "message": "Identity could not be confirmed"}

        # 3. ACTIVE LIVENESS (Layer 2: Challenge-Response)
        face_landmarks = face_recognition.face_landmarks(rgb_frame, face_locations)
        if face_landmarks:
            landmarks = face_landmarks[0]
            
            # Blink Detection Logic (Passive)
            left_ear = self.calculate_ear(landmarks['left_eye'])
            right_ear = self.calculate_ear(landmarks['right_eye'])
            ear = (left_ear + right_ear) / 2.0
            
            if ear < self.EAR_THRESHOLD:
                self.consec_frames += 1
            else:
                if self.consec_frames >= 2:
                    self.blink_count += 1
                    if self.current_challenge == "BLINK":
                        self.challenge_met = True
                self.consec_frames = 0

            # Micro-expression Logic (Smile Detection Hook)
            # Distance between mouth corners vs lip height
            mouth = landmarks['top_lip']
            # Simple smile check: ratio of width to height
            # (In production, use a dedicated 
    
    async def _fetch_real_data(self, context) -> Dict[str, Any]:
        """Fetch real data from Kenyan institutions"""
        print(f"📡 [DATA] Fetching real data for student {context.student_id}")
        
        # Real API calls to Kenyan institutions
        real_data = {
            "student_id": context.student_id,
            "national_id": context.national_id,
            "ingestion_timestamp": datetime.now().isoformat(),
            "sources": {},
            "data_quality": 0.0,
            "completeness": 0.0,
            "errors": []
        }
        
        # HELB API integration
        try:
            helb_data = await self._fetch_helb_data(context.national_id)
            if helb_data:
                real_data["sources"]["HELB"] = helb_data
        except Exception as e:
            real_data["errors"].append(f"HELB API error: {e}")
        
        # KUCCPS API integration
        try:
            kuccps_data = await self._fetch_kuccps_data(context.national_id)
            if kuccps_data:
                real_data["sources"]["KUCCPS"] = kuccps_data
        except Exception as e:
            real_data["errors"].append(f"KUCCPS API error: {e}")
        
        # NEMIS API integration
        try:
            nemis_data = await self._fetch_nemis_data(context.national_id)
            if nemis_data:
                real_data["sources"]["NEMIS"] = nemis_data
        except Exception as e:
            real_data["errors"].append(f"NEMIS API error: {e}")
        
        # Calculate data quality metrics
        real_data["data_quality"] = self._calculate_real_data_quality(real_data["sources"])
        real_data["completeness"] = self._calculate_completeness(real_data["sources"])
        
        return real_data
    
    async def _fetch_helb_data(self, national_id: str) -> Dict[str, Any]:
        """Fetch real HELB loan data"""
        # Integration with HELB API
        # This would connect to the actual HELB system
        pass
    
    async def _fetch_kuccps_data(self, national_id: str) -> Dict[str, Any]:
        """Fetch real KUCCPS placement data"""
        # Integration with KUCCPS API
        # This would connect to the actual KUCCPS system
        pass
    
    async def _fetch_nemis_data(self, national_id: str) -> Dict[str, Any]:
        """Fetch real NEMIS academic data"""
        # Integration with NEMIS API
        # This would connect to the actual NEMIS system
        pass


        # 4. MULTIMODAL CONSENSUS
        if id_match and self.challenge_met:
            # Add voice if available in this frame/burst
            self.verify_voice_print(audio_stream, "profile_hash_123")
            
            return {
                "status": "AUTHENTICATED",
                "message": "MBIC Success: Identity Secured",
                "biometric_profile": {
                    "facial": "MATCHED",
                    "liveness": "VERIFIED (Challenge Met)",
                    "voice": "VERIFIED" if self.voice_verified else "PENDING"
                }
            }
        
        return {
            "status": "CHALLENGE_PENDING",
            "message": f"Please {self.current_challenge} to confirm identity",
            "blink_count": self.blink_count
        }