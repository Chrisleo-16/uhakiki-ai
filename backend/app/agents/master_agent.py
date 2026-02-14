"""
Master Agent - Central Orchestration for UhakikiAI AAFI System
Implements Plan-Act-Reflect recursive loop with dynamic agent coordination
"""

import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
import time
from datetime import datetime

from crewai import Agent, Task, Crew, Process, LLM
from .data_ingestion_agent import DataIngestionAgent
from .anomaly_detection_agent import AnomalyDetectionAgent  
from .risk_scoring_agent import RiskScoringAgent
from .reporting_agent import ReportingAgent


class VerificationPhase(Enum):
    OBSERVE = "observe"
    ORIENT = "orient" 
    DECIDE = "decide"
    ACT = "act"


@dataclass
class VerificationContext:
    """Shared context across all agents in the verification pipeline"""
    student_id: str
    national_id: str
    document_path: str
    biometric_data: Dict[str, Any]
    verification_history: List[Dict]
    current_phase: VerificationPhase
    risk_score: float = 0.0
    anomaly_indicators: List[str] = None
    agent_outputs: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.anomaly_indicators is None:
            self.anomaly_indicators = []
        if self.agent_outputs is None:
            self.agent_outputs = {}


class MasterAgent:
    """
    Central orchestration agent that manages the entire AAFI pipeline
    Implements recursive Plan-Act-Reflect loop for autonomous fraud investigation
    """
    
    def __init__(self):
        self.llm = self._get_sovereign_brain()
        self.max_reflection_cycles = 3
        self.risk_thresholds = {
            "low": 30.0,
            "medium": 60.0, 
            "high": 85.0
        }
        
        # Initialize specialized agents
        self.data_agent = DataIngestionAgent(self.llm)
        self.anomaly_agent = AnomalyDetectionAgent(self.llm)
        self.risk_agent = RiskScoringAgent(self.llm)
        self.reporting_agent = ReportingAgent(self.llm)
        
        self.verification_log = []
    
    def _get_sovereign_brain(self):
        """Dynamic LLM selection based on system resources"""
        import psutil
        stats = psutil.virtual_memory()
        available_gb = stats.available / (1024 ** 3)
        
        if available_gb > 4.5:
            return LLM(
                model="openai/phi3:mini",
                base_url="http://localhost:11434/v1",
                api_key="NA"
            )
        else:
            return LLM(
                model="openai/qwen2:0.5b", 
                base_url="http://localhost:11434/v1",
                api_key="NA"
            )
    
    async def run_verification_pipeline(self, context: VerificationContext) -> Dict[str, Any]:
        """
        Main verification pipeline implementing Plan-Act-Reflect loop
        """
        print(f"🏛️ [MASTER] Starting AAFI verification for student {context.student_id}")
        
        cycle_count = 0
        final_decision = None
        
        while cycle_count < self.max_reflection_cycles and not final_decision:
            cycle_count += 1
            print(f"\n--- REFLECTION CYCLE {cycle_count} ---")
            
            # PLAN PHASE
            plan = await self._plan_phase(context)
            print(f"📋 [PLAN] {plan}")
            
            # ACT PHASE  
            await self._act_phase(context)
            
            # REFLECT PHASE
            decision, confidence = await self._reflect_phase(context)
            print(f"🤔 [REFLECT] Decision: {decision} (Confidence: {confidence:.2f})")
            
            # Check if we have high confidence decision
            if confidence >= 0.85:
                final_decision = decision
            elif cycle_count >= self.max_reflection_cycles:
                final_decision = "REQUIRES_HUMAN_REVIEW"
        
        # Generate final report
        final_report = await self.reporting_agent.generate_final_report(
            context, final_decision, cycle_count
        )
        
        return {
            "verdict": final_decision,
            "confidence": confidence if 'confidence' in locals() else 0.5,
            "risk_score": context.risk_score,
            "cycles_completed": cycle_count,
            "report": final_report,
            "audit_log": self.verification_log
        }
    
    async def _plan_phase(self, context: VerificationContext) -> str:
        """Plan phase: Determine next actions based on current state"""
        context.current_phase = VerificationPhase.OBSERVE
        
        # Data ingestion first
        if not context.agent_outputs.get("data_ingestion"):
            await self.data_agent.ingest_data(context)
        
        # Plan based on risk level
        if context.risk_score > self.risk_thresholds["high"]:
            return "High risk detected - Deep anomaly analysis required"
        elif context.risk_score > self.risk_thresholds["medium"]:
            return "Medium risk - Enhanced verification needed"
        else:
            return "Low risk - Standard verification sufficient"
    
    async def _act_phase(self, context: VerificationContext):
        """Act phase: Execute specialized agent tasks"""
        context.current_phase = VerificationPhase.ORIENT
        
        # Anomaly detection
        if not context.agent_outputs.get("anomaly_detection"):
            anomaly_results = await self.anomaly_agent.detect_anomalies(context)
            context.agent_outputs["anomaly_detection"] = anomaly_results
            context.anomaly_indicators.extend(anomaly_results.get("anomalies", []))
        
        # Risk scoring
        if not context.agent_outputs.get("risk_scoring"):
            risk_results = await self.risk_agent.calculate_risk_score(context)
            context.agent_outputs["risk_scoring"] = risk_results
            context.risk_score = risk_results.get("overall_risk_score", 0.0)
        
        context.current_phase = VerificationPhase.DECIDE
    
    async def _reflect_phase(self, context: VerificationContext) -> tuple[str, float]:
        """Reflect phase: Analyze results and determine confidence"""
        context.current_phase = VerificationPhase.ACT
        
        # Analyze all agent outputs
        risk_score = context.risk_score
        anomalies = context.anomaly_indicators
        
        # Calculate confidence based on consistency of signals
        confidence = self._calculate_confidence(context)
        
        # Determine decision
        if risk_score >= self.risk_thresholds["high"] or len(anomalies) >= 3:
            decision = "FAIL"
        elif risk_score <= self.risk_thresholds["low"] and len(anomalies) == 0:
            decision = "PASS"
        else:
            decision = "REQUIRES_HUMAN_REVIEW"
        
        # Log this reflection cycle
        log_entry = {
            "cycle": len(self.verification_log) + 1,
            "timestamp": datetime.now().isoformat(),
            "phase": context.current_phase.value,
            "risk_score": risk_score,
            "anomalies": anomalies.copy(),
            "decision": decision,
            "confidence": confidence
        }
        self.verification_log.append(log_entry)
        
        return decision, confidence
    
    def _calculate_confidence(self, context: VerificationContext) -> float:
        """Calculate confidence in the current decision"""
        base_confidence = 0.5
        
        # Increase confidence based on data quality
        if context.agent_outputs.get("data_ingestion", {}).get("data_quality", 0) > 0.8:
            base_confidence += 0.2
        
        # Increase confidence if multiple agents agree
        anomaly_score = context.agent_outputs.get("anomaly_detection", {}).get("anomaly_score", 0)
        risk_score = context.risk_score
        
        # Consistency between anomaly detection and risk scoring
        if (anomaly_score > 0.7 and risk_score > 70) or (anomaly_score < 0.3 and risk_score < 30):
            base_confidence += 0.3
        
        return min(base_confidence, 1.0)


# Singleton instance for system-wide use
master_agent = MasterAgent()
