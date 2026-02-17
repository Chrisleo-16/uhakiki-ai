import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

app = FastAPI(
    title="Uhakiki-AI: Sovereign Identity Engine",
    description="Agentic Fraud Detection System backed by Milvus & Neural Embeddings.",
    version="Phase-2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Your Next.js URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include only review router for now
from app.api.v1 import review
app.include_router(review.router, prefix="/api/v1/review")

@app.get("/")
async def root():
    return {"message": "Uhakiki-AI API is running"}

@app.get("/api/v1/health")
def health_check():
    return {"status": "ONLINE", "phase": "2 - Agentic Intelligence"}

# Mock endpoints for dashboard
@app.get("/api/v1/metrics")
def get_verification_metrics():
    return {
        "totalVerifications": 15420,
        "fraudPrevented": 1247,
        "shillingsSaved": 186500000,
        "averageRiskScore": 34.2,
        "processingTime": 2.8,
        "systemHealth": 98.7
    }

@app.get("/api/v1/realtime-stats")
def get_realtime_stats():
    return {
        "activeVerifications": 23,
        "queueLength": 47,
        "averageProcessingTime": 2.1,
        "systemLoad": 67.3,
        "errorRate": 0.2,
        "throughput": 145.7
    }

@app.get("/api/v1/fraud-trends")
def get_fraud_trends():
    return [
        {"date": "2024-06-01", "fraudAttempts": 45, "fraudPrevented": 38, "riskScore": 42.1},
        {"date": "2024-06-02", "fraudAttempts": 52, "fraudPrevented": 44, "riskScore": 38.7},
        {"date": "2024-06-03", "fraudAttempts": 38, "fraudPrevented": 35, "riskScore": 35.2},
        {"date": "2024-06-04", "fraudAttempts": 61, "fraudPrevented": 52, "riskScore": 45.8},
        {"date": "2024-06-05", "fraudAttempts": 47, "fraudPrevented": 41, "riskScore": 39.4},
        {"date": "2024-06-06", "fraudAttempts": 55, "fraudPrevented": 48, "riskScore": 41.2},
    ]

@app.get("/api/v1/hotspots")
def get_geographic_hotspots():
    return [
        {"county": "Nairobi", "constituency": "Kasarani", "riskScore": 67.8, "fraudCases": 145},
        {"county": "Mombasa", "constituency": "Mvita", "riskScore": 58.3, "fraudCases": 89},
        {"county": "Kisumu", "constituency": "Kisumu Central", "riskScore": 52.1, "fraudCases": 67},
        {"county": "Nakuru", "constituency": "Nakuru Town East", "riskScore": 48.9, "fraudCases": 54},
        {"county": "Kiambu", "constituency": "Thika", "riskScore": 45.2, "fraudCases": 43},
    ]

@app.get("/api/v1/fraud-rings")
def get_fraud_rings():
    return [
        {
            "id": "FR-001",
            "name": "Nairobi Student Loan Syndicate",
            "members": 12,
            "detectedDate": "2024-05-15",
            "riskLevel": "critical",
            "totalAmount": 24500000,
            "status": "disrupted"
        },
        {
            "id": "FR-002", 
            "name": "Coastal Identity Ring",
            "members": 8,
            "detectedDate": "2024-06-02",
            "riskLevel": "high",
            "totalAmount": 12800000,
            "status": "investigating"
        },
        {
            "id": "FR-003",
            "name": "Western Kenya Fraud Network",
            "members": 6,
            "detectedDate": "2024-06-10",
            "riskLevel": "medium",
            "totalAmount": 8700000,
            "status": "active"
        }
    ]
