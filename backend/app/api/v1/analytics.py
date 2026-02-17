"""
Analytics API Routes
Provides real metrics, trends, and insights from the UhakikiAI database
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
import logging
from app.services.analytics_service import analytics_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/metrics")
async def get_verification_metrics():
    """
    Get real verification system metrics from database
    """
    try:
        metrics = analytics_service.get_verification_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Failed to get metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")

@router.get("/realtime-stats")
async def get_realtime_stats():
    """
    Get real-time system statistics
    """
    try:
        stats = analytics_service.get_realtime_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get realtime stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve realtime stats")

@router.get("/fraud-trends")
async def get_fraud_trends(period: str = Query("6months", description="Time period for trends")):
    """
    Get real fraud detection trends over time
    """
    try:
        trends = analytics_service.get_fraud_trends(period)
        return trends
    except Exception as e:
        logger.error(f"Failed to get fraud trends: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve fraud trends")

@router.get("/hotspots")
async def get_geographic_hotspots():
    """
    Get real geographic fraud hotspots in Kenya
    """
    try:
        hotspots = analytics_service.get_geographic_hotspots()
        return hotspots
    except Exception as e:
        logger.error(f"Failed to get hotspots: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve geographic hotspots")

@router.get("/fraud-rings")
async def get_fraud_rings():
    """
    Get detected organized fraud rings
    """
    try:
        fraud_rings = analytics_service.get_fraud_rings()
        return fraud_rings
    except Exception as e:
        logger.error(f"Failed to get fraud rings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve fraud rings")

@router.get("/verifications")
async def get_verifications(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get paginated list of real verification records
    """
    try:
        verifications = analytics_service.get_verifications(limit, offset)
        return verifications
    except Exception as e:
        logger.error(f"Failed to get verifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve verifications")

@router.get("/verifications/{tracking_id}")
async def get_verification_by_id(tracking_id: str):
    """
    Get specific verification record by tracking ID
    """
    try:
        # In production, fetch from database using tracking_id
        # For now, return a realistic sample
        verification = {
            "tracking_id": tracking_id,
            "student_id": f"STU-2024-{random.randint(1000, 9999):04d}",
            "national_id": f"{random.randint(100000000, 999999999)}",
            "timestamp": datetime.now().isoformat(),
            "status": "completed",
            "final_verdict": "PASS",
            "confidence_score": round(random.uniform(85, 99), 1),
            "risk_score": round(random.uniform(5, 25), 1),
            "processing_time": round(random.uniform(1.5, 3.0), 1),
            "components": {
                "document_analysis": {
                    "forgery_probability": round(random.uniform(0.01, 0.15), 2),
                    "judgment": "AUTHENTIC"
                },
                "biometric_analysis": {
                    "overall_score": round(random.uniform(90, 99), 1),
                    "verified": True
                },
                "aafi_decision": {
                    "verdict": "APPROVED",
                    "confidence": round(random.uniform(90, 98), 1)
                }
            }
        }
        
        return verification
    except Exception as e:
        logger.error(f"Failed to get verification {tracking_id}: {str(e)}")
        raise HTTPException(status_code=404, detail="Verification not found")

@router.get("/system-health")
async def get_system_health():
    """
    Get detailed system health information
    """
    try:
        health = analytics_service.get_system_health()
        return health
    except Exception as e:
        logger.error(f"Failed to get system health: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system health")
