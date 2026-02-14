"""
Analytics API Routes
Provides metrics, trends, and insights for the UhakikiAI dashboard
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
import random
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/metrics")
async def get_verification_metrics():
    """
    Get overall verification system metrics
    """
    try:
        # In production, these would come from your database
        # For now, providing realistic mock data that matches the system
        metrics = {
            "totalVerifications": 45832 + random.randint(-100, 500),
            "fraudPrevented": 1247 + random.randint(-10, 25),
            "shillingsSaved": 2400000000 + random.randint(-100000000, 500000000),
            "averageRiskScore": round(23.4 + random.uniform(-2, 2), 1),
            "processingTime": round(2.3 + random.uniform(-0.3, 0.3), 1),
            "systemHealth": round(98.7 + random.uniform(-1, 1), 1),
        }
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
        stats = {
            "activeVerifications": random.randint(100, 150),
            "queueLength": random.randint(20, 50),
            "averageProcessingTime": round(random.uniform(1.8, 2.5), 1),
            "systemLoad": round(random.uniform(60, 80), 1),
            "errorRate": round(random.uniform(0.5, 1.5), 1),
            "throughput": round(random.uniform(85, 95), 1),
        }
        return stats
    except Exception as e:
        logger.error(f"Failed to get realtime stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve realtime stats")

@router.get("/fraud-trends")
async def get_fraud_trends(period: str = Query("6months", description="Time period for trends")):
    """
    Get fraud detection trends over time
    """
    try:
        # Generate monthly trends for the last 6 months
        trends = []
        base_date = datetime.now() - timedelta(days=180)
        
        for i in range(6):
            month_date = base_date + timedelta(days=30 * i)
            fraud_attempts = random.randint(320, 460)
            fraud_prevented = int(fraud_attempts * random.uniform(0.75, 0.85))
            risk_score = round(random.uniform(22, 35), 1)
            
            trends.append({
                "date": month_date.strftime("%Y-%m"),
                "fraudAttempts": fraud_attempts,
                "fraudPrevented": fraud_prevented,
                "riskScore": risk_score
            })
        
        return trends
    except Exception as e:
        logger.error(f"Failed to get fraud trends: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve fraud trends")

@router.get("/hotspots")
async def get_geographic_hotspots():
    """
    Get geographic fraud hotspots in Kenya
    """
    try:
        # Real Kenyan counties and constituencies with realistic risk scores
        hotspots = [
            {"county": "Nairobi", "constituency": "Kamukunji", "riskScore": round(random.uniform(60, 75), 1), "fraudCases": random.randint(80, 100)},
            {"county": "Mombasa", "constituency": "Mvita", "riskScore": round(random.uniform(50, 65), 1), "fraudCases": random.randint(60, 80)},
            {"county": "Kisumu", "constituency": "Kisumu Central", "riskScore": round(random.uniform(40, 55), 1), "fraudCases": random.randint(35, 55)},
            {"county": "Nakuru", "constituency": "Nakuru Town East", "riskScore": round(random.uniform(35, 50), 1), "fraudCases": random.randint(30, 50)},
            {"county": "Kiambu", "constituency": "Thika Town", "riskScore": round(random.uniform(30, 45), 1), "fraudCases": random.randint(25, 40)},
            {"county": "Uasin Gishu", "constituency": "Eldoret North", "riskScore": round(random.uniform(25, 40), 1), "fraudCases": random.randint(20, 35)},
        ]
        
        # Sort by risk score (highest first)
        hotspots.sort(key=lambda x: x["riskScore"], reverse=True)
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
        fraud_rings = [
            {
                "id": "FR-001",
                "name": "Education Cartel Network",
                "members": random.randint(40, 55),
                "detectedDate": "2024-03-15",
                "riskLevel": "critical",
                "totalAmount": random.randint(40000000, 50000000),
                "status": "disrupted"
            },
            {
                "id": "FR-002", 
                "name": "Identity Farming Operation",
                "members": random.randint(20, 30),
                "detectedDate": "2024-05-22",
                "riskLevel": "high",
                "totalAmount": random.randint(25000000, 35000000),
                "status": "investigating"
            },
            {
                "id": "FR-003",
                "name": "Document Synthesis Ring", 
                "members": random.randint(12, 20),
                "detectedDate": "2024-06-08",
                "riskLevel": "medium",
                "totalAmount": random.randint(10000000, 20000000),
                "status": "active"
            },
            {
                "id": "FR-004",
                "name": "Exam Impersonation Syndicate",
                "members": random.randint(8, 15),
                "detectedDate": "2024-06-18",
                "riskLevel": "high", 
                "totalAmount": random.randint(15000000, 25000000),
                "status": "investigating"
            }
        ]
        
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
    Get paginated list of verification records
    """
    try:
        # In production, fetch from database
        # For now, generate realistic verification records
        verifications = []
        statuses = ["completed", "processing", "failed", "pending"]
        verdicts = ["PASS", "FAIL", "REQUIRES_HUMAN_REVIEW", "PENDING"]
        
        for i in range(limit):
            tracking_id = f"VR-2024-{8000 + offset + i:04d}"
            student_id = f"STU-2024-{8000 + offset + i:04d}"
            national_id = f"{random.randint(100000000, 999999999)}"
            
            # Generate timestamp within last 30 days
            days_ago = random.randint(0, 30)
            timestamp = (datetime.now() - timedelta(days=days_ago)).isoformat()
            
            status = random.choice(statuses)
            verdict = random.choice(verdicts) if status == "completed" else "PENDING"
            
            verification = {
                "tracking_id": tracking_id,
                "student_id": student_id,
                "national_id": national_id,
                "timestamp": timestamp,
                "status": status,
                "final_verdict": verdict,
                "confidence_score": round(random.uniform(60, 99), 1) if status == "completed" else 0,
                "risk_score": round(random.uniform(5, 80), 1) if status == "completed" else 0,
                "processing_time": round(random.uniform(1.5, 5.0), 1) if status == "completed" else 0,
                "components": {
                    "document_analysis": {
                        "forgery_probability": round(random.uniform(0.01, 0.45), 2),
                        "judgment": random.choice(["AUTHENTIC", "SUSPICIOUS"])
                    },
                    "biometric_analysis": {
                        "overall_score": round(random.uniform(70, 99), 1),
                        "verified": random.choice([True, False])
                    },
                    "aafi_decision": {
                        "verdict": random.choice(["APPROVED", "REQUIRES_REVIEW", "FLAGGED"]),
                        "confidence": round(random.uniform(65, 98), 1)
                    }
                } if status == "completed" else None
            }
            
            verifications.append(verification)
        
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
        health = {
            "status": "ONLINE",
            "phase": "2 - Agentic Intelligence",
            "uptime": random.randint(86400, 2592000), # 1 day to 30 days in seconds
            "memory_usage": round(random.uniform(40, 75), 1),
            "cpu_usage": round(random.uniform(20, 60), 1),
            "active_connections": random.randint(50, 200),
            "database_status": "HEALTHY",
            "ml_models_status": "ACTIVE",
            "services": {
                "face_recognition": "ACTIVE",
                "document_analysis": "ACTIVE", 
                "liveness_detection": "ACTIVE",
                "security_council": "ACTIVE",
                "milvus_vault": "HEALTHY",
                "redis_cache": "HEALTHY"
            }
        }
        return health
    except Exception as e:
        logger.error(f"Failed to get system health: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system health")
