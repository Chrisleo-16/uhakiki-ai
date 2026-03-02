"use client"

import { useState } from 'react'
import { 
  Shield, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  HelpCircle,
  ChevronDown,
  ChevronUp,
  FileText,
  Fingerprint,
  Eye,
  Mic,
  Globe,
  Clock,
  Activity
} from 'lucide-react'

interface DecisionExplainerProps {
  verdict: 'PASS' | 'FAIL' | 'REVIEW'
  confidence: number
  riskScore: number
  factors: {
    documentAnalysis: {
      forgeryProbability: number
      elaScore: number
      mseScore: number
      status: string
    }
    biometricAnalysis: {
      faceMatch: number
      livenessScore: number
      voiceMatch: number
    }
    dataIngestion: {
      helbMatch: boolean
      kuccpsMatch: boolean
      nemisMatch: boolean
      dataQuality: number
    }
    anomalyIndicators: string[]
  }
  trackingId: string
  timestamp: string
}

/**
 * XAI Component: Explainable AI Decision Panel
 * 
 * This component addresses the MVP criteria D2: Transparency & Explainability
 * It provides human-understandable explanations for why the AI made its decision
 */
export function DecisionExplainer({ 
  verdict, 
  confidence, 
  riskScore, 
  factors,
  trackingId,
  timestamp 
}: DecisionExplainerProps) {
  const [expandedSection, setExpandedSection] = useState<string | null>('overview')

  const getVerdictConfig = () => {
    switch (verdict) {
      case 'PASS':
        return {
          icon: CheckCircle,
          color: 'text-emerald-600',
          bgColor: 'bg-emerald-50',
          borderColor: 'border-emerald-200',
          title: 'Verification Approved',
          description: 'The applicant has been verified as a genuine student.'
        }
      case 'FAIL':
        return {
          icon: XCircle,
          color: 'text-red-600',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          title: 'Verification Failed',
          description: 'The application has been flagged as potentially fraudulent.'
        }
      default:
        return {
          icon: AlertTriangle,
          color: 'text-amber-600',
          bgColor: 'bg-amber-50',
          borderColor: 'border-amber-200',
          title: 'Manual Review Required',
          description: 'This application needs human review due to uncertain risk.'
        }
    }
  }

  const config = getVerdictConfig()
  const VerdictIcon = config.icon

  // Generate human-readable explanation based on factors
  const generateExplanation = () => {
    const explanations: string[] = []

    // Document analysis
    if (factors.documentAnalysis.forgeryProbability > 0.5) {
      explanations.push(`Document analysis detected ${Math.round(factors.documentAnalysis.forgeryProbability * 100)}% probability of forgery.`)
    } else if (factors.documentAnalysis.forgeryProbability < 0.1) {
      explanations.push('Document authenticity confirmed - no forgery indicators detected.')
    }

    // Biometric analysis
    if (factors.biometricAnalysis.livenessScore > 0.7) {
      explanations.push('Liveness verification passed - confirmed live person.')
    } else if (factors.biometricAnalysis.livenessScore < 0.4) {
      explanations.push('Liveness check failed - could not confirm live person.')
    }

    if (factors.biometricAnalysis.faceMatch > 0.8) {
      explanations.push('Face recognition match confirmed - photo matches ID.')
    }

    // Data cross-reference
    const matchedSources = []
    if (factors.dataIngestion.helbMatch) matchedSources.push('HELB')
    if (factors.dataIngestion.kuccpsMatch) matchedSources.push('KUCCPS')
    if (factors.dataIngestion.nemisMatch) matchedSources.push('NEMIS')
    
    if (matchedSources.length > 0) {
      explanations.push(`Data cross-reference successful: ${matchedSources.join(', ')} records matched.`)
    } else {
      explanations.push('Warning: No external database matches found.')
    }

    // Anomalies
    if (factors.anomalyIndicators.length > 0) {
      explanations.push(`${factors.anomalyIndicators.length} anomaly indicator(s) detected requiring attention.`)
    }

    return explanations
  }

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section)
  }

  return (
    <div className="w-full max-w-4xl mx-auto space-y-4">
      {/* Header Card */}
      <div className={`${config.bgColor} ${config.borderColor} border rounded-xl p-6`}>
        <div className="flex items-start gap-4">
          <div className={`p-3 rounded-full ${config.bgColor} border-2 ${config.borderColor}`}>
            <VerdictIcon className={`w-8 h-8 ${config.color}`} />
          </div>
          <div className="flex-1">
            <h2 className={`text-xl font-bold ${config.color}`}>{config.title}</h2>
            <p className="text-slate-600 mt-1">{config.description}</p>
            
            {/* Confidence Meter */}
            <div className="mt-4">
              <div className="flex justify-between text-sm mb-1">
                <span className="font-medium">AI Confidence</span>
                <span className={`font-bold ${
                  confidence >= 85 ? 'text-emerald-600' : 
                  confidence >= 60 ? 'text-amber-600' : 'text-red-600'
                }`}>
                  {confidence.toFixed(1)}%
                </span>
              </div>
              <div className="h-3 bg-slate-200 rounded-full overflow-hidden">
                <div 
                  className={`h-full transition-all duration-500 ${
                    confidence >= 85 ? 'bg-emerald-500' : 
                    confidence >= 60 ? 'bg-amber-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${confidence}%` }}
                />
              </div>
            </div>

            {/* Risk Score */}
            <div className="mt-4 flex items-center gap-2">
              <Activity className="w-4 h-4 text-slate-500" />
              <span className="text-sm text-slate-600">Risk Score:</span>
              <span className={`font-bold ${
                riskScore < 30 ? 'text-emerald-600' :
                riskScore < 60 ? 'text-amber-600' : 'text-red-600'
              }`}>
                {riskScore.toFixed(1)}/100
              </span>
            </div>
          </div>
        </div>

        {/* Tracking Info */}
        <div className="mt-4 pt-4 border-t border-slate-200">
          <div className="flex items-center gap-4 text-xs text-slate-500">
            <span>ID: {trackingId}</span>
            <span>•</span>
            <span>{new Date(timestamp).toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* Human-Readable Explanations */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
        <button 
          onClick={() => toggleSection('overview')}
          className="w-full p-4 flex items-center justify-between hover:bg-slate-50"
        >
          <div className="flex items-center gap-2">
            <HelpCircle className="w-5 h-5 text-blue-600" />
            <span className="font-semibold">Why this decision?</span>
          </div>
          {expandedSection === 'overview' ? (
            <ChevronUp className="w-5 h-5 text-slate-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-slate-400" />
          )}
        </button>
        
        {expandedSection === 'overview' && (
          <div className="px-4 pb-4">
            <ul className="space-y-2">
              {generateExplanation().map((exp, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-slate-700">
                  <span className="text-blue-500 mt-1">•</span>
                  <span>{exp}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Detailed Breakdown Accordions */}
      
      {/* Document Analysis */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
        <button 
          onClick={() => toggleSection('document')}
          className="w-full p-4 flex items-center justify-between hover:bg-slate-50"
        >
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-slate-600" />
            <span className="font-semibold">Document Analysis</span>
            <span className={`text-xs px-2 py-0.5 rounded-full ${
              factors.documentAnalysis.forgeryProbability < 0.3 
                ? 'bg-emerald-100 text-emerald-700' 
                : 'bg-red-100 text-red-700'
            }`}>
              {factors.documentAnalysis.forgeryProbability < 0.3 ? 'PASS' : 'FLAG'}
            </span>
          </div>
          {expandedSection === 'document' ? (
            <ChevronUp className="w-5 h-5 text-slate-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-slate-400" />
          )}
        </button>
        
        {expandedSection === 'document' && (
          <div className="px-4 pb-4 space-y-3">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <div className="text-xs text-slate-500">Forgery Probability</div>
                <div className={`font-bold ${
                  factors.documentAnalysis.forgeryProbability < 0.3 ? 'text-emerald-600' : 'text-red-600'
                }`}>
                  {(factors.documentAnalysis.forgeryProbability * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-500">ELA Score</div>
                <div className="font-medium">{factors.documentAnalysis.elaScore.toFixed(4)}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500">MSE Score</div>
                <div className="font-medium">{factors.documentAnalysis.mseScore.toFixed(4)}</div>
              </div>
            </div>
            <p className="text-sm text-slate-600">
              {factors.documentAnalysis.forgeryProbability < 0.3 
                ? 'Document appears authentic based on neural reconstruction analysis and error level analysis.'
                : 'Document shows signs of manipulation. The neural autoencoder detected reconstruction anomalies.'}
            </p>
          </div>
        )}
      </div>

      {/* Biometric Analysis */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
        <button 
          onClick={() => toggleSection('biometric')}
          className="w-full p-4 flex items-center justify-between hover:bg-slate-50"
        >
          <div className="flex items-center gap-2">
            <Fingerprint className="w-5 h-5 text-slate-600" />
            <span className="font-semibold">Biometric Verification</span>
            <span className={`text-xs px-2 py-0.5 rounded-full ${
              factors.biometricAnalysis.livenessScore > 0.7 
                ? 'bg-emerald-100 text-emerald-700' 
                : 'bg-amber-100 text-amber-700'
            }`}>
              {factors.biometricAnalysis.livenessScore > 0.7 ? 'VERIFIED' : 'CHECK'}
            </span>
          </div>
          {expandedSection === 'biometric' ? (
            <ChevronUp className="w-5 h-5 text-slate-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-slate-400" />
          )}
        </button>
        
        {expandedSection === 'biometric' && (
          <div className="px-4 pb-4 space-y-3">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <div className="text-xs text-slate-500">Face Match</div>
                <div className="font-medium">
                  {(factors.biometricAnalysis.faceMatch * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-500">Liveness Score</div>
                <div className={`font-medium ${
                  factors.biometricAnalysis.livenessScore > 0.7 ? 'text-emerald-600' : 'text-amber-600'
                }`}>
                  {(factors.biometricAnalysis.livenessScore * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-500">Voice Match</div>
                <div className="font-medium">
                  {(factors.biometricAnalysis.voiceMatch * 100).toFixed(1)}%
                </div>
              </div>
            </div>
            <p className="text-sm text-slate-600">
              {factors.biometricAnalysis.livenessScore > 0.7
                ? 'Live person verified through MBIC challenge-response system. Face matches ID photo.'
                : 'Additional verification needed. Please retake liveness challenge.'}
            </p>
          </div>
        )}
      </div>

      {/* Data Cross-Reference */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
        <button 
          onClick={() => toggleSection('data')}
          className="w-full p-4 flex items-center justify-between hover:bg-slate-50"
        >
          <div className="flex items-center gap-2">
            <Globe className="w-5 h-5 text-slate-600" />
            <span className="font-semibold">External Data Cross-Reference</span>
            <span className={`text-xs px-2 py-0.5 rounded-full ${
              factors.dataIngestion.dataQuality > 0.8 
                ? 'bg-emerald-100 text-emerald-700' 
                : 'bg-amber-100 text-amber-700'
            }`}>
              {factors.dataIngestion.dataQuality > 0.8 ? 'MATCHED' : 'PARTIAL'}
            </span>
          </div>
          {expandedSection === 'data' ? (
            <ChevronUp className="w-5 h-5 text-slate-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-slate-400" />
          )}
        </button>
        
        {expandedSection === 'data' && (
          <div className="px-4 pb-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="flex items-center gap-2">
                {factors.dataIngestion.helbMatch ? (
                  <CheckCircle className="w-4 h-4 text-emerald-600" />
                ) : (
                  <XCircle className="w-4 h-4 text-slate-400" />
                )}
                <span className="text-sm">HELB</span>
              </div>
              <div className="flex items-center gap-2">
                {factors.dataIngestion.kuccpsMatch ? (
                  <CheckCircle className="w-4 h-4 text-emerald-600" />
                ) : (
                  <XCircle className="w-4 h-4 text-slate-400" />
                )}
                <span className="text-sm">KUCCPS</span>
              </div>
              <div className="flex items-center gap-2">
                {factors.dataIngestion.nemisMatch ? (
                  <CheckCircle className="w-4 h-4 text-emerald-600" />
                ) : (
                  <XCircle className="w-4 h-4 text-slate-400" />
                )}
                <span className="text-sm">NEMIS</span>
              </div>
            </div>
            <p className="text-sm text-slate-600 mt-3">
              Data quality score: {(factors.dataIngestion.dataQuality * 100).toFixed(0)}%
              {factors.dataIngestion.dataQuality < 0.8 
                ? ' - Manual verification recommended.' 
                : ' - Cross-reference successful.'}
            </p>
          </div>
        )}
      </div>

      {/* Anomaly Indicators */}
      {factors.anomalyIndicators.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          <button 
            onClick={() => toggleSection('anomalies')}
            className="w-full p-4 flex items-center justify-between hover:bg-slate-50"
          >
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-600" />
              <span className="font-semibold">Anomaly Indicators</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">
                {factors.anomalyIndicators.length}
              </span>
            </div>
            {expandedSection === 'anomalies' ? (
              <ChevronUp className="w-5 h-5 text-slate-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-slate-400" />
            )}
          </button>
          
          {expandedSection === 'anomalies' && (
            <div className="px-4 pb-4">
              <ul className="space-y-2">
                {factors.anomalyIndicators.map((indicator, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-amber-700">
                    <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <span>{indicator}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
