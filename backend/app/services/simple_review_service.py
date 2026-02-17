"""
Simplified Review Service
Handles human review workflow without external dependencies
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import uuid

logger = logging.getLogger(__name__)

class SimpleReviewService:
    """Simplified review service for demonstration"""
    
    def __init__(self):
        # Mock data for demonstration
        self.mock_cases = [
            {
                "id": "HR-001",
                "student_id": "STU-2024-0892",
                "national_id": "3456789012",
                "risk_score": 78.5,
                "priority": "critical",
                "assigned_to": "Officer K. Mwangi",
                "created_at": "2024-06-15T09:30:00Z",
                "status": "pending",
                "notes": ["High-risk document anomalies detected", "Biometric mismatch indicators", "Multiple application attempts"],
                "tracking_id": "VR-2024-0892",
                "document_url": "",
                "biometric_url": "",
            },
            {
                "id": "HR-002", 
                "student_id": "STU-2024-1034",
                "national_id": "23456789012",
                "risk_score": 62.3,
                "priority": "high",
                "assigned_to": "",
                "created_at": "2024-06-15T10:45:00Z",
                "status": "pending",
                "notes": ["Suspicious geographic patterns", "Inconsistent external data"],
                "tracking_id": "VR-2024-1034",
                "document_url": "",
                "biometric_url": "",
            },
            {
                "id": "HR-003",
                "student_id": "STU-2024-0765", 
                "national_id": "123456789012",
                "risk_score": 45.7,
                "priority": "medium",
                "assigned_to": "Officer A. Otieno",
                "created_at": "2024-06-15T11:20:00Z",
                "status": "pending",
                "notes": ["Minor document inconsistencies", "Requires manual verification"],
                "tracking_id": "VR-2024-0765",
                "document_url": "",
                "biometric_url": "",
            }
        ]
        
    def get_review_cases(self, status: str = "pending", limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get cases that need human review"""
        try:
            # Filter by status
            filtered_cases = [case for case in self.mock_cases if case.get("status") == status]
            
            # Apply pagination
            paginated_cases = filtered_cases[offset:offset + limit]
            
            return paginated_cases
        except Exception as e:
            logger.error(f"Failed to get review cases: {e}")
            return []
    
    def get_review_case_by_id(self, case_id: str) -> Optional[Dict]:
        """Get specific review case by ID"""
        try:
            for case in self.mock_cases:
                if case.get("id") == case_id:
                    return case
            return None
        except Exception as e:
            logger.error(f"Failed to get review case {case_id}: {e}")
            return None
    
    def update_review_case(self, case_id: str, updates: Dict) -> bool:
        """Update review case with new status, notes, etc."""
        try:
            for case in self.mock_cases:
                if case.get("id") == case_id:
                    case.update(updates)
                    case["updated_at"] = datetime.now().isoformat()
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to update review case {case_id}: {e}")
            return False
    
    def assign_case(self, case_id: str, officer_name: str) -> bool:
        """Assign a case to a review officer"""
        return self.update_review_case(case_id, {
            "assigned_to": officer_name,
            "status": "assigned"
        })
    
    def complete_review(self, case_id: str, verdict: str, notes: List[str]) -> bool:
        """Complete a review with verdict and notes"""
        return self.update_review_case(case_id, {
            "status": "completed",
            "review_verdict": verdict,
            "review_notes": notes,
            "completed_at": datetime.now().isoformat()
        })
    
    def get_review_stats(self) -> Dict:
        """Get review workflow statistics"""
        try:
            pending = len([c for c in self.mock_cases if c.get("status") == "pending"])
            assigned = len([c for c in self.mock_cases if c.get("status") == "assigned"])
            completed = len([c for c in self.mock_cases if c.get("status") == "completed"])
            
            return {
                "pending_cases": pending,
                "assigned_cases": assigned,
                "completed_cases": completed,
                "total_cases": len(self.mock_cases),
                "critical_priority": len([c for c in self.mock_cases if c.get("priority") == "critical"]),
                "high_priority": len([c for c in self.mock_cases if c.get("priority") == "high"]),
                "average_review_time": "2.5 hours"
            }
        except Exception as e:
            logger.error(f"Failed to get review stats: {e}")
            return {
                "pending_cases": 0,
                "assigned_cases": 0,
                "completed_cases": 0,
                "total_cases": 0,
                "critical_priority": 0,
                "high_priority": 0,
                "average_review_time": "0 hours"
            }

# Global service instance
simple_review_service = SimpleReviewService()
