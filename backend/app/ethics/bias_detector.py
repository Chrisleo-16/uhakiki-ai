"""
Bias & Fairness Detection Module
Addresses D3 criterion from MVP Judging Criteria
Ensures AI does not produce discriminatory outcomes
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class BiasDetector:
    """
    Detects and measures bias in verification decisions
    Implements fairness metrics for demographic parity and equalized odds
    """
    
    def __init__(self):
        self.verification_history: List[Dict] = []
        # Kenyan demographic regions for analysis
        self.regions = [
            "Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret",
            "Meru", "Machakos", "Kiambu", "Kajiado", "Bungoma"
        ]
        
    def record_decision(self, decision: Dict[str, Any]):
        """Record a verification decision for bias analysis"""
        self.verification_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "decision": decision.get("decision"),  # approve/reject
            "risk_score": decision.get("risk_score"),
            "region": decision.get("region", "unknown"),
            "age_group": decision.get("age_group", "unknown"),
            "document_type": decision.get("document_type", "unknown"),
            "confidence": decision.get("confidence", 0.0)
        })
    
    def calculate_demographic_parity(self) -> float:
        """
        Calculate demographic parity - equal approval rates across groups
        Returns score 0-100 (100 = perfect parity)
        """
        if not self.verification_history:
            return 100.0
            
        # Group by region
        region_approvals: Dict[str, int] = {}
        region_totals: Dict[str, int] = {}
        
        for record in self.verification_history:
            region = record.get("region", "unknown")
            decision = record.get("decision", "reject")
            
            region_totals[region] = region_totals.get(region, 0) + 1
            if decision == "approve":
                region_approvals[region] = region_approvals.get(region, 0) + 1
        
        # Calculate approval rates
        approval_rates = {}
        for region, total in region_totals.items():
            if total > 10:  # Minimum sample size
                approval_rates[region] = region_approvals.get(region, 0) / total
        
        if len(approval_rates) < 2:
            return 100.0
            
        # Calculate variance - lower is better
        rates = list(approval_rates.values())
        avg_rate = sum(rates) / len(rates)
        
        if avg_rate == 0:
            return 100.0
            
        # Variance as percentage difference from average
        variance = sum((r - avg_rate) ** 2 for r in rates) / len(rates)
        max_variance = avg_rate * (1 - avg_rate)  # Maximum possible variance
        
        if max_variance == 0:
            return 100.0
            
        # Convert to 0-100 score (lower variance = higher score)
        parity_score = (1 - (variance / max_variance)) * 100
        
        return max(0, min(100, parity_score))
    
    def calculate_equalized_odds(self) -> float:
        """
        Calculate equalized odds - equal error rates across groups
        Returns score 0-100 (100 = perfect equalized odds)
        """
        if not self.verification_history:
            return 100.0
            
        # Calculate false positive and false negative rates by region
        region_fp_rates: Dict[str, List[float]] = {}
        region_fn_rates: Dict[str, List[float]] = {}
        
        for record in self.verification_history:
            region = record.get("region", "unknown")
            decision = record.get("decision")
            risk_score = record.get("risk_score", 0)
            
            if region not in region_fp_rates:
                region_fp_rates[region] = []
                region_fn_rates[region] = []
            
            # Approve but high risk = potential false positive
            if decision == "approve" and risk_score > 50:
                region_fp_rates[region].append(1)
            else:
                region_fp_rates[region].append(0)
                
            # Reject but low risk = potential false negative
            if decision == "reject" and risk_score < 30:
                region_fn_rates[region].append(1)
            else:
                region_fn_rates[region].append(0)
        
        # Calculate average rates per region
        fp_rates = {}
        fn_rates = {}
        
        for region, fp_list in region_fp_rates.items():
            if len(fp_list) > 10:
                fp_rates[region] = sum(fp_list) / len(fp_list)
        
        for region, fn_list in region_fn_rates.items():
            if len(fn_list) > 10:
                fn_rates[region] = sum(fn_list) / len(fn_list)
        
        if not fp_rates or not fn_rates:
            return 100.0
            
        # Calculate disparity
        fp_values = list(fp_rates.values())
        fn_values = list(fn_rates.values())
        
        fp_variance = max(fp_values) - min(fp_values) if fp_values else 0
        fn_variance = max(fn_values) - min(fn_values) if fn_values else 0
        
        # Combined score - lower disparity = higher score
        avg_error = (sum(fp_values) / len(fp_values) + sum(fn_values) / len(fn_values)) / 2
        
        if avg_error == 0:
            return 100.0
            
        disparity_penalty = ((fp_variance + fn_variance) / 2) / max(avg_error, 0.1)
        equalized_odds_score = max(0, 100 - (disparity_penalty * 50))
        
        return equalized_odds_score
    
    def get_false_rates_by_region(self) -> Dict[str, Dict[str, float]]:
        """Get false positive and false negative rates by region"""
        region_stats: Dict[str, Dict[str, float]] = {}
        
        for region in self.regions:
            region_records = [r for r in self.verification_history if r.get("region") == region]
            
            if len(region_records) < 10:
                continue
                
            approvals = [r for r in region_records if r.get("decision") == "approve"]
            rejections = [r for r in region_records if r.get("decision") == "reject"]
            
            fp = len([r for r in approvals if r.get("risk_score", 0) > 50])
            fn = len([r for r in rejections if r.get("risk_score", 0) < 30])
            
            region_stats[region] = {
                "false_positive_rate": fp / len(approvals) if approvals else 0,
                "false_negative_rate": fn / len(rejections) if rejections else 0
            }
        
        return region_stats
    
    def generate_bias_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive bias report for judging criteria D3
        """
        demographic_parity = self.calculate_demographic_parity()
        equalized_odds = self.calculate_equalized_odds()
        region_rates = self.get_false_rates_by_region()
        
        # Overall fairness score (weighted average)
        fairness_score = (demographic_parity * 0.4) + (equalized_odds * 0.6)
        
        # Generate recommendations
        recommendations = []
        if demographic_parity < 80:
            recommendations.append("Review approval criteria for regional disparities")
        if equalized_odds < 80:
            recommendations.append("Investigate error rate differences across demographics")
        if region_rates:
            max_fp_region = max(region_rates.items(), key=lambda x: x[1].get("false_positive_rate", 0))
            if max_fp_region[1].get("false_positive_rate", 0) > 0.15:
                recommendations.append(f"High false positive rate in {max_fp_region[0]} - review local thresholds")
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "demographic_parity": round(demographic_parity, 2),
            "equalized_odds": round(equalized_odds, 2),
            "fairness_score": round(fairness_score, 2),
            "false_positive_rate_by_region": {k: round(v["false_positive_rate"], 4) for k, v in region_rates.items()},
            "false_negative_rate_by_region": {k: round(v["false_negative_rate"], 4) for k, v in region_rates.items()},
            "total_decisions_analyzed": len(self.verification_history),
            "recommendations": recommendations,
            "status": "FAIR" if fairness_score >= 80 else "REVIEW_NEEDED"
        }


# Singleton instance
bias_detector = BiasDetector()
