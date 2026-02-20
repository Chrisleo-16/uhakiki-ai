"use client"

import { useState } from 'react'
import { Eye, EyeOff, Download, AlertTriangle, CheckCircle, XCircle, ZoomIn, ZoomOut } from 'lucide-react'

interface ForgeryAnalysisResult {
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

interface ForgeryEvidenceViewerProps {
  analysisResult: ForgeryAnalysisResult
  documentType: string
  onExportEvidence?: () => void
}

export default function ForgeryEvidenceViewer({ 
  analysisResult, 
  documentType,
  onExportEvidence 
}: ForgeryEvidenceViewerProps) {
  const [activeView, setActiveView] = useState<'original' | 'ela' | 'reconstruction' | 'comparison'>('comparison')
  const [zoomLevel, setZoomLevel] = useState(1)
  const [showDetails, setShowDetails] = useState(true)

  const getJudgmentColor = (judgment: string) => {
    switch (judgment.toUpperCase()) {
      case 'AUTHENTIC': return 'text-emerald-600 bg-emerald-50 border-emerald-200'
      case 'FORGED': return 'text-red-600 bg-red-50 border-red-200'
      case 'SUSPICIOUS': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getJudgmentIcon = (judgment: string) => {
    switch (judgment.toUpperCase()) {
      case 'AUTHENTIC': return <CheckCircle className="w-5 h-5" />
      case 'FORGED': return <XCircle className="w-5 h-5" />
      case 'SUSPICIOUS': return <AlertTriangle className="w-5 h-5" />
      default: return <AlertTriangle className="w-5 h-5" />
    }
  }

  const getImageUrl = (path: string) => {
    // Convert backend path to accessible URL
    if (path.startsWith('backend/')) {
      return `http://localhost:8000/${path}`
    }
    return path
  }

  const handleZoomIn = () => setZoomLevel(prev => Math.min(prev + 0.25, 3))
  const handleZoomOut = () => setZoomLevel(prev => Math.max(prev - 0.25, 0.5))

  const exportEvidence = () => {
    const evidenceData = {
      document_type: documentType,
      analysis_timestamp: new Date().toISOString(),
      analysis_result: analysisResult,
      evidence_urls: {
        original: getImageUrl(analysisResult.visuals.original),
        ela_map: getImageUrl(analysisResult.visuals.ela_map),
        reconstruction: getImageUrl(analysisResult.visuals.reconstruction)
      }
    }
    
    const blob = new Blob([JSON.stringify(evidenceData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `forgery_evidence_${Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    onExportEvidence?.()
  }

  return (
    <div className="space-y-6">
      {/* Header with Judgment */}
      <div className={`rounded-xl border-2 p-6 ${getJudgmentColor(analysisResult.judgment)}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {getJudgmentIcon(analysisResult.judgment)}
            <div>
              <h3 className="text-xl font-bold">Document Analysis Result</h3>
              <p className="text-sm opacity-75">
                {documentType.replace('_', ' ').toUpperCase()} - Forensic Analysis Complete
              </p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold">
              {(analysisResult.forgery_probability * 100).toFixed(1)}%
            </div>
            <div className="text-sm font-medium">Forgery Probability</div>
          </div>
        </div>
      </div>

      {/* Analysis Metrics */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h4 className="text-lg font-semibold text-slate-900 mb-4">Forensic Analysis Metrics</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-slate-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-slate-600">ELA Analysis</span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                analysisResult.ela_status === 'AUTHENTIC' ? 'bg-emerald-100 text-emerald-700' :
                analysisResult.ela_status === 'FORGED' ? 'bg-red-100 text-red-700' :
                'bg-yellow-100 text-yellow-700'
              }`}>
                {analysisResult.ela_status}
              </span>
            </div>
            <p className="text-xs text-slate-500">Error Level Analysis detected compression artifacts</p>
          </div>

          <div className="p-4 bg-slate-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-slate-600">Neural Analysis</span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                analysisResult.neural_anomaly === 'CLEAN' ? 'bg-emerald-100 text-emerald-700' :
                'bg-red-100 text-red-700'
              }`}>
                {analysisResult.neural_anomaly}
              </span>
            </div>
            <p className="text-xs text-slate-500">RAD Autoencoder reconstruction analysis</p>
          </div>

          <div className="p-4 bg-slate-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-slate-600">Final Judgment</span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                analysisResult.judgment === 'AUTHENTIC' ? 'bg-emerald-100 text-emerald-700' :
                analysisResult.judgment === 'FORGED' ? 'bg-red-100 text-red-700' :
                'bg-yellow-100 text-yellow-700'
              }`}>
                {analysisResult.judgment}
              </span>
            </div>
            <p className="text-xs text-slate-500">Combined forensic analysis result</p>
          </div>
        </div>
      </div>

      {/* View Controls */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex space-x-2">
            {[
              { id: 'comparison', label: 'Comparison' },
              { id: 'original', label: 'Original' },
              { id: 'ela', label: 'ELA Map' },
              { id: 'reconstruction', label: 'Reconstruction' }
            ].map((view) => (
              <button
                key={view.id}
                onClick={() => setActiveView(view.id as any)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeView === view.id
                    ? 'bg-emerald-600 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {view.label}
              </button>
            ))}
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleZoomOut}
              className="p-2 rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="text-sm font-medium text-slate-600 min-w-[3rem] text-center">
              {Math.round(zoomLevel * 100)}%
            </span>
            <button
              onClick={handleZoomIn}
              className="p-2 rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="p-2 rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200"
            >
              {showDetails ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
            <button
              onClick={exportEvidence}
              className="px-3 py-2 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 flex items-center space-x-1"
            >
              <Download className="w-4 h-4" />
              <span>Export</span>
            </button>
          </div>
        </div>
      </div>

      {/* Image Viewer */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="overflow-auto max-h-[600px]">
          {activeView === 'comparison' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <div>
                  <h5 className="text-sm font-medium text-slate-700 mb-2">Original Document</h5>
                  <div className="border border-slate-200 rounded-lg overflow-hidden">
                    <img
                      src={getImageUrl(analysisResult.visuals.original)}
                      alt="Original document"
                      style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'top left' }}
                      className="w-full h-auto"
                    />
                  </div>
                </div>
                <div>
                  <h5 className="text-sm font-medium text-slate-700 mb-2">ELA Analysis</h5>
                  <div className="border border-slate-200 rounded-lg overflow-hidden">
                    <img
                      src={getImageUrl(analysisResult.visuals.ela_map)}
                      alt="ELA map showing manipulation areas"
                      style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'top left' }}
                      className="w-full h-auto"
                    />
                  </div>
                </div>
                <div>
                  <h5 className="text-sm font-medium text-slate-700 mb-2">RAD Reconstruction</h5>
                  <div className="border border-slate-200 rounded-lg overflow-hidden">
                    <img
                      src={getImageUrl(analysisResult.visuals.reconstruction)}
                      alt="Neural reconstruction showing anomalies"
                      style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'top left' }}
                      className="w-full h-auto"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeView !== 'comparison' && (
            <div className="space-y-4">
              <h5 className="text-sm font-medium text-slate-700 capitalize">
                {activeView === 'ela' ? 'Error Level Analysis Map' :
                 activeView === 'reconstruction' ? 'RAD Autoencoder Reconstruction' :
                 'Original Document'}
              </h5>
              <div className="border border-slate-200 rounded-lg overflow-hidden">
                <img
                  src={
                    activeView === 'original' ? getImageUrl(analysisResult.visuals.original) :
                    activeView === 'ela' ? getImageUrl(analysisResult.visuals.ela_map) :
                    getImageUrl(analysisResult.visuals.reconstruction)
                  }
                  alt={activeView}
                  style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'top left' }}
                  className="w-full h-auto"
                />
              </div>
            </div>
          )}
        </div>

        {/* Analysis Details */}
        {showDetails && (
          <div className="mt-6 p-4 bg-slate-50 rounded-lg">
            <h5 className="text-sm font-medium text-slate-700 mb-3">Technical Analysis Details</h5>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium text-slate-600">ELA Status:</span>
                <span className="ml-2 text-slate-900">{analysisResult.ela_status}</span>
              </div>
              <div>
                <span className="font-medium text-slate-600">Neural Anomaly:</span>
                <span className="ml-2 text-slate-900">{analysisResult.neural_anomaly}</span>
              </div>
              <div>
                <span className="font-medium text-slate-600">Forgery Probability:</span>
                <span className="ml-2 text-slate-900">
                  {(analysisResult.forgery_probability * 100).toFixed(2)}%
                </span>
              </div>
              <div>
                <span className="font-medium text-slate-600">Risk Level:</span>
                <span className="ml-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    analysisResult.forgery_probability > 0.7 ? 'bg-red-100 text-red-700' :
                    analysisResult.forgery_probability > 0.3 ? 'bg-yellow-100 text-yellow-700' :
                    'bg-emerald-100 text-emerald-700'
                  }`}>
                    {analysisResult.forgery_probability > 0.7 ? 'HIGH' :
                     analysisResult.forgery_probability > 0.3 ? 'MEDIUM' : 'LOW'}
                  </span>
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
