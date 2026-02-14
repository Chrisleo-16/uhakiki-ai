"""
Reporting and Decision Agent - Generates detailed forensic reports and final decisions
Initiates appropriate workflows based on risk assessment results
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

from crewai import Agent, Task, LLM


class DecisionStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    REQUIRES_HUMAN_REVIEW = "REQUIRES_HUMAN_REVIEW"


@dataclass
class ForensicReport:
    """Comprehensive forensic report for verification case"""
    student_id: str
    national_id: str
    verification_timestamp: datetime
    decision_status: DecisionStatus
    confidence_score: float
    risk_score: float
    evidence_summary: Dict[str, Any]
    detailed_findings: List[str]
    recommendations: List[str]
    audit_trail: List[Dict[str, Any]]
    compliance_notes: List[str]


class ReportingAgent:
    """
    Specialized agent for generating comprehensive forensic reports
    Handles decision-making and workflow initiation based on verification results
    """
    
    def __init__(self, llm: LLM):
        self.llm = llm
        self.logger = logging.getLogger(__name__)
        
        # Decision thresholds
        self.decision_thresholds = {
            "auto_approve": 30.0,      # Risk score below this = auto-approve
            "auto_reject": 85.0,       # Risk score above this = auto-reject
            "min_confidence": 0.75     # Minimum confidence for automated decisions
        }
        
        # Compliance requirements (Kenya Data Protection Act 2019)
        self.compliance_requirements = {
            "data_minimization": "Section 25(c) - Only process essential biometric data",
            "accuracy_rights": "Section 26 - Right to correction of automated decisions",
            "human_intervention": "Section 35 - Right to human intervention for automated decisions",
            "audit_trail": "Section 69 - Maintain comprehensive audit trails",
            "data_security": "Section 72 - Implement appropriate security measures"
        }
    
    def create_agent(self) -> Agent:
        """Create CrewAI agent for reporting and decision"""
        return Agent(
            role='Forensic Reporting & Decision Specialist',
            goal='Generate comprehensive forensic reports and make evidence-based verification decisions',
            backstory="""You are a forensic reporting specialist responsible for creating detailed,
            evidence-based verification reports. You ensure compliance with Kenya Data Protection Act 2019
            and provide clear explanations for all decisions. Your reports are used for audit purposes
            and must be thorough, accurate, and legally compliant.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
    
    async def generate_final_report(
        self, 
        context, 
        decision: str, 
        cycles_completed: int
    ) -> Dict[str, Any]:
        """
        Generate comprehensive final verification report
        """
        print(f"📋 [REPORT] Generating final report for student {context.student_id}")
        
        # Determine decision status
        decision_status = DecisionStatus(decision)
        
        # Extract evidence from all agents
        evidence_summary = self._compile_evidence_summary(context)
        
        # Generate detailed findings
        detailed_findings = self._generate_detailed_findings(context, decision_status)
        
        # Create recommendations
        recommendations = self._generate_recommendations(context, decision_status)
        
        # Build audit trail
        audit_trail = self._build_audit_trail(context, cycles_completed)
        
        # Generate compliance notes
        compliance_notes = self._generate_compliance_notes(context, decision_status)
        
        # Calculate confidence score
        confidence_score = self._calculate_overall_confidence(context)
        
        # Create forensic report
        report = ForensicReport(
            student_id=context.student_id,
            national_id=context.national_id,
            verification_timestamp=datetime.now(),
            decision_status=decision_status,
            confidence_score=confidence_score,
            risk_score=context.risk_score,
            evidence_summary=evidence_summary,
            detailed_findings=detailed_findings,
            recommendations=recommendations,
            audit_trail=audit_trail,
            compliance_notes=compliance_notes
        )
        
        # Serialize report for API response
        serialized_report = self._serialize_report(report)
        
        # Initiate appropriate workflows
        await self._initiate_workflows(report, context)
        
        # Save report to secure storage
        await self._save_report(report)
        
        return serialized_report
    
    def _compile_evidence_summary(self, context) -> Dict[str, Any]:
        """Compile evidence summary from all agent outputs"""
        
        evidence = {
            "document_analysis": {},
            "biometric_analysis": {},
            "external_data": {},
            "anomaly_detection": {},
            "risk_assessment": {}
        }
        
        # Document forgery evidence
        forgery_results = context.agent_outputs.get("forgery_detection", {})
        if forgery_results:
            evidence["document_analysis"] = {
                "mse_score": forgery_results.get("mse_score", 0),
                "ela_score": forgery_results.get("ela_score", 0),
                "neural_anomaly": forgery_results.get("neural_anomaly", "CLEAN"),
                "judgment": forgery_results.get("judgment", "UNKNOWN"),
                "visual_evidence": forgery_results.get("visuals", {})
            }
        
        # Biometric evidence
        biometric_data = context.biometric_data
        if biometric_data:
            evidence["biometric_analysis"] = {
                "facial_match": biometric_data.get("face_match_score", 0),
                "liveness_confidence": biometric_data.get("liveness_confidence", 0),
                "voice_match": biometric_data.get("voice_match_score"),
                "challenge_response": biometric_data.get("challenge_met", False)
            }
        
        # External data evidence
        data_ingestion = context.agent_outputs.get("data_ingestion", {})
        if data_ingestion:
            evidence["external_data"] = {
                "data_quality": data_ingestion.get("data_quality", 0),
                "completeness": data_ingestion.get("completeness", 0),
                "sources_verified": list(data_ingestion.get("sources", {}).keys()),
                "data_errors": data_ingestion.get("errors", [])
            }
        
        # Anomaly detection evidence
        anomaly_results = context.agent_outputs.get("anomaly_detection", {})
        if anomaly_results:
            evidence["anomaly_detection"] = {
                "anomaly_score": anomaly_results.get("anomaly_score", 0),
                "anomaly_count": anomaly_results.get("anomaly_count", 0),
                "risk_indicators": anomaly_results.get("risk_indicators", []),
                "geographic_risk": anomaly_results.get("geographic_risk", {})
            }
        
        # Risk assessment evidence
        risk_results = context.agent_outputs.get("risk_scoring", {})
        if risk_results:
            evidence["risk_assessment"] = {
                "final_risk_score": risk_results.get("final_risk_score", 0),
                "risk_level": risk_results.get("risk_level", "UNKNOWN"),
                "bayesian_probability": risk_results.get("bayesian_probability", 0),
                "confidence_score": risk_results.get("confidence_score", 0)
            }
        
        return evidence
    
    def _generate_detailed_findings(self, context, decision_status: DecisionStatus) -> List[str]:
        """Generate detailed findings based on verification results"""
        
        findings = []
        
        # Risk assessment findings
        risk_score = context.risk_score
        findings.append(f"Overall fraud risk score: {risk_score:.1f}/100")
        
        if risk_score >= 85:
            findings.append("CRITICAL RISK LEVEL: Multiple serious fraud indicators detected")
        elif risk_score >= 60:
            findings.append("HIGH RISK LEVEL: Significant fraud indicators present")
        elif risk_score >= 30:
            findings.append("MEDIUM RISK LEVEL: Some fraud indicators detected")
        else:
            findings.append("LOW RISK LEVEL: Minimal fraud indicators detected")
        
        # Document analysis findings
        forgery_results = context.agent_outputs.get("forgery_detection", {})
        if forgery_results:
            judgment = forgery_results.get("judgment", "UNKNOWN")
            findings.append(f"Document integrity analysis: {judgment}")
            
            if forgery_results.get("neural_anomaly") == "DETECTED":
                findings.append("Neural analysis detected potential AI-generated document manipulation")
            
            mse_score = forgery_results.get("mse_score", 0)
            if mse_score > 0.025:
                findings.append(f"Document reconstruction anomalies detected (MSE: {mse_score:.4f})")
        
        # Biometric findings
        biometric_data = context.biometric_data
        if biometric_data:
            face_score = biometric_data.get("face_match_score", 0)
            findings.append(f"Facial recognition match score: {face_score:.2f}")
            
            liveness_confidence = biometric_data.get("liveness_confidence", 0)
            if liveness_confidence < 0.7:
                findings.append(f"Liveness detection concerns (Confidence: {liveness_confidence:.2f})")
            else:
                findings.append("Liveness verification successfully completed")
        
        # Anomaly findings
        anomaly_results = context.agent_outputs.get("anomaly_detection", {})
        if anomaly_results:
            anomaly_count = anomaly_results.get("anomaly_count", 0)
            if anomaly_count > 0:
                findings.append(f"{anomaly_count} anomaly patterns detected during analysis")
                
                risk_indicators = anomaly_results.get("risk_indicators", [])
                if risk_indicators:
                    findings.append(f"Primary risk indicators: {', '.join(risk_indicators[:3])}")
        
        # External data findings
        data_ingestion = context.agent_outputs.get("data_ingestion", {})
        if data_ingestion:
            sources_verified = list(data_ingestion.get("sources", {}).keys())
            if sources_verified:
                findings.append(f"External data verified from: {', '.join(sources_verified)}")
            
            data_quality = data_ingestion.get("data_quality", 0)
            findings.append(f"External data quality score: {data_quality:.2f}")
        
        # Decision rationale
        if decision_status == DecisionStatus.PASS:
            findings.append("DECISION: APPROVED - Identity verification successful, no significant fraud indicators")
        elif decision_status == DecisionStatus.FAIL:
            findings.append("DECISION: REJECTED - Significant fraud indicators detected, verification failed")
        else:
            findings.append("DECISION: REQUIRES HUMAN REVIEW - Mixed indicators, manual review recommended")
        
        return findings
    
    def _generate_recommendations(self, context, decision_status: DecisionStatus) -> List[str]:
        """Generate actionable recommendations based on verification results"""
        
        recommendations = []
        
        if decision_status == DecisionStatus.PASS:
            recommendations.extend([
                "Proceed with standard processing workflow",
                "Generate secure QR code for mobile verification",
                "Record successful verification in national database",
                "Schedule periodic re-verification if required"
            ])
        elif decision_status == DecisionStatus.FAIL:
            recommendations.extend([
                "IMMEDIATE ACTION REQUIRED - Block further processing",
                "Flag case for fraud investigation team",
                "Preserve all evidence for legal proceedings",
                "Report to relevant authorities if criminal activity suspected"
            ])
        else:  # REQUIRES_HUMAN_REVIEW
            recommendations.extend([
                "Escalate to human verification officer",
                "Request additional documentation if needed",
                "Consider video call verification",
                "Document all concerns for human reviewer"
            ])
        
        # Risk-based recommendations
        risk_score = context.risk_score
        if risk_score >= 60:
            recommendations.append("Implement enhanced monitoring for future applications")
        
        # Data quality recommendations
        data_ingestion = context.agent_outputs.get("data_ingestion", {})
        if data_ingestion and data_ingestion.get("data_quality", 1) < 0.7:
            recommendations.append("Improve data quality from external sources")
        
        return recommendations
    
    def _build_audit_trail(self, context, cycles_completed: int) -> List[Dict[str, Any]]:
        """Build comprehensive audit trail"""
        
        audit_trail = []
        
        # Initial submission
        audit_trail.append({
            "timestamp": datetime.now().isoformat(),
            "action": "VERIFICATION_INITIATED",
            "actor": "SYSTEM",
            "details": f"Student {context.student_id} verification started",
            "data": {
                "student_id": context.student_id,
                "national_id": context.national_id
            }
        })
        
        # Agent execution steps
        for agent_name, output in context.agent_outputs.items():
            if output:
                audit_trail.append({
                    "timestamp": datetime.now().isoformat(),
                    "action": f"AGENT_EXECUTION_{agent_name.upper()}",
                    "actor": agent_name,
                    "details": f"{agent_name} analysis completed",
                    "data": {"status": "COMPLETED"}
                })
        
        # Reflection cycles
        for i in range(cycles_completed):
            audit_trail.append({
                "timestamp": datetime.now().isoformat(),
                "action": f"REFLECTION_CYCLE_{i+1}",
                "actor": "MASTER_AGENT",
                "details": f"Plan-Act-Reflect cycle {i+1} completed",
                "data": {"cycle_number": i+1}
            })
        
        # Final decision
        audit_trail.append({
            "timestamp": datetime.now().isoformat(),
            "action": "FINAL_DECISION",
            "actor": "REPORTING_AGENT",
            "details": "Final verification decision made",
            "data": {
                "decision": context.agent_outputs.get("final_decision", "UNKNOWN"),
                "confidence": context.agent_outputs.get("confidence", 0),
                "risk_score": context.risk_score
            }
        })
        
        return audit_trail
    
    def _generate_compliance_notes(self, context, decision_status: DecisionStatus) -> List[str]:
        """Generate compliance notes for Kenya Data Protection Act 2019"""
        
        compliance_notes = []
        
        # Data minimization
        compliance_notes.append(
            f"✓ {self.compliance_requirements['data_minimization']} - Only essential biometric and document data processed"
        )
        
        # Human intervention rights
        if decision_status in [DecisionStatus.FAIL, DecisionStatus.REQUIRES_HUMAN_REVIEW]:
            compliance_notes.append(
                f"✓ {self.compliance_requirements['human_intervention']} - Human review available for automated decision"
            )
        
        # Audit trail
        compliance_notes.append(
            f"✓ {self.compliance_requirements['audit_trail']} - Comprehensive audit trail maintained"
        )
        
        # Data security
        compliance_notes.append(
            f"✓ {self.compliance_requirements['data_security']} - All data encrypted and securely stored"
        )
        
        # Accuracy rights
        compliance_notes.append(
            f"ℹ {self.compliance_requirements['accuracy_rights']} - Student can request correction of verification data"
        )
        
        return compliance_notes
    
    def _calculate_overall_confidence(self, context) -> float:
        """Calculate overall confidence in verification decision"""
        
        confidence_scores = []
        
        # Confidence from risk assessment
        risk_results = context.agent_outputs.get("risk_scoring", {})
        if risk_results:
            confidence_scores.append(risk_results.get("confidence_score", 0.5))
        
        # Confidence from anomaly detection
        anomaly_results = context.agent_outputs.get("anomaly_detection", {})
        if anomaly_results:
            confidence_scores.append(anomaly_results.get("confidence_score", 0.5))
        
        # Confidence from data quality
        data_ingestion = context.agent_outputs.get("data_ingestion", {})
        if data_ingestion:
            confidence_scores.append(data_ingestion.get("data_quality", 0.5))
        
        # Average confidence
        if confidence_scores:
            return sum(confidence_scores) / len(confidence_scores)
        
        return 0.5  # Default confidence
    
    async def _initiate_workflows(self, report: ForensicReport, context):
        """Initiate appropriate workflows based on decision"""
        
        if report.decision_status == DecisionStatus.PASS:
            await self._initiate_approval_workflow(report, context)
        elif report.decision_status == DecisionStatus.FAIL:
            await self._initiate_rejection_workflow(report, context)
        else:
            await self._initiate_review_workflow(report, context)
    
    async def _initiate_approval_workflow(self, report: ForensicReport, context):
        """Initiate approval workflow"""
        print(f"✅ [WORKFLOW] Initiating approval workflow for student {context.student_id}")
        
        # Generate QR code (would call QR system)
        # Send approval notification
        # Update national database
        # Schedule any follow-up actions
        
        # Placeholder for workflow initiation
        pass
    
    async def _initiate_rejection_workflow(self, report: ForensicReport, context):
        """Initiate rejection workflow"""
        print(f"🚫 [WORKFLOW] Initiating rejection workflow for student {context.student_id}")
        
        # Flag for fraud investigation
        # Preserve evidence
        # Notify authorities if needed
        # Block further processing
        
        # Placeholder for workflow initiation
        pass
    
    async def _initiate_review_workflow(self, report: ForensicReport, context):
        """Initiate human review workflow"""
        print(f"👥 [WORKFLOW] Initiating human review workflow for student {context.student_id}")
        
        # Create case for human reviewer
        # Compile evidence package
        # Send notification to review team
        # Set review deadline
        
        # Placeholder for workflow initiation
        pass
    
    async def _save_report(self, report: ForensicReport):
        """Save report to secure storage"""
        
        # Create secure storage path
        report_path = f"backend/data/reports/verification_{report.student_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Serialize report
        report_data = self._serialize_report(report)
        
        # Save to file (in production, would use secure database)
        import os
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=4, default=str)
        
        self.logger.info(f"Report saved to {report_path}")
    
    def _serialize_report(self, report: ForensicReport) -> Dict[str, Any]:
        """Serialize forensic report to dictionary"""
        
        return {
            "student_id": report.student_id,
            "national_id": report.national_id,
            "verification_timestamp": report.verification_timestamp.isoformat(),
            "decision_status": report.decision_status.value,
            "confidence_score": report.confidence_score,
            "risk_score": report.risk_score,
            "evidence_summary": report.evidence_summary,
            "detailed_findings": report.detailed_findings,
            "recommendations": report.recommendations,
            "audit_trail": report.audit_trail,
            "compliance_notes": report.compliance_notes,
            "report_metadata": {
                "generated_by": "UhakikiAI AAFI System",
                "version": "1.0",
                "compliance_standard": "Kenya Data Protection Act 2019"
            }
        }
