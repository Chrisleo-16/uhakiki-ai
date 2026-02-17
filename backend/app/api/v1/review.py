"""
Review API Routes
Handles human review workflow for flagged verifications
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional
from pydantic import BaseModel
import logging
from app.services.simple_review_service import simple_review_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Pydantic models for request/response
class ReviewCase(BaseModel):
    id: str
    student_id: str
    national_id: str
    risk_score: float
    priority: str
    assigned_to: str
    created_at: str
    status: str
    notes: List[str]
    tracking_id: str
    document_url: Optional[str] = ""
    biometric_url: Optional[str] = ""

class ReviewUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[List[str]] = None
    review_verdict: Optional[str] = None

class CaseAssignment(BaseModel):
    officer_name: str

class ReviewCompletion(BaseModel):
    verdict: str  # "APPROVED", "REJECTED", "REQUIRES_FURTHER_INVESTIGATION"
    notes: List[str]

@router.get("/cases", response_model=List[ReviewCase])
async def get_review_cases(
    status: str = Query("pending", description="Filter by review status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get cases that need human review
    """
    try:
        cases = simple_review_service.get_review_cases(status, limit, offset)
        return cases
    except Exception as e:
        logger.error(f"Failed to get review cases: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve review cases")

@router.get("/cases/{case_id}", response_model=ReviewCase)
async def get_review_case(case_id: str):
    """
    Get specific review case by ID
    """
    try:
        case = simple_review_service.get_review_case_by_id(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Review case not found")
        return case
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get review case {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve review case")

@router.put("/cases/{case_id}")
async def update_review_case(case_id: str, updates: ReviewUpdate):
    """
    Update review case with new information
    """
    try:
        success = simple_review_service.update_review_case(case_id, updates.dict(exclude_unset=True))
        if not success:
            raise HTTPException(status_code=404, detail="Review case not found or update failed")
        return {"message": "Review case updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update review case {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update review case")

@router.post("/cases/{case_id}/assign")
async def assign_review_case(case_id: str, assignment: CaseAssignment):
    """
    Assign a case to a review officer
    """
    try:
        success = simple_review_service.assign_case(case_id, assignment.officer_name)
        if not success:
            raise HTTPException(status_code=404, detail="Review case not found or assignment failed")
        return {"message": f"Case assigned to {assignment.officer_name}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign case {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to assign case")

@router.post("/cases/{case_id}/complete")
async def complete_review(case_id: str, completion: ReviewCompletion):
    """
    Complete a review with verdict and notes
    """
    try:
        success = simple_review_service.complete_review(case_id, completion.verdict, completion.notes)
        if not success:
            raise HTTPException(status_code=404, detail="Review case not found or completion failed")
        return {"message": "Review completed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to complete review {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to complete review")

@router.get("/stats")
async def get_review_stats():
    """
    Get review workflow statistics
    """
    try:
        # Get cases by status using simple_review_service
        pending_cases = simple_review_service.get_review_cases("pending", limit=1000)
        assigned_cases = simple_review_service.get_review_cases("assigned", limit=1000)
        completed_cases = simple_review_service.get_review_cases("completed", limit=1000)
        
        # Calculate stats
        stats = {
            "pending_cases": len(pending_cases),
            "assigned_cases": len(assigned_cases),
            "completed_cases": len(completed_cases),
            "total_cases": len(pending_cases) + len(assigned_cases) + len(completed_cases),
            "critical_priority": len([c for c in pending_cases if c.get("priority") == "critical"]),
            "high_priority": len([c for c in pending_cases if c.get("priority") == "high"]),
            "average_review_time": "2.5 hours",  # This would be calculated from timestamps in production
        }
        
        return stats
    except Exception as e:
        logger.error(f"Failed to get review stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve review statistics")
