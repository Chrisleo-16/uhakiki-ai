"""
Document Review Service
Handles human review workflow for flagged verifications
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from app.db.milvus_client import search_vault, store_in_vault
from langchain_milvus import Milvus
from langchain_huggingface import HuggingFaceEmbeddings
import os
import uuid

logger = logging.getLogger(__name__)

# Configuration
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
MILVUS_URI = os.getenv("MILVUS_URI", "./sovereign_vault.db")
COLLECTION_NAME = "student_records"

class DocumentReviewService:
    """Service for managing document review workflow"""
    
    def __init__(self):
        self.collection_name = COLLECTION_NAME
        self.milvus_uri = MILVUS_URI
        
    def get_connection(self):
        """Get Milvus connection"""
        try:
            vector_db = Milvus(
                embedding_function=embeddings,
                collection_name=self.collection_name,
                connection_args={"uri": self.milvus_uri}
            )
            return vector_db
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            return None
    
    def get_review_cases(self, status: str = "pending", limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get cases that need human review"""
        try:
            vector_db = self.get_connection()
            if not vector_db:
                return []
            
            # Search for high-risk or flagged cases
            search_query = "high risk fraud flagged verification"
            records = vector_db.similarity_search(search_query, k=100)
            
            # Filter and format for review
            review_cases = []
            for i, record in enumerate(records[offset:offset + limit]):
                metadata = record.metadata
                
                # Only include cases that need review
                risk_score = float(metadata.get('risk_score', 0))
                fraud_flag = metadata.get('fraud_flag', 'False')
                
                if risk_score > 30 or fraud_flag == 'True':
                    review_case = {
                        "id": f"HR-{i + offset + 1:03d}",
                        "student_id": metadata.get('student_id', f"STU-{i + offset:04d}"),
                        "national_id": metadata.get('national_id', f"{123456789 + i}"),
                        "risk_score": risk_score,
                        "priority": self._determine_priority(risk_score),
                        "assigned_to": metadata.get('assigned_to', 'Unassigned'),
                        "created_at": metadata.get('timestamp', datetime.now().isoformat()),
                        "status": status,
                        "notes": self._generate_review_notes(metadata),
                        "tracking_id": metadata.get('tracking_id', f"VR-{i + offset:04d}"),
                        "document_url": metadata.get('document_url', ''),
                        "biometric_url": metadata.get('biometric_url', ''),
                    }
                    
                    review_cases.append(review_case)
            
            # Sort by risk score (highest first)
            review_cases.sort(key=lambda x: x["risk_score"], reverse=True)
            return review_cases[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get review cases: {e}")
            return []
    
    def get_review_case_by_id(self, case_id: str) -> Optional[Dict]:
        """Get specific review case by ID"""
        try:
            # Extract numeric ID from case_id (e.g., "HR-001" -> 1)
            case_number = int(case_id.split('-')[1]) if '-' in case_id else 0
            
            vector_db = self.get_connection()
            if not vector_db:
                return None
            
            search_query = "high risk fraud flagged verification"
            records = vector_db.similarity_search(search_query, k=100)
            
            # Find the specific case
            if case_number <= len(records):
                record = records[case_number - 1]
                metadata = record.metadata
                
                review_case = {
                    "id": case_id,
                    "student_id": metadata.get('student_id', f"STU-{case_number:04d}"),
                    "national_id": metadata.get('national_id', f"{123456789 + case_number}"),
                    "risk_score": float(metadata.get('risk_score', 0)),
                    "priority": self._determine_priority(float(metadata.get('risk_score', 0))),
                    "assigned_to": metadata.get('assigned_to', 'Unassigned'),
                    "created_at": metadata.get('timestamp', datetime.now().isoformat()),
                    "status": metadata.get('review_status', 'pending'),
                    "notes": self._generate_review_notes(metadata),
                    "tracking_id": metadata.get('tracking_id', f"VR-{case_number:04d}"),
                    "document_url": metadata.get('document_url', ''),
                    "biometric_url": metadata.get('biometric_url', ''),
                    "document_analysis": metadata.get('document_analysis', {}),
                    "biometric_analysis": metadata.get('biometric_analysis', {}),
                    "fraud_indicators": metadata.get('fraud_indicators', []),
                }
                
                return review_case
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get review case {case_id}: {e}")
            return None
    
    def update_review_case(self, case_id: str, updates: Dict) -> bool:
        """Update review case with new status, notes, etc."""
        try:
            # Find the case
            case = self.get_review_case_by_id(case_id)
            if not case:
                return False
            
            # Update the record in database
            vector_db = self.get_connection()
            if not vector_db:
                return False
            
            # Create updated record
            updated_content = f"verification record {case['student_id']} {updates.get('status', 'updated')}"
            updated_metadata = {
                **case,
                **updates,
                "updated_at": datetime.now().isoformat(),
                "review_updated": True,
            }
            
            # Store the update
            shard = {
                "content": updated_content,
                "metadata": updated_metadata
            }
            
            success = store_in_vault([shard])
            return success if success else False
            
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
    
    def _determine_priority(self, risk_score: float) -> str:
        """Determine priority based on risk score"""
        if risk_score >= 70:
            return "critical"
        elif risk_score >= 50:
            return "high"
        elif risk_score >= 30:
            return "medium"
        else:
            return "low"
    
    def _generate_review_notes(self, metadata: Dict) -> List[str]:
        """Generate review notes based on metadata"""
        notes = []
        
        risk_score = float(metadata.get('risk_score', 0))
        fraud_flag = metadata.get('fraud_flag', 'False')
        
        if risk_score > 70:
            notes.append("Critical risk score detected")
        elif risk_score > 50:
            notes.append("High risk score detected")
        
        if fraud_flag == 'True':
            notes.append("Fraud flag triggered by automated system")
        
        # Add document analysis notes
        doc_analysis = metadata.get('document_analysis', {})
        if isinstance(doc_analysis, dict):
            forgery_prob = doc_analysis.get('forgery_probability', 0)
            if forgery_prob > 0.3:
                notes.append("High forgery probability detected")
        
        # Add biometric notes
        bio_analysis = metadata.get('biometric_analysis', {})
        if isinstance(bio_analysis, dict):
            if not bio_analysis.get('verified', True):
                notes.append("Biometric verification failed")
        
        if not notes:
            notes.append("Routine review required")
        
        return notes

# Global service instance
review_service = DocumentReviewService()
