"""
Risk Scoring Agent - Implements Dynamic Bayesian Network for Fraud Risk Assessment
Synthesizes evidence from all verification components into unified risk score
"""

import numpy as np
import json
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import math

from crewai import Agent, Task, LLM


class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM" 
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class RiskFactors:
    """Structured risk factors for Bayesian analysis"""
    document_integrity: float  # 0-1, higher = more suspicious
    biometric_match: float     # 0-1, higher = better match
    liveness_confidence: float # 0-1, higher = more confident
    historical_patterns: float  # 0-1, higher = more suspicious
    geographic_risk: float     # 0-1, higher = higher risk
    behavioral_anomalies: float # 0-1, higher = more anomalies


class BayesianRiskEngine:
    """
    Dynamic Bayesian Network for risk assessment
    Calculates conditional probabilities based on multiple evidence sources
    """
    
    def __init__(self):
        # Prior probabilities (based on historical fraud data)
        self.priors = {
            "document_fraud": 0.15,    # 15% baseline document fraud rate
            "identity_fraud": 0.08,     # 8% baseline identity fraud rate  
            "biometric_spoof": 0.05,   # 5% baseline biometric spoof rate
            "overall_fraud": 0.12      # 12% baseline overall fraud rate
        }
        
        # Conditional probability tables (simplified for implementation)
        # P(evidence | fraud_true) vs P(evidence | fraud_false)
        self.conditional_probs = {
            "high_mse": {"fraud": 0.85, "no_fraud": 0.15},
            "low_face_match": {"fraud": 0.78, "no_fraud": 0.22},
            "failed_liveness": {"fraud": 0.92, "no_fraud": 0.08},
            "duplicate_pattern": {"fraud": 0.88, "no_fraud": 0.12},
            "high_risk_location": {"fraud": 0.65, "no_fraud": 0.35},
            "behavioral_anomaly": {"fraud": 0.73, "no_fraud": 0.27}
        }
    
    def calculate_posterior(self, evidence: Dict[str, bool]) -> float:
        """
        Calculate posterior probability using Bayes' theorem
        P(fraud | evidence) = P(evidence | fraud) * P(fraud) / P(evidence)
        """
        prior_fraud = self.priors["overall_fraud"]
        prior_no_fraud = 1 - prior_fraud
        
        # Calculate likelihood of evidence given fraud and no fraud
        likelihood_fraud = 1.0
        likelihood_no_fraud = 1.0
        
        for evidence_type, present in evidence.items():
            if evidence_type in self.conditional_probs:
                probs = self.conditional_probs[evidence_type]
                if present:
                    likelihood_fraud *= probs["fraud"]
                    likelihood_no_fraud *= probs["no_fraud"]
                else:
                    # Evidence not present - use complementary probabilities
                    likelihood_fraud *= (1 - probs["fraud"])
                    likelihood_no_fraud *= (1 - probs["no_fraud"])
        
        # Calculate evidence probability (normalization constant)
        evidence_prob = likelihood_fraud * prior_fraud + likelihood_no_fraud * prior_no_fraud
        
        # Calculate posterior
        if evidence_prob > 0:
            posterior = (likelihood_fraud * prior_fraud) / evidence_prob
        else:
            posterior = prior_fraud  # Fallback to prior
        
        return min(posterior, 1.0)



    
    async def _fetch_real_data(self, context) -> Dict[str, Any]:
        """Fetch real data from Kenyan institutions"""
        print(f"📡 [DATA] Fetching real data for student {context.student_id}")
        
        # Real API calls to Kenyan institutions
        real_data = {
            "student_id": context.student_id,
            "national_id": context.national_id,
            "ingestion_timestamp": datetime.now().isoformat(),
            "sources": {},
            "data_quality": 0.0,
            "completeness": 0.0,
            "errors": []
        }
        
        # HELB API integration
        try:
            helb_data = await self._fetch_helb_data(context.national_id)
            if helb_data:
                real_data["sources"]["HELB"] = helb_data
        except Exception as e:
            real_data["errors"].append(f"HELB API error: {e}")
        
        # KUCCPS API integration
        try:
            kuccps_data = await self._fetch_kuccps_data(context.national_id)
            if kuccps_data:
                real_data["sources"]["KUCCPS"] = kuccps_data
        except Exception as e:
            real_data["errors"].append(f"KUCCPS API error: {e}")
        
        # NEMIS API integration
        try:
            nemis_data = await self._fetch_nemis_data(context.national_id)
            if nemis_data:
                real_data["sources"]["NEMIS"] = nemis_data
        except Exception as e:
            real_data["errors"].append(f"NEMIS API error: {e}")
        
        # Calculate data quality metrics
        real_data["data_quality"] = self._calculate_real_data_quality(real_data["sources"])
        real_data["completeness"] = self._calculate_completeness(real_data["sources"])
        
        return real_data
    
    async def _fetch_helb_data(self, national_id: str) -> Dict[str, Any]:
        """Fetch real HELB loan data"""
        # Integration with HELB API
        # This would connect to the actual HELB system
        pass
    
    async def _fetch_kuccps_data(self, national_id: str) -> Dict[str, Any]:
        """Fetch real KUCCPS placement data"""
        # Integration with KUCCPS API
        # This would connect to the actual KUCCPS system
        pass
    
    async def _fetch_nemis_data(self, national_id: str) -> Dict[str, Any]:
        """Fetch real NEMIS academic data"""
        # Integration with NEMIS API
        # This would connect to the actual NEMIS system
        pass


    
    async def _fetch_real_data(self, context) -> Dict[str, Any]:
        """Fetch real data from Kenyan institutions"""
        print(f"📡 [DATA] Fetching real data for student {context.student_id}")
        
        # Real API calls to Kenyan institutions
        real_data = {
            "student_id": context.student_id,
            "national_id": context.national_id,
            "ingestion_timestamp": datetime.now().isoformat(),
            "sources": {},
            "data_quality": 0.0,
            "completeness": 0.0,
            "errors": []
        }
        
        # HELB API integration
        try:
            helb_data = await self._fetch_helb_data(context.national_id)
            if helb_data:
                real_data["sources"]["HELB"] = helb_data
        except Exception as e:
            real_data["errors"].append(f"HELB API error: {e}")
        
        # KUCCPS API integration
        try:
            kuccps_data = await self._fetch_kuccps_data(context.national_id)
            if kuccps_data:
                real_data["sources"]["KUCCPS"] = kuccps_data
        except Exception as e:
            real_data["errors"].append(f"KUCCPS API error: {e}")
        
        # NEMIS API integration
        try:
            nemis_data = await self._fetch_nemis_data(context.national_id)
            if nemis_data:
                real_data["sources"]["NEMIS"] = nemis_data
        except Exception as e:
            real_data["errors"].append(f"NEMIS API error: {e}")
        
        # Calculate data quality metrics
        real_data["data_quality"] = self._calculate_real_data_quality(real_data["sources"])
        real_data["completeness"] = self._calculate_completeness(real_data["sources"])
        
        return real_data
    
    async def _fetch_helb_data(self, national_id: str) -> Dict[str, Any]:
        """Fetch real HELB loan data"""
        # Integration with HELB API
        # This would connect to the actual HELB system
        pass
    
    async def _fetch_kuccps_data(self, national_id: str) -> Dict[str, Any]:
        """Fetch real KUCCPS placement data"""
        # Integration with KUCCPS API
        # This would connect to the actual KUCCPS system
        pass
    
    async def _fetch_nemis_data(self, national_id: str) -> Dict[str, Any]:
        """Fetch real NEMIS academic data"""
        # Integration with NEMIS API
        # This would connect to the actual NEMIS system
        pass


    
    async def _fetch_real_data(self, context) -> Dict[str, Any]:
        """Fetch real data from Kenyan institutions"""
        print(f"📡 [DATA] Fetching real data for student {context.student_id}")
        
        # Real API calls to Kenyan institutions
        real_data = {
            "student_id": context.student_id,
            "national_id": context.national_id,
            "ingestion_timestamp": datetime.now().isoformat(),
            "sources": {},
            "data_quality": 0.0,
            "completeness": 0.0,
            "errors": []
        }
        
        # HELB API integration
        try:
            helb_data = await self._fetch_helb_data(context.national_id)
            if helb_data:
                real_data["sources"]["HELB"] = helb_data
        except Exception as e:
            real_data["errors"].append(f"HELB API error: {e}")
        
        # KUCCPS API integration
        try:
            kuccps_data = await self._fetch_kuccps_data(context.national_id)
            if kuccps_data:
                real_data["sources"]["KUCCPS"] = kuccps_data
        except Exception as e:
            real_data["errors"].append(f"KUCCPS API error: {e}")
        
        # NEMIS API integration
        try:
            nemis_data = await self._fetch_nemis_data(context.national_id)
            if nemis_data:
                real_data["sources"]["NEMIS"] = nemis_data
        except Exception as e:
            real_data["errors"].append(f"NEMIS API error: {e}")
        
        # Calculate data quality metrics
        real_data["data_quality"] = self._calculate_real_data_quality(real_data["sources"])
        real_data["completeness"] = self._calculate_completeness(real_data["sources"])
        
        return real_data
    
    async def _fetch_helb_data(self, national_id: str) -> Dict[str, Any]:
        """Fetch real HELB loan data"""
        # Integration with HELB API
        # This would connect to the actual HELB system
        pass
    
    async def _fetch_kuccps_data(self, national_id: str) -> Dict[str, Any]:
        """Fetch real KUCCPS placement data"""
        # Integration with KUCCPS API
        # This would connect to the actual KUCCPS system
        pass
    
    async def _fetch_nemis_data(self, national_id: str) -> Dict[str, Any]:
        """Fetch real NEMIS academic data"""
        # Integration with NEMIS API
        # This would connect to the actual NEMIS system
        pass

class RiskScoringAgent:
    """
    Specialized agent for comprehensive risk assessment
    Integrates multiple evidence sources into unified fraud risk score
    """
    
    def __init__(self, llm: LLM):
        self.llm = llm
        self.bayesian_engine = BayesianRiskEngine()
        self.risk_weights = {
            "document_integrity": 0.30,
            "biometric_match": 0.25,
            "liveness_confidence": 0.20,
            "historical_patterns": 0.15,
            "geographic_risk": 0.05,
            "behavioral_anomalies": 0.05
        }
    
    def create_agent(self) -> Agent:
        """Create CrewAI agent for risk scoring"""
        return Agent(
            role='Risk Assessment Specialist',
            goal='Calculate comprehensive fraud risk score using Bayesian analysis',
            backstory="""You are a quantitative risk analyst specializing in identity fraud detection.
            You use statistical methods and Bayesian networks to synthesize multiple evidence sources
            into accurate risk assessments. Your analysis is always mathematically sound and evidence-based.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
    
    async def calculate_risk_score(self, context) -> Dict[str, Any]:
        """
        Main risk calculation method
        Combines Bayesian analysis with weighted scoring
        """
        print(f"🎯 [RISK] Calculating risk score for student {context.student_id}")
        
        # Extract risk factors from context
        risk_factors = self._extract_risk_factors(context)
        
        # Bayesian analysis
        evidence = self._convert_to_evidence(risk_factors)
        bayesian_risk = self.bayesian_engine.calculate_posterior(evidence)
        
        # Weighted scoring
        weighted_score = self._calculate_weighted_score(risk_factors)
        
        # Combine both approaches
        final_risk_score = (bayesian_risk * 0.6) + (weighted_score * 0.4)
        final_risk_score = min(final_risk_score * 100, 100)  # Convert to 0-100 scale
        
        # Determine risk level
        risk_level = self._determine_risk_level(final_risk_score)
        
        # Generate risk breakdown
        risk_breakdown = {
            "bayesian_probability": bayesian_risk,
            "weighted_score": weighted_score,
            "final_risk_score": final_risk_score,
            "risk_level": risk_level.value,
            "risk_factors": risk_factors,
            "evidence_analysis": evidence,
            "confidence_score": self._calculate_confidence(risk_factors)
        }
        
        # Add recommendations
        risk_breakdown["recommendations"] = self._generate_recommendations(risk_breakdown)
        
        return risk_breakdown
    
    def _extract_risk_factors(self, context) -> RiskFactors:
        """Extract structured risk factors from verification context"""
        
        # Document integrity from forgery detection
        anomaly_results = context.agent_outputs.get("anomaly_detection", {})
        document_risk = anomaly_results.get("anomaly_score", 0.0) / 100.0
        
        # Biometric match quality
        biometric_data = context.biometric_data
        face_match_score = biometric_data.get("face_match_score", 0.5)
        
        # Liveness confidence
        liveness_confidence = biometric_data.get("liveness_confidence", 0.5)
        
        # Historical patterns (placeholder - would query historical database)
        historical_risk = self._analyze_historical_patterns(context)
        
        # Geographic risk (placeholder - would use IP/location data)
        geographic_risk = self._assess_geographic_risk(context)
        
        # Behavioral anomalies
        behavioral_risk = self._detect_behavioral_anomalies(context)
        
        return RiskFactors(
            document_integrity=document_risk,
            biometric_match=1.0 - face_match_score,  # Invert: higher = more risk
            liveness_confidence=1.0 - liveness_confidence,  # Invert: higher = more risk
            historical_patterns=historical_risk,
            geographic_risk=geographic_risk,
            behavioral_anomalies=behavioral_risk
        )
    
    def _convert_to_evidence(self, factors: RiskFactors) -> Dict[str, bool]:
        """Convert risk factors to binary evidence for Bayesian analysis"""
        return {
            "high_mse": factors.document_integrity > 0.15,
            "low_face_match": factors.biometric_match > 0.3,
            "failed_liveness": factors.liveness_confidence > 0.4,
            "duplicate_pattern": factors.historical_patterns > 0.6,
            "high_risk_location": factors.geographic_risk > 0.5,
            "behavioral_anomaly": factors.behavioral_anomalies > 0.5
        }
    
    def _calculate_weighted_score(self, factors: RiskFactors) -> float:
        """Calculate weighted risk score from all factors"""
        score = 0.0
        
        score += factors.document_integrity * self.risk_weights["document_integrity"]
        score += factors.biometric_match * self.risk_weights["biometric_match"]
        score += factors.liveness_confidence * self.risk_weights["liveness_confidence"]
        score += factors.historical_patterns * self.risk_weights["historical_patterns"]
        score += factors.geographic_risk * self.risk_weights["geographic_risk"]
        score += factors.behavioral_anomalies * self.risk_weights["behavioral_anomalies"]
        
        return min(score, 1.0)
    
    def _determine_risk_level(self, score: float) -> RiskLevel:
        """Determine risk category based on score"""
        if score >= 85:
            return RiskLevel.CRITICAL
        elif score >= 60:
            return RiskLevel.HIGH
        elif score >= 30:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _calculate_confidence(self, factors: RiskFactors) -> float:
        """Calculate confidence in risk assessment"""
        # Higher confidence when all factors provide clear signals
        factor_clarity = 0.0
        
        # Check if factors are consistently high or low
        factor_values = [
            factors.document_integrity,
            factors.biometric_match,
            factors.liveness_confidence,
            factors.historical_patterns,
            factors.geographic_risk,
            factors.behavioral_anomalies
        ]
        
        # Calculate variance - lower variance = higher confidence
        variance = np.var(factor_values)
        confidence = max(0.5, 1.0 - variance)
        
        return confidence
    
    def _analyze_historical_patterns(self, context) -> float:
        """Analyze historical verification patterns"""
        # Placeholder implementation
        # In production, would query database for similar patterns
        verification_history = context.verification_history
        
        if not verification_history:
            return 0.1  # Low risk for new applicants
        
        # Check for suspicious patterns in history
        suspicious_indicators = 0
        for record in verification_history:
            if record.get("flags", 0) > 2:
                suspicious_indicators += 1
        
        return min(suspicious_indicators / len(verification_history), 1.0)
    
    def _assess_geographic_risk(self, context) -> float:
        """Assess risk based on geographic factors"""
        # Placeholder implementation
        # In production, would use IP geolocation, known fraud hotspots
        return 0.1  # Default low risk
    
    def _detect_behavioral_anomalies(self, context) -> float:
        """Detect behavioral anomalies during verification"""
        # Placeholder implementation
        # In production, would analyze interaction patterns, timing, etc.
        return 0.1  # Default low risk
    
    def _generate_recommendations(self, risk_breakdown: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on risk assessment"""
        recommendations = []
        risk_level = risk_breakdown["risk_level"]
        score = risk_breakdown["final_risk_score"]
        
        if risk_level == RiskLevel.CRITICAL.value:
            recommendations.extend([
                "IMMEDIATE MANUAL REVIEW REQUIRED",
                "Block further processing until human verification",
                "Flag for potential fraud investigation"
            ])
        elif risk_level == RiskLevel.HIGH.value:
            recommendations.extend([
                "Enhanced verification procedures recommended",
                "Additional documentation required",
                "Consider video call verification"
            ])
        elif risk_level == RiskLevel.MEDIUM.value:
            recommendations.extend([
                "Standard verification with additional checks",
                "Monitor for anomalous patterns"
            ])
        else:
            recommendations.extend([
                "Proceed with standard verification",
                "No additional measures required"
            ])
        
        # Specific factor-based recommendations
        factors = risk_breakdown["risk_factors"]
        if factors["document_integrity"] > 0.2:
            recommendations.append("Document appears manipulated - request original")
        
        if factors["biometric_match"] > 0.3:
            recommendations.append("Biometric mismatch - verify identity documents")
        
        if factors["liveness_confidence"] > 0.4:
            recommendations.append("Liveness detection failed - require live verification")
        
        return recommendations
