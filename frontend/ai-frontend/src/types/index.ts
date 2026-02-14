export interface VerificationResult {
  tracking_id: string
  timestamp: string
  student_id: string
  national_id: string
  verification_results: {
    document_analysis: DocumentAnalysis
    biometric_analysis: BiometricAnalysis
    data_ingestion: DataIngestion
    aafi_decision: AAFIDecision
  }
  final_verdict: 'PASS' | 'FAIL' | 'REQUIRES_HUMAN_REVIEW'
  confidence_score: number
  risk_score: number
  compliance_status: 'COMPLIANT' | 'REVIEW_REQUIRED'
}

export interface DocumentAnalysis {
  forgery_probability: number
  ela_status: string
  neural_anomaly: string
  judgment: string
  visuals: {
    original: string
    ela_map: string
    reconstruction: string
  }
}

export interface BiometricAnalysis {
  face_verification: {
    face_detected: boolean
    match_confidence: number
    verified: boolean
    encoding_quality: string
  }
  voice_verification: {
    success: boolean
    verified: boolean
    match_score: number
    quality_score: number
    error?: string
  }
  liveness_verification: {
    liveness_confirmed: boolean
    frames_processed: number
    challenge_type: string
    confidence: number
  }
  overall_biometric_score: number
}

export interface DataIngestion {
  student_id: string
  national_id: string
  ingestion_timestamp: string
  sources: Record<string, any>
  data_quality: number
  completeness: number
  errors: Array<{ source: string; error: string }>
}

export interface AAFIDecision {
  verdict: string
  confidence: number
  risk_score: number
  cycles_completed: number
  report: {
    student_id: string
    decision_status: string
    confidence_score: number
    risk_score: number
    evidence_summary: EvidenceSummary
    detailed_findings: string[]
    recommendations: string[]
    audit_trail: AuditEntry[]
    compliance_notes: string[]
  }
}

export interface EvidenceSummary {
  document_analysis: Record<string, any>
  biometric_analysis: Record<string, any>
  external_data: Record<string, any>
  anomaly_detection: Record<string, any>
  risk_assessment: Record<string, any>
}

export interface AuditEntry {
  timestamp: string
  action: string
  actor: string
  details: string
  data: Record<string, any>
}

export interface DashboardMetrics {
  total_verifications: number
  fraud_prevented: number
  shillings_saved: number
  average_risk_score: number
  processing_time: number
  system_health: number
}

export interface FraudTrend {
  date: string
  fraud_attempts: number
  fraud_prevented: number
  risk_score: number
}

export interface GeographicHotspot {
  county: string
  constituency: string
  risk_score: number
  fraud_cases: number
  lat: number
  lng: number
}

export interface FraudRing {
  id: string
  name: string
  members: number
  detected_date: string
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  total_fraud_amount: number
  status: 'active' | 'investigating' | 'disrupted'
  patterns: string[]
}

export interface HumanReviewCase {
  id: string
  student_id: string
  national_id: string
  risk_score: number
  priority: 'low' | 'medium' | 'high' | 'critical'
  assigned_to?: string
  created_at: string
  status: 'pending' | 'in_review' | 'completed'
  notes: string[]
}

export interface SystemAlert {
  id: string
  type: 'system' | 'security' | 'performance' | 'compliance'
  severity: 'info' | 'warning' | 'error' | 'critical'
  title: string
  message: string
  timestamp: string
  resolved: boolean
}

export interface EconomicImpact {
  period: string
  total_funding: number
  fraud_prevented: number
  savings_percentage: number
  students_verified: number
  processing_efficiency: number
}

export interface RealTimeStats {
  active_verifications: number
  queue_length: number
  average_processing_time: number
  system_load: number
  error_rate: number
  throughput: number
}
