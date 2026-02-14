import cv2
import time
import logging
from typing import Optional, Dict, Any
from backend.app.logic.liveness_detector import MBICSystem
from backend.app.core.config import settings  # Recommended: store EAR thresholds here

# --- SOVEREIGN LOGGING (DPA 2019 COMPLIANT) ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [UHAKIKI-VISION] - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VisionGateway:
    """Handles all hardware interactions and input fallbacks."""
    def __init__(self, source: Any = 0):
        self.source = source
        self.cap = None

    def initialize_capture(self) -> bool:
        """Attempts to open the camera using multiple backends."""
        backends = [cv2.CAP_V4L2, cv2.CAP_DSHOW, None]
        for backend in backends:
            try:
                if backend is not None:
                    self.cap = cv2.VideoCapture(self.source, backend)
                else:
                    self.cap = cv2.VideoCapture(self.source)
                
                if self.cap.isOpened():
                    logger.info(f"Connected to vision source {self.source} via {backend}")
                    return True
            except Exception as e:
                continue
        
        logger.error("❌ No physical vision sensors detected.")
        return False

    def get_frame(self):
        if not self.cap: return None, False
        return self.cap.read()

    def release(self):
        if self.cap: self.cap.release()

class SovereignIdentityVerifier:
    """The 'Brain' orchestrator for student verification."""
    def __init__(self):
        self.engine = MBICSystem()
        self.gateway = None
        self.session_id = f"SES-{int(time.time())}"

    def run(self, input_source=0):
        self.gateway = VisionGateway(input_source)
        
        if not self.gateway.initialize_capture():
            print("\n⚠️ HARDWARE ALERT: Camera not found.")
            print(">> Scaling Fallback: Switching to 'Simulation Mode' (provide video file path).")
            # In a production "Water Wheel", this would trigger a system alert
            return

        print(f"🛡️ Uhakiki-AI Sovereign Test Active | Session: {self.session_id}")
        
        while True:
            ret, frame = self.gateway.get_frame()
            if not ret: break

            # 1. Processing Logic
            try:
                # known_encoding would be pulled from the National DB in Phase 4
                result = self.engine.process_mbic_frame(frame, known_encoding=None)
            except Exception as e:
                logger.error(f"Integrity Breach in OODA loop: {e}")
                continue

            # 2. Production-Grade HUD (Head-Up Display)
            self._render_hud(frame, result)

            cv2.imshow("Uhakiki-AI | National Asset Pipeline", frame)

            # 3. Exit Conditions
            if cv2.waitKey(1) & 0xFF == ord('q'): break
            if result.get("status") == "AUTHENTICATED":
                logger.info("✅ Biometric Signature Verified. Access Granted.")
                cv2.waitKey(2000)
                break

        self.gateway.release()
        cv2.destroyAllWindows()

    def _render_hud(self, frame, result):
        """Clean HUD design for high-pressure environments (Konza deployment)."""
        status = result.get("status", "SCANNING")
        color = (0, 255, 0) if status == "AUTHENTICATED" else (0, 165, 255)
        
        # Overlay Identity Box
        cv2.rectangle(frame, (10, 10), (350, 120), (0, 0, 0), -1) # Semi-trans background
        cv2.putText(frame, f"IDENTITY: {status}", (25, 45), 1, 1.5, color, 2)
        cv2.putText(frame, f"CMD: {result.get('message', 'Align Face')}", (25, 85), 1, 1.2, (255, 255, 255), 1)
        
        # Telemetry Data
        if 'blink_count' in result:
            cv2.putText(frame, f"BIO-TELEMETRY: {result['blink_count']} blinks", (25, 110), 1, 0.8, (200, 200, 200), 1)

if __name__ == "__main__":
    verifier = SovereignIdentityVerifier()
    # TIP: To bypass your camera error, change '0' to the path of a video file here:
    verifier.run(input_source=0)