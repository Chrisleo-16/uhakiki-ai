"""
UhakikiAI - Sovereign Identity Engine
Phase 2.0: Agentic Intelligence with OODA Loop Architecture

A comprehensive document verification and fraud detection system designed for
Kenyan Higher Education funding protection.

Core Components:
- RAD Autoencoder: Document reconstruction anomaly detection
- Security Council: Autonomous agent orchestration
- Milvus Vault: Sovereign identity storage
- DPIA Compliance: DPA 2019 Section 31 compliance
- Real-time Analytics: Executive dashboard integration
"""

__version__ = "2.0.0"
__author__ = "UhakikiAI Development Team"
__description__ = "Sovereign Identity Engine for Kenyan Education"

# Import core modules with error handling
try:
    from .logic.council import SecurityCouncil
    _council_available = True
except ImportError:
    _council_available = False
    SecurityCouncil = None

try:
    from .logic.forgery_detector import detect_pixel_anomalies
    _forgery_detector_available = True
except ImportError:
    _forgery_detector_available = False
    detect_pixel_anomalies = None

try:
    from .models.model_loader import model_manager
    _model_manager_available = True
except ImportError:
    _model_manager_available = False
    model_manager = None

try:
    from .compliance.dpia_audit import dpia_manager
    _compliance_available = True
except ImportError:
    _compliance_available = False
    dpia_manager = None

__all__ = [
    "SecurityCouncil",
    "detect_pixel_anomalies", 
    "model_manager",
    "dpia_manager"
]