"""
Simplified Document Service
Handles document upload and processing without external dependencies
"""

from datetime import datetime
from typing import Dict, List, Optional
import logging
import random

logger = logging.getLogger(__name__)

class SimpleDocumentService:
    """Simplified document service for demonstration"""
    
    def __init__(self):
        self.supported_types = {
            "national_id": {
                "name": "Kenyan National ID Card",
                "required_fields": ["id_number", "name", "date_of_birth"],
                "supported_formats": ["jpg", "jpeg", "png"],
                "min_quality_score": 0.6
            },
            "passport": {
                "name": "Kenyan Passport",
                "required_fields": ["passport_number", "name", "nationality"],
                "supported_formats": ["jpg", "jpeg", "png"],
                "min_quality_score": 0.7
            }
        }
    
    def process_document(self, base64_image: str, expected_type: Optional[str] = None) -> Dict:
        """Complete document processing pipeline (simplified)"""
        try:
            # Simulate document processing
            doc_type = expected_type or self._detect_document_type()
            quality_score = random.uniform(0.5, 0.95)
            risk_score = random.uniform(0.1, 0.8)
            
            # Extract fields (simulated)
            extracted_fields = self._extract_mock_fields(doc_type)
            
            # Quality analysis
            quality_analysis = {
                "sharpness": random.uniform(0.6, 0.95),
                "noise_level": random.uniform(0.05, 0.25),
                "brightness": random.uniform(0.4, 0.8),
                "contrast": random.uniform(0.5, 0.9),
                "edge_density": random.uniform(0.08, 0.2),
                "color_variance": random.uniform(100, 200),
                "quality_score": quality_score,
                "is_acceptable": quality_score > 0.6
            }
            
            # Forgery analysis
            forgery_indicators = []
            if risk_score > 0.6:
                forgery_indicators.append("High risk patterns detected")
            if quality_score < 0.5:
                forgery_indicators.append("Poor image quality")
            if not extracted_fields.get("id_number"):
                forgery_indicators.append("Missing required fields")
            
            forgery_analysis = {
                "indicators": forgery_indicators,
                "risk_score": risk_score,
                "risk_level": self._determine_risk_level(risk_score),
                "quality_analysis": quality_analysis,
                "text_length": len(str(extracted_fields)),
                "document_type": doc_type
            }
            
            # Overall assessment
            overall_score = (quality_score * 0.4) + ((1 - risk_score) * 0.6)
            
            return {
                "success": True,
                "document_type": doc_type,
                "extracted_fields": extracted_fields,
                "quality_analysis": quality_analysis,
                "forgery_analysis": forgery_analysis,
                "overall_score": overall_score,
                "verification_status": "PASS" if overall_score > 0.7 else "REQUIRES_REVIEW" if overall_score > 0.4 else "FAIL",
                "extracted_text": f"Extracted text from {doc_type} document...",
                "processing_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Document processing error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _detect_document_type(self) -> str:
        """Detect document type (simplified)"""
        return random.choice(["national_id", "passport"])
    
    def _extract_mock_fields(self, doc_type: str) -> Dict:
        """Extract mock fields based on document type"""
        if doc_type == "national_id":
            return {
                "id_number": f"{random.randint(10000000, 99999999)}",
                "name": f"Student {random.randint(1000, 9999)}",
                "date_of_birth": f"{random.randint(1960, 2000)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                "serial_number": f"ID{random.randint(100000, 999999)}"
            }
        elif doc_type == "passport":
            return {
                "passport_number": f"K{random.randint(100000, 999999)}",
                "name": f"Student {random.randint(1000, 9999)}",
                "nationality": "Kenyan",
                "place_of_birth": "Kenya"
            }
        else:
            return {}
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level based on score"""
        if risk_score >= 0.7:
            return "high"
        elif risk_score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def get_supported_types(self) -> Dict:
        """Get supported document types"""
        return {
            "supported_types": self.supported_types,
            "general_requirements": {
                "min_resolution": "300dpi",
                "max_file_size": "10MB",
                "accepted_formats": ["jpg", "jpeg", "png"],
                "quality_threshold": 0.6
            }
        }
    
    def verify_document_integrity(self, reference_data: Optional[str] = None) -> Dict:
        """Verify document integrity (simplified)"""
        verification_score = random.uniform(0.7, 0.95)
        
        return {
            "document_verified": True,
            "verification_score": verification_score,
            "verification_status": "PASS" if verification_score > 0.8 else "REQUIRES_REVIEW",
            "reference_match": True,
            "field_matches": "4/4" if reference_data else "N/A"
        }
    
    def batch_process(self, documents: List, document_type: Optional[str] = None) -> Dict:
        """Process multiple documents (simplified)"""
        results = []
        successful = 0
        
        for i, doc in enumerate(documents):
            try:
                result = self.process_document("mock_base64_image", document_type)
                result["filename"] = f"document_{i + 1}.jpg"
                result["file_size"] = random.randint(100000, 2000000)
                results.append(result)
                
                if result.get("success", False):
                    successful += 1
            except Exception as e:
                results.append({
                    "success": False,
                    "filename": f"document_{i + 1}.jpg",
                    "error": str(e)
                })
        
        return {
            "batch_results": results,
            "summary": {
                "total_documents": len(documents),
                "successful": successful,
                "failed": len(documents) - successful,
                "success_rate": successful / len(documents) if documents else 0
            }
        }
    
    def get_quality_analysis(self, document_id: str) -> Dict:
        """Get detailed quality analysis (simplified)"""
        return {
            "document_id": document_id,
            "quality_metrics": {
                "sharpness": random.uniform(70, 95),
                "noise_level": random.uniform(5, 20),
                "brightness": random.uniform(100, 150),
                "contrast": random.uniform(40, 70),
                "edge_density": random.uniform(0.1, 0.2),
                "color_variance": random.uniform(120, 180)
            },
            "quality_score": random.uniform(0.7, 0.9),
            "quality_assessment": "good",
            "recommendations": [
                "Image quality is acceptable for verification",
                "All text regions are clearly visible",
                "No significant compression artifacts detected"
            ],
            "processed_at": datetime.now().isoformat()
        }

# Global service instance
simple_document_service = SimpleDocumentService()
