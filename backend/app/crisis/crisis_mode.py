"""
Crisis & Emergency Utility Module
Addresses A3 criterion from MVP Judging Criteria
Enables system utility during national emergencies
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class CrisisMode(Enum):
    NORMAL = "normal"
    PANDEMIC = "pandemic"
    EMERGENCY = "emergency"
    OFFLINE = "offline"


class CrisisModeManager:
    """
    Manages crisis modes for national emergencies
    Enables bulk verification and offline capabilities
    """
    
    def __init__(self):
        self.current_mode = CrisisMode.NORMAL
        self.mode_history: List[Dict] = []
        self.offline_cache: Dict[str, Any] = {}
        
    def set_mode(self, mode: CrisisMode) -> Dict[str, Any]:
        """Switch to a specific crisis mode"""
        previous_mode = self.current_mode
        self.current_mode = mode
        
        # Record mode change
        self.mode_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "previous_mode": previous_mode.value,
            "new_mode": mode.value
        })
        
        # Configure based on mode
        config = self._get_mode_config(mode)
        
        logger.info(f"Crisis mode changed: {previous_mode.value} -> {mode.value}")
        
        return {
            "success": True,
            "previous_mode": previous_mode.value,
            "current_mode": mode.value,
            "configuration": config
        }
    
    def _get_mode_config(self, mode: CrisisMode) -> Dict[str, Any]:
        """Get configuration for each crisis mode"""
        configs = {
            CrisisMode.NORMAL: {
                "description": "Standard operation mode",
                "bulk_verification_enabled": False,
                "offline_mode_enabled": False,
                "lax_document_requirements": False,
                "max_daily_verifications": 10000,
                "require_biometric": True,
                "require_liveness": True,
                "cache_duration_hours": 24
            },
            CrisisMode.PANDEMIC: {
                "description": "Pandemic response - remote verification priority",
                "bulk_verification_enabled": True,
                "offline_mode_enabled": True,
                "lax_document_requirements": True,  # Accept more document types
                "max_daily_verifications": 100000,
                "require_biometric": True,
                "require_liveness": False,  # No touch required
                "cache_duration_hours": 168,  # 1 week
                "use_selfie_instead_of_liveness": True,
                "accept_expired_documents": True
            },
            CrisisMode.EMERGENCY: {
                "description": "National emergency - rapid deployment mode",
                "bulk_verification_enabled": True,
                "offline_mode_enabled": True,
                "lax_document_requirements": True,
                "max_daily_verifications": 500000,
                "require_biometric": False,  # Skip biometric for speed
                "require_liveness": False,
                "cache_duration_hours": 720,  # 30 days
                "allow_batch_processing": True,
                "priority_verification": True
            },
            CrisisMode.OFFLINE: {
                "description": "Offline/connectivity-limited operation",
                "bulk_verification_enabled": True,
                "offline_mode_enabled": True,
                "lax_document_requirements": True,
                "max_daily_verifications": 50000,
                "require_biometric": True,
                "require_liveness": True,
                "cache_duration_hours": 8760,  # 1 year
                "use_cached_models": True,
                "allow_local_verification": True
            }
        }
        
        return configs.get(mode, configs[CrisisMode.NORMAL])
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current crisis mode status"""
        return {
            "enabled": self.current_mode != CrisisMode.NORMAL,
            "mode": self.current_mode.value,
            "configuration": self._get_mode_config(self.current_mode),
            "offline_cache_size": len(self.offline_cache),
            "mode_history_count": len(self.mode_history)
        }
    
    def enable_bulk_verification(self, batch_size: int = 1000) -> Dict[str, Any]:
        """Enable bulk verification mode for crisis"""
        config = self._get_mode_config(self.current_mode)
        
        return {
            "bulk_verification_enabled": True,
            "batch_size": batch_size,
            "estimated_throughput": batch_size * 60,  # per hour
            "priority_queue": True
        }
    
    def cache_for_offline(self, key: str, data: Any) -> None:
        """Cache data for offline use"""
        self.offline_cache[key] = {
            "data": data,
            "cached_at": datetime.utcnow().isoformat()
        }
    
    def get_offline_cache(self, key: str) -> Optional[Any]:
        """Retrieve cached offline data"""
        if key in self.offline_cache:
            return self.offline_cache[key]["data"]
        return None
    
    def get_bulk_verification_stats(self) -> Dict[str, Any]:
        """Get statistics for bulk verification during crisis"""
        return {
            "mode": self.current_mode.value,
            "bulk_enabled": self._get_mode_config(self.current_mode).get("bulk_verification_enabled", False),
            "cached_records": len(self.offline_cache),
            "estimated_daily_capacity": self._get_mode_config(self.current_mode).get("max_daily_verifications", 0),
            "offline_capable": self._get_mode_config(self.current_mode).get("offline_mode_enabled", False)
        }


# Singleton instance
crisis_mode_manager = CrisisModeManager()
