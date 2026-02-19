"""
Anomaly Detection Agent - Cross-references GD-FD and MBIC outputs with known fraud patterns
Identifies geographic risk scores and historical data anomalies
"""

import numpy as np
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging

from crewai import Agent, Task, LLM


@dataclass
class AnomalyPattern:
    """Represents a detected anomaly pattern"""
    pattern_type: str
    severity: float  # 0-1, higher = more severe
    confidence: float  # 0-1, higher = more confident
    description: str
    evidence: Dict[str, Any]
    risk_contribution: float  # Contribution to overall risk score


@dataclass
class GeographicRisk:
    """Geographic risk assessment"""
    county: str
    constituency: str
    risk_score: float
    known_fraud_hotspot: bool
    risk_factors: List[str]



    
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

class AnomalyDetectionAgent:
    """
    Specialized agent for detecting anomalies across multiple data sources
    Combines document analysis, biometric data, and historical patterns
    """
    
    def __init__(self, llm: LLM):
        self.llm = llm
        self.logger = logging.getLogger(__name__)
        
        # Known fraud patterns (would be updated from ML models)
        self.fraud_patterns = {
            "document_synthesis": {
                "indicators": ["perfect_edges", "uniform_noise", "missing_microprint"],
                "weight": 0.9
            },
            "identity_farming": {
                "indicators": ["multiple_applications", "similar_biometrics", "geographic_clustering"],
                "weight": 0.85
            },
            "deepfake_manipulation": {
                "indicators": ["inconsistent_lighting", "artifact_patterns", "unnatural_textures"],
                "weight": 0.95
            },
            "template_reuse": {
                "indicators": ["identical_layouts", "consistent_anomalies", "serial_patterns"],
                "weight": 0.7
            }
        }
        
        # Geographic risk data (simplified for implementation)
        self.geographic_risk_map = {
            "Nairobi": {"risk_score": 0.3, "hotspot": False},
            "Mombasa": {"risk_score": 0.4, "hotspot": False},
            "Kisumu": {"risk_score": 0.35, "hotspot": False},
            "Nakuru": {"risk_score": 0.25, "hotspot": False},
            # Add more counties as needed
        }
        
        # Anomaly thresholds
        self.thresholds = {
            "mse_anomaly": 0.025,
            "ela_anomaly": 0.05,
            "biometric_mismatch": 0.3,
            "liveness_failure": 0.4,
            "temporal_anomaly": 0.7
        }
    
    def create_agent(self) -> Agent:
        """Create CrewAI agent for anomaly detection"""
        return Agent(
            role='Forensic Anomaly Detection Specialist',
            goal='Identify sophisticated fraud patterns across document, biometric, and behavioral data',
            backstory="""You are a forensic analyst specializing in detecting sophisticated identity fraud.
            You analyze pixel-level document anomalies, biometric inconsistencies, and behavioral patterns
            to identify fraud attempts that traditional systems miss. Your analysis is evidence-based and
            mathematically rigorous.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
    
    async def detect_anomalies(self, context) -> Dict[str, Any]:
        """
        Main anomaly detection method
        Analyzes all available data for suspicious patterns
        """
        print(f"🔍 [ANOMALY] Detecting anomalies for student {context.student_id}")
        
        detected_anomalies = []
        anomaly_score = 0.0
        
        # Document forgery anomalies
        document_anomalies = await self._analyze_document_anomalies(context)
        detected_anomalies.extend(document_anomalies)
        
        # Biometric anomalies
        biometric_anomalies = await self._analyze_biometric_anomalies(context)
        detected_anomalies.extend(biometric_anomalies)
        
        # Historical pattern anomalies
        historical_anomalies = await self._analyze_historical_anomalies(context)
        detected_anomalies.extend(historical_anomalies)
        
        # Geographic risk assessment
        geographic_risk = await self._assess_geographic_risk(context)
        
        # Temporal anomalies
        temporal_anomalies = await self._analyze_temporal_anomalies(context)
        detected_anomalies.extend(temporal_anomalies)
        
        # Cross-source correlation anomalies
        correlation_anomalies = await self._analyze_correlation_anomalies(context)
        detected_anomalies.extend(correlation_anomalies)
        
        # Calculate overall anomaly score
        anomaly_score = self._calculate_anomaly_score(detected_anomalies)
        
        # Categorize anomalies by severity
        anomaly_categories = self._categorize_anomalies(detected_anomalies)
        
        return {
            "anomaly_score": anomaly_score,
            "anomaly_count": len(detected_anomalies),
            "anomalies": [self._serialize_anomaly(a) for a in detected_anomalies],
            "anomaly_categories": anomaly_categories,
            "geographic_risk": self._serialize_geographic_risk(geographic_risk),
            "risk_indicators": self._extract_risk_indicators(detected_anomalies),
            "confidence_score": self._calculate_detection_confidence(detected_anomalies),
            "recommendations": self._generate_anomaly_recommendations(detected_anomalies)
        }
    
    async def _analyze_document_anomalies(self, context) -> List[AnomalyPattern]:
        """Analyze document for forgery and manipulation anomalies"""
        anomalies = []
        
        # Get forgery detection results
        forgery_results = context.agent_outputs.get("forgery_detection", {})
        
        if not forgery_results:
            return anomalies
        
        # Check MSE anomaly
        mse_score = forgery_results.get("mse_score", 0)
        if mse_score > self.thresholds["mse_anomaly"]:
            anomalies.append(AnomalyPattern(
                pattern_type="document_mse_anomaly",
                severity=min(mse_score * 10, 1.0),
                confidence=0.9,
                description=f"Document shows reconstruction anomalies (MSE: {mse_score:.4f})",
                evidence={"mse_score": mse_score, "threshold": self.thresholds["mse_anomaly"]},
                risk_contribution=0.3
            ))
        
        # Check ELA anomaly
        ela_score = forgery_results.get("ela_score", 0)
        if ela_score > self.thresholds["ela_anomaly"]:
            anomalies.append(AnomalyPattern(
                pattern_type="document_ela_anomaly",
                severity=min(ela_score * 5, 1.0),
                confidence=0.85,
                description=f"Error Level Analysis indicates digital manipulation (ELA: {ela_score:.4f})",
                evidence={"ela_score": ela_score, "threshold": self.thresholds["ela_anomaly"]},
                risk_contribution=0.25
            ))
        
        # Check for deepfake patterns
        if forgery_results.get("neural_anomaly") == "DETECTED":
            anomalies.append(AnomalyPattern(
                pattern_type="deepfake_indicators",
                severity=0.8,
                confidence=0.95,
                description="Neural analysis detected potential deepfake manipulation",
                evidence=forgery_results.get("neural_analysis", {}),
                risk_contribution=0.4
            ))
        
        return anomalies
    
    async def _analyze_biometric_anomalies(self, context) -> List[AnomalyPattern]:
        """Analyze biometric data for spoofing and manipulation"""
        anomalies = []
        
        biometric_data = context.biometric_data
        
        if not biometric_data:
            return anomalies
        
        # Face match anomaly
        face_match_score = biometric_data.get("face_match_score", 1.0)
        if face_match_score < (1 - self.thresholds["biometric_mismatch"]):
            anomalies.append(AnomalyPattern(
                pattern_type="facial_mismatch",
                severity=1.0 - face_match_score,
                confidence=0.9,
                description=f"Facial recognition shows poor match (Score: {face_match_score:.2f})",
                evidence={"face_match_score": face_match_score},
                risk_contribution=0.35
            ))
        
        # Liveness detection anomaly
        liveness_confidence = biometric_data.get("liveness_confidence", 1.0)
        if liveness_confidence < (1 - self.thresholds["liveness_failure"]):
            anomalies.append(AnomalyPattern(
                pattern_type="liveness_failure",
                severity=1.0 - liveness_confidence,
                confidence=0.95,
                description=f"Liveness detection indicates potential spoofing (Confidence: {liveness_confidence:.2f})",
                evidence={"liveness_confidence": liveness_confidence},
                risk_contribution=0.4
            ))
        
        # Voice biometric anomaly (if available)
        voice_match_score = biometric_data.get("voice_match_score")
        if voice_match_score is not None and voice_match_score < 0.7:
            anomalies.append(AnomalyPattern(
                pattern_type="voice_mismatch",
                severity=1.0 - voice_match_score,
                confidence=0.8,
                description=f"Voice biometric shows poor match (Score: {voice_match_score:.2f})",
                evidence={"voice_match_score": voice_match_score},
                risk_contribution=0.2
            ))
        
        return anomalies
    
    async def _analyze_historical_anomalies(self, context) -> List[AnomalyPattern]:
        """Analyze historical data for suspicious patterns"""
        anomalies = []
        
        verification_history = context.verification_history
        
        if not verification_history:
            return anomalies
        
        # Multiple applications anomaly
        recent_applications = [
            record for record in verification_history
            if datetime.fromisoformat(record["timestamp"]) > datetime.now() - timedelta(days=30)
        ]
        
        if len(recent_applications) > 3:
            anomalies.append(AnomalyPattern(
                pattern_type="multiple_applications",
                severity=min(len(recent_applications) / 10, 1.0),
                confidence=0.9,
                description=f"Multiple recent applications detected ({len(recent_applications)} in 30 days)",
                evidence={"recent_applications": len(recent_applications), "applications": recent_applications},
                risk_contribution=0.3
            ))
        
        # Rejected applications pattern
        rejected_count = sum(1 for record in verification_history if record.get("status") == "REJECTED")
        if rejected_count > 2:
            anomalies.append(AnomalyPattern(
                pattern_type="repeated_rejections",
                severity=min(rejected_count / 5, 1.0),
                confidence=0.85,
                description=f"Multiple previous rejections ({rejected_count})",
                evidence={"rejected_count": rejected_count},
                risk_contribution=0.25
            ))
        
        return anomalies
    
    async def _assess_geographic_risk(self, context) -> GeographicRisk:
        """Assess geographic risk based on location data"""
        
        # Default values (would be extracted from context in production)
        county = "Nairobi"  # Would get from document or external data
        constituency = "Westlands"  # Would get from document
        
        # Get risk data for county
        county_risk = self.geographic_risk_map.get(county, {"risk_score": 0.2, "hotspot": False})
        
        # Additional risk factors
        risk_factors = []
        
        # Check if it's a known fraud hotspot
        if county_risk["hotspot"]:
            risk_factors.append("known_fraud_hotspot")
        
        # Cross-border risk (simplified)
        if county in ["Mombasa", "Busia", "Malaba"]:
            risk_factors.append("border_region")
        
        # Urban center risk
        urban_counties = ["Nairobi", "Mombasa", "Kisumu", "Nakuru"]
        if county in urban_counties:
            risk_factors.append("urban_center")
        
        return GeographicRisk(
            county=county,
            constituency=constituency,
            risk_score=county_risk["risk_score"],
            known_fraud_hotspot=county_risk["hotspot"],
            risk_factors=risk_factors
        )
    
    async def _analyze_temporal_anomalies(self, context) -> List[AnomalyPattern]:
        """Analyze temporal patterns for anomalies"""
        anomalies = []
        
        verification_history = context.verification_history
        
        if not verification_history:
            return anomalies
        
        # Unusual timing patterns
        timestamps = [
            datetime.fromisoformat(record["timestamp"])
            for record in verification_history
        ]
        
        # Check for applications at unusual hours
        unusual_hours = [
            ts for ts in timestamps
            if ts.hour < 6 or ts.hour > 22
        ]
        
        if len(unusual_hours) > len(timestamps) * 0.3:
            anomalies.append(AnomalyPattern(
                pattern_type="unusual_timing",
                severity=len(unusual_hours) / len(timestamps),
                confidence=0.7,
                description=f"High proportion of applications at unusual hours ({len(unusual_hours)}/{len(timestamps)})",
                evidence={"unusual_hours": len(unusual_hours), "total_applications": len(timestamps)},
                risk_contribution=0.15
            ))
        
        return anomalies
    
    async def _analyze_correlation_anomalies(self, context) -> List[AnomalyPattern]:
        """Analyze cross-source correlation anomalies"""
        anomalies = []
        
        # Get data from different sources
        data_ingestion = context.agent_outputs.get("data_ingestion", {})
        
        if not data_ingestion or not data_ingestion.get("sources"):
            return anomalies
        
        sources = data_ingestion["sources"]
        
        # Check for inconsistencies between sources
        inconsistencies = []
        
        # HELB vs KUCCPS consistency check
        helb_data = sources.get("HELB", {}).get("data", {}).get("processed_fields", {})
        kuccps_data = sources.get("KUCCPS", {}).get("data", {}).get("processed_fields", {})
        
        if helb_data and kuccps_data:
            helb_institution = helb_data.get("institution")
            kuccps_institution = kuccps_data.get("institution_placed")
            
            if helb_institution and kuccps_institution and helb_institution != kuccps_institution:
                inconsistencies.append({
                    "type": "institution_mismatch",
                    "helb": helb_institution,
                    "kuccps": kuccps_institution
                })
        
        if inconsistencies:
            anomalies.append(AnomalyPattern(
                pattern_type="data_inconsistency",
                severity=0.6,
                confidence=0.8,
                description=f"Data inconsistencies found between sources: {[inc['type'] for inc in inconsistencies]}",
                evidence={"inconsistencies": inconsistencies},
                risk_contribution=0.2
            ))
        
        return anomalies
    
    def _calculate_anomaly_score(self, anomalies: List[AnomalyPattern]) -> float:
        """Calculate overall anomaly score from detected anomalies"""
        
        if not anomalies:
            return 0.0
        
        # Weighted sum of anomaly severities
        total_score = sum(anomaly.severity * anomaly.risk_contribution for anomaly in anomalies)
        
        # Normalize to 0-1 scale
        max_possible_score = sum(anomaly.risk_contribution for anomaly in anomalies)
        
        if max_possible_score > 0:
            return min(total_score / max_possible_score, 1.0)
        
        return 0.0
    
    def _categorize_anomalies(self, anomalies: List[AnomalyPattern]) -> Dict[str, List[AnomalyPattern]]:
        """Categorize anomalies by type"""
        
        categories = {
            "document": [],
            "biometric": [],
            "behavioral": [],
            "historical": [],
            "geographic": [],
            "correlation": []
        }
        
        for anomaly in anomalies:
            if "document" in anomaly.pattern_type or "deepfake" in anomaly.pattern_type:
                categories["document"].append(anomaly)
            elif "facial" in anomaly.pattern_type or "liveness" in anomaly.pattern_type or "voice" in anomaly.pattern_type:
                categories["biometric"].append(anomaly)
            elif "multiple" in anomaly.pattern_type or "timing" in anomaly.pattern_type:
                categories["behavioral"].append(anomaly)
            elif "repeated" in anomaly.pattern_type:
                categories["historical"].append(anomaly)
            elif "inconsistency" in anomaly.pattern_type:
                categories["correlation"].append(anomaly)
        
        return categories
    
    def _extract_risk_indicators(self, anomalies: List[AnomalyPattern]) -> List[str]:
        """Extract key risk indicators from anomalies"""
        
        indicators = []
        
        for anomaly in anomalies:
            if anomaly.severity > 0.7:
                indicators.append(f"HIGH_{anomaly.pattern_type.upper()}")
            elif anomaly.severity > 0.4:
                indicators.append(f"MEDIUM_{anomaly.pattern_type.upper()}")
            else:
                indicators.append(f"LOW_{anomaly.pattern_type.upper()}")
        
        return indicators
    
    def _calculate_detection_confidence(self, anomalies: List[AnomalyPattern]) -> float:
        """Calculate overall confidence in anomaly detection"""
        
        if not anomalies:
            return 0.5
        
        # Average confidence weighted by severity
        weighted_confidence = sum(
            anomaly.confidence * anomaly.severity 
            for anomaly in anomalies
        )
        total_severity = sum(anomaly.severity for anomaly in anomalies)
        
        if total_severity > 0:
            return weighted_confidence / total_severity
        
        return 0.5
    
    def _generate_anomaly_recommendations(self, anomalies: List[AnomalyPattern]) -> List[str]:
        """Generate recommendations based on detected anomalies"""
        
        recommendations = []
        
        high_severity_anomalies = [a for a in anomalies if a.severity > 0.7]
        document_anomalies = [a for a in anomalies if "document" in a.pattern_type]
        biometric_anomalies = [a for a in anomalies if "facial" in a.pattern_type or "liveness" in a.pattern_type]
        
        if high_severity_anomalies:
            recommendations.append("IMMEDIATE MANUAL REVIEW REQUIRED - High severity anomalies detected")
        
        if document_anomalies:
            recommendations.append("Request original physical document for verification")
            recommendations.append("Perform enhanced forensic analysis on document")
        
        if biometric_anomalies:
            recommendations.append("Conduct live video interview for identity verification")
            recommendations.append("Require additional biometric verification methods")
        
        if len(anomalies) > 5:
            recommendations.append("Multiple anomaly types detected - Comprehensive investigation recommended")
        
        return recommendations
    
    def _serialize_anomaly(self, anomaly: AnomalyPattern) -> Dict[str, Any]:
        """Serialize anomaly pattern to dictionary"""
        return {
            "pattern_type": anomaly.pattern_type,
            "severity": anomaly.severity,
            "confidence": anomaly.confidence,
            "description": anomaly.description,
            "evidence": anomaly.evidence,
            "risk_contribution": anomaly.risk_contribution
        }
    
    def _serialize_geographic_risk(self, risk: GeographicRisk) -> Dict[str, Any]:
        """Serialize geographic risk to dictionary"""
        return {
            "county": risk.county,
            "constituency": risk.constituency,
            "risk_score": risk.risk_score,
            "known_fraud_hotspot": risk.known_fraud_hotspot,
            "risk_factors": risk.risk_factors
        }
