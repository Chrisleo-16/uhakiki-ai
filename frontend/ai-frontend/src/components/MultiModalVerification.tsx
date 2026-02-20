"use client"

import { useState, useCallback } from 'react'
import { FileText, User, Shield, ArrowRight, CheckCircle, AlertTriangle, Clock, Loader2 } from 'lucide-react'
import DocumentUpload from './DocumentUpload'
import ForgeryEvidenceViewer from './ForgeryEvidenceViewer'
import BiometricVerification from './BiometricVerification'

interface VerificationStep {
  id: 'document' | 'biometric' | 'analysis'
  title: string
  description: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  icon: React.ComponentType<{ className?: string }>
}

interface MultiModalVerificationProps {
  studentId: string
  nationalId: string
  onVerificationComplete: (result: any) => void
  onError: (error: string) => void
}

export default function MultiModalVerification({ 
  studentId, 
  nationalId,
  onVerificationComplete,
  onError 
}: MultiModalVerificationProps) {
  const [currentStep, setCurrentStep] = useState<'document' | 'biometric' | 'analysis'>('document')
  const [verificationSteps, setVerificationSteps] = useState<VerificationStep[]>([
    {
      id: 'document',
      title: 'Document Verification',
      description: 'Upload and analyze identity document for forgery',
      status: 'in_progress',
      icon: FileText
    },
    {
      id: 'biometric',
      title: 'Biometric Verification',
      description: 'Face recognition and liveness detection',
      status: 'pending',
      icon: User
    },
    {
      id: 'analysis',
      title: 'Final Analysis',
      description: 'Cross-reference results and generate report',
      status: 'pending',
      icon: Shield
    }
  ])

  const [documentData, setDocumentData] = useState<any>(null)
  const [documentAnalysis, setDocumentAnalysis] = useState<any>(null)
  const [biometricResult, setBiometricResult] = useState<any>(null)
  const [finalAnalysis, setFinalAnalysis] = useState<any>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  const updateStepStatus = useCallback((stepId: string, status: VerificationStep['status']) => {
    setVerificationSteps(prev => 
      prev.map(step => 
        step.id === stepId ? { ...step, status } : step
      )
    )
  }, [])

  const handleDocumentUploaded = (data: any) => {
    setDocumentData(data)
  }

  const handleDocumentAnalyzed = async (analysisResult: any) => {
    setDocumentAnalysis(analysisResult)
    updateStepStatus('document', 'completed')
    
    // Auto-advance to biometric step
    setTimeout(() => {
      setCurrentStep('biometric')
      updateStepStatus('biometric', 'in_progress')
    }, 1500)
  }

  const handleDocumentError = (error: string) => {
    updateStepStatus('document', 'failed')
    onError(error)
  }

  const handleBiometricComplete = (result: any) => {
    setBiometricResult(result)
    updateStepStatus('biometric', 'completed')
    
    // Auto-advance to analysis step
    setTimeout(() => {
      setCurrentStep('analysis')
      updateStepStatus('analysis', 'in_progress')
      performFinalAnalysis()
    }, 1500)
  }

  const handleBiometricError = (error: string) => {
    updateStepStatus('biometric', 'failed')
    onError(error)
  }

  const performFinalAnalysis = async () => {
    setIsProcessing(true)
    
    try {
      // Combine document and biometric analysis
      const combinedData = {
        student_id: studentId,
        national_id: nationalId,
        document_analysis: documentAnalysis,
        biometric_analysis: biometricResult,
        verification_timestamp: new Date().toISOString()
      }

      // Call the comprehensive verification endpoint
      const formData = new FormData()
      
      // Add document if available
      if (documentData?.file) {
        formData.append('id_card', documentData.file)
      }
      
      // Add biometric data
      formData.append('national_id', nationalId)
      formData.append('student_id', studentId)
      
      // Mock liveness video (in real implementation, this would be captured)
      if (biometricResult?.sessionData) {
        formData.append('liveness_session', JSON.stringify(biometricResult.sessionData))
      }

      const response = await fetch('http://localhost:8000/verify-student', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`)
      }

      const finalResult = await response.json()
      setFinalAnalysis(finalResult)
      updateStepStatus('analysis', 'completed')
      
      // Complete verification
      setTimeout(() => {
        onVerificationComplete({
          ...finalResult,
          multimodal_data: {
            document_analysis: documentAnalysis,
            biometric_analysis: biometricResult,
            combined_result: finalResult
          }
        })
      }, 2000)

    } catch (error) {
      console.error('Final analysis failed:', error)
      updateStepStatus('analysis', 'failed')
      onError('Failed to complete final analysis. Please try again.')
    } finally {
      setIsProcessing(false)
    }
  }

  const getStepColor = (status: VerificationStep['status']) => {
    switch (status) {
      case 'completed': return 'text-emerald-600 bg-emerald-50 border-emerald-200'
      case 'in_progress': return 'text-blue-600 bg-blue-50 border-blue-200'
      case 'failed': return 'text-red-600 bg-red-50 border-red-200'
      case 'pending': return 'text-gray-400 bg-gray-50 border-gray-200'
    }
  }

  const getOverallProgress = () => {
    const completed = verificationSteps.filter(step => step.status === 'completed').length
    return (completed / verificationSteps.length) * 100
  }

  return (
    <div className="space-y-6">
      {/* Progress Header */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h2 className="text-xl font-semibold text-slate-900 mb-4">
          Multi-Modal Identity Verification
        </h2>
        
        {/* Progress Steps */}
        <div className="space-y-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-slate-600">Overall Progress</span>
            <span className="text-sm font-medium text-slate-900">{Math.round(getOverallProgress())}%</span>
          </div>
          <div className="w-full bg-slate-200 rounded-full h-2">
            <div 
              className="bg-emerald-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${getOverallProgress()}%` }}
            />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
            {verificationSteps.map((step, index) => (
              <div
                key={step.id}
                className={`relative p-4 rounded-lg border-2 transition-all ${
                  currentStep === step.id ? 'border-emerald-500 bg-emerald-50' :
                  getStepColor(step.status)
                }`}
              >
                <div className="flex items-start space-x-3">
                  <step.icon className={`w-5 h-5 mt-0.5 ${
                    step.status === 'completed' ? 'text-emerald-600' :
                    step.status === 'in_progress' ? 'text-blue-600' :
                    step.status === 'failed' ? 'text-red-600' :
                    'text-gray-400'
                  }`} />
                  <div className="flex-1">
                    <h4 className="font-medium text-slate-900">{step.title}</h4>
                    <p className="text-sm text-slate-600 mt-1">{step.description}</p>
                    {step.status === 'completed' && (
                      <div className="flex items-center space-x-1 mt-2">
                        <CheckCircle className="w-4 h-4 text-emerald-600" />
                        <span className="text-xs font-medium text-emerald-700">Completed</span>
                      </div>
                    )}
                    {step.status === 'in_progress' && (
                      <div className="flex items-center space-x-1 mt-2">
                        <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
                        <span className="text-xs font-medium text-blue-700">In Progress</span>
                      </div>
                    )}
                    {step.status === 'failed' && (
                      <div className="flex items-center space-x-1 mt-2">
                        <AlertTriangle className="w-4 h-4 text-red-600" />
                        <span className="text-xs font-medium text-red-700">Failed</span>
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Arrow connector */}
                {index < verificationSteps.length - 1 && (
                  <div className="hidden md:block absolute top-1/2 -right-3 transform -translate-y-1/2">
                    <ArrowRight className="w-6 h-6 text-slate-300" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Step Content */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        {currentStep === 'document' && (
          <div>
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Step 1: Document Verification</h3>
            <DocumentUpload
              onDocumentUploaded={handleDocumentUploaded}
              onDocumentAnalyzed={handleDocumentAnalyzed}
              onError={handleDocumentError}
              isAnalyzing={verificationSteps.find(s => s.id === 'document')?.status === 'in_progress'}
            />
          </div>
        )}

        {currentStep === 'biometric' && (
          <div>
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Step 2: Biometric Verification</h3>
            <BiometricVerification
              studentId={studentId}
              onVerificationComplete={handleBiometricComplete}
              onError={handleBiometricError}
            />
          </div>
        )}

        {currentStep === 'analysis' && (
          <div>
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Step 3: Final Analysis</h3>
            
            {isProcessing ? (
              <div className="text-center py-12">
                <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
                <h4 className="text-lg font-medium text-slate-900 mb-2">Performing Final Analysis</h4>
                <p className="text-slate-600">Cross-referencing document and biometric data...</p>
              </div>
            ) : finalAnalysis ? (
              <div className="space-y-6">
                {/* Final Result */}
                <div className={`rounded-xl border-2 p-6 ${
                  finalAnalysis.verdict === 'APPROVED' 
                    ? 'bg-emerald-50 border-emerald-200' 
                    : 'bg-red-50 border-red-200'
                }`}>
                  <div className="flex items-center space-x-3">
                    {finalAnalysis.verdict === 'APPROVED' ? (
                      <CheckCircle className="w-8 h-8 text-emerald-600" />
                    ) : (
                      <AlertTriangle className="w-8 h-8 text-red-600" />
                    )}
                    <div>
                      <h4 className="text-xl font-bold text-slate-900">
                        {finalAnalysis.verdict === 'APPROVED' ? 'Verification Approved' : 'Verification Flagged'}
                      </h4>
                      <p className="text-slate-600 mt-1">{finalAnalysis.explanation}</p>
                    </div>
                  </div>
                </div>

                {/* Component Results */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {documentAnalysis && (
                    <div className="p-4 bg-slate-50 rounded-lg">
                      <h5 className="font-medium text-slate-900 mb-2">Document Analysis</h5>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-slate-600">Judgment:</span>
                          <span className={`font-medium ${
                            documentAnalysis.judgment === 'AUTHENTIC' ? 'text-emerald-700' : 'text-red-700'
                          }`}>
                            {documentAnalysis.judgment}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-600">Forgery Risk:</span>
                          <span className="font-medium text-slate-900">
                            {(documentAnalysis.forgery_probability * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                  {biometricResult && (
                    <div className="p-4 bg-slate-50 rounded-lg">
                      <h5 className="font-medium text-slate-900 mb-2">Biometric Analysis</h5>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-slate-600">Result:</span>
                          <span className={`font-medium ${
                            biometricResult.verdict === 'APPROVED' ? 'text-emerald-700' : 'text-red-700'
                          }`}>
                            {biometricResult.verdict}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-600">Confidence:</span>
                          <span className="font-medium text-slate-900">
                            {biometricResult.confidence ? Math.round(biometricResult.confidence * 100) : 'N/A'}%
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Tracking ID */}
                <div className="p-4 bg-blue-50 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <Clock className="w-5 h-5 text-blue-600" />
                    <span className="text-sm font-medium text-blue-900">Tracking ID:</span>
                    <span className="font-mono text-sm text-blue-700">{finalAnalysis.tracking_id}</span>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        )}
      </div>

      {/* Document Evidence Viewer (shown when document analysis is complete) */}
      {documentAnalysis && currentStep !== 'document' && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Document Evidence</h3>
          <ForgeryEvidenceViewer
            analysisResult={documentAnalysis}
            documentType={documentData?.type || 'national_id'}
          />
        </div>
      )}
    </div>
  )
}
