"""
Model Training API Endpoint
Provides REST API for training and managing models
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional
import sys
from pathlib import Path
import logging

# Add training module to path
sys.path.append(str(Path(__file__).parent.parent.parent / "training"))

from training.training_pipeline import UnifiedTrainer
from ..compliance.dpia_audit import dpia_manager

router = APIRouter(prefix="/training", tags=["model_training"])
logger = logging.getLogger(__name__)

class TrainingRequest(BaseModel):
    model_type: Optional[str] = None  # 'rad', 'biometric', 'fraud', or None for all
    epochs: Optional[int] = None
    batch_size: Optional[int] = None

class TrainingResponse(BaseModel):
    status: str
    message: str
    results: Optional[Dict[str, Any]] = None

# Global trainer instance
trainer = None

@router.post("/start", response_model=TrainingResponse)
async def start_training(request: TrainingRequest, background_tasks: BackgroundTasks):
    """
    Start model training process
    """
    global trainer
    
    try:
        trainer = UnifiedTrainer()
        
        # Add training to background tasks
        background_tasks.add_task(run_training_task, request)
        
        return TrainingResponse(
            status="started",
            message=f"Training started for model: {request.model_type or 'all models'}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start training: {str(e)}")

@router.get("/status", response_model=Dict[str, Any])
async def get_training_status():
    """
    Get current training status
    """
    # Check if training is running or completed
    training_results_path = Path("/home/cb-fx/uhakiki-ai/backend/app/training/training_results.json")
    
    if training_results_path.exists():
        import json
        with open(training_results_path, 'r') as f:
            results = json.load(f)
        return {"status": "completed", "results": results}
    else:
        return {"status": "not_started", "results": None}

@router.post("/models/reload")
async def reload_models():
    """
    Reload all models from disk
    """
    try:
        from ..models.model_loader import model_manager
        model_manager.reload_models()
        
        return {"status": "success", "message": "Models reloaded successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload models: {str(e)}")

@router.get("/compliance")
async def get_training_compliance():
    """
    Get DPA 2019 compliance status for training activities
    """
    try:
        compliance_status = dpia_manager.get_compliance_status()
        return compliance_status
        
    except Exception as e:
        logger.error(f"Failed to get compliance status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get compliance: {str(e)}")

@router.post("/compliance/audit")
async def conduct_compliance_audit():
    """
    Conduct DPA 2019 Section 31 compliance audit
    """
    try:
        audit_results = dpia_manager.conduct_dpia_assessment()
        return {
            "status": "completed",
            "message": "DPA 2019 Section 31 audit completed successfully",
            "audit_results": audit_results
        }
        
    except Exception as e:
        logger.error(f"Compliance audit failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Audit failed: {str(e)}")

async def run_training_task(request: TrainingRequest):
    """
    Background task for running training
    """
    try:
        if trainer:
            results = trainer.run_full_training_pipeline()
            print(f"Training completed: {results}")
        else:
            print("Trainer not initialized")
            
    except Exception as e:
        print(f"Training failed: {e}")
