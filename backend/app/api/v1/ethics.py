"""
Ethics & Fairness API Routes
Exposes bias detection and fairness metrics
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from app.ethics.bias_detector import bias_detector
from app.benchmark.benchmark_engine import benchmark_engine
from app.tests.robustness_tests import robustness_tester
from app.crisis.crisis_mode import crisis_mode_manager, CrisisMode

router = APIRouter()


# =====================
# BIAS & FAIRNESS (D3)
# =====================

class RecordDecisionRequest(BaseModel):
    decision: str
    risk_score: float
    region: str = "unknown"
    age_group: str = "unknown"
    document_type: str = "unknown"
    confidence: float = 0.0


@router.post("/bias/record")
async def record_decision(request: RecordDecisionRequest):
    """Record a verification decision for bias analysis"""
    try:
        bias_detector.record_decision(request.dict())
        return {"success": True, "message": "Decision recorded for bias analysis"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bias/report")
async def get_bias_report():
    """Get comprehensive bias and fairness report"""
    try:
        report = bias_detector.generate_bias_report()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# BENCHMARKING (B1)
# =====================

class RunBenchmarkRequest(BaseModel):
    test_samples: int = 100


@router.post("/benchmark/run")
async def run_benchmark(request: RunBenchmarkRequest = None):
    """Run benchmark tests against baseline"""
    try:
        samples = request.test_samples if request else 100
        results = benchmark_engine.run_benchmark(test_samples=samples)
        return {"status": "completed", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benchmark/results")
async def get_benchmark_results():
    """Get latest benchmark results"""
    try:
        results = benchmark_engine.get_latest_results()
        if not results:
            return {"status": "NO_BENCHMARKS", "message": "Run benchmark to get results"}
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benchmark/summary")
async def get_benchmark_summary():
    """Get performance summary across all benchmarks"""
    try:
        summary = benchmark_engine.get_performance_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# ROBUSTNESS TESTS (B2)
# =====================

@router.post("/robustness/stress")
async def run_stress_test(concurrent_requests: int = 100):
    """Run stress test with concurrent requests"""
    try:
        results = robustness_tester.run_stress_test(concurrent_requests)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/robustness/edge-cases")
async def run_edge_case_tests():
    """Run edge case tests"""
    try:
        results = robustness_tester.run_edge_case_tests()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/robustness/adversarial")
async def run_adversarial_tests():
    """Run adversarial input tests"""
    try:
        results = robustness_tester.run_adversarial_tests()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/robustness/full")
async def run_full_robustness_tests():
    """Run complete robustness test suite"""
    try:
        results = robustness_tester.run_all_robustness_tests()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# CRISIS MODE (A3)
# =====================

class SetCrisisModeRequest(BaseModel):
    mode: str  # normal, pandemic, emergency, offline


@router.get("/crisis-mode")
async def get_crisis_mode():
    """Get current crisis mode status"""
    try:
        status = crisis_mode_manager.get_current_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crisis-mode")
async def set_crisis_mode(request: SetCrisisModeRequest):
    """Set crisis mode"""
    try:
        mode_map = {
            "normal": CrisisMode.NORMAL,
            "pandemic": CrisisMode.PANDEMIC,
            "emergency": CrisisMode.EMERGENCY,
            "offline": CrisisMode.OFFLINE
        }
        
        if request.mode not in mode_map:
            raise HTTPException(status_code=400, detail=f"Invalid mode: {request.mode}")
        
        result = crisis_mode_manager.set_mode(mode_map[request.mode])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crisis-mode/bulk-stats")
async def get_bulk_verification_stats():
    """Get bulk verification statistics for crisis mode"""
    try:
        stats = crisis_mode_manager.get_bulk_verification_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
