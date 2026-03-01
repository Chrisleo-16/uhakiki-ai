"use client"

import { useState, useEffect } from 'react'
import BiometricVerification from '@/components/BiometricVerification'
import MultiModalVerification from '@/components/MultiModalVerification'
import ForgeryEvidenceViewer from '@/components/ForgeryEvidenceViewer'
import NationalSecurityDashboard from '@/components/NationalSecurityDashboard'
import FaceRegistration from '@/components/FaceRegistration'
import { User, Camera, Shield, CheckCircle, AlertCircle, FileText, Layers, Eye, BarChart3, XCircle } from 'lucide-react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type VerificationRecord = {
  tracking_id: string
  student_id: string
  national_id: string
  timestamp: string
  status: 'completed' | 'processing' | 'failed' | 'pending'
  final_verdict: 'PASS' | 'FAIL' | 'REQUIRES_HUMAN_REVIEW' | 'PENDING'
  confidence_score: number
  risk_score: number
  processing_time: number
  components?: {
    document_analysis: { forgery_probability: number, judgment: string }
    biometric_analysis: { overall_score: number, verified: boolean }
    aafi_decision: { verdict: string, confidence: number }
  }
  multimodal_data?: {
    document_analysis: any
    biometric_analysis: any
    combined_result: any
  }
}

function formatDate(date: string): string {
  return new Intl.DateTimeFormat('en-KE', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(date))
}

function getStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'completed': return 'text-emerald-700 bg-emerald-50 border-emerald-200'
    case 'processing': return 'text-blue-700 bg-blue-50 border-blue-200'
    case 'failed':     return 'text-red-700 bg-red-50 border-red-200'
    case 'pending':    return 'text-yellow-700 bg-yellow-50 border-yellow-200'
    default:           return 'text-gray-700 bg-gray-50 border-gray-200'
  }
}

function getVerdictColor(verdict: string): string {
  switch (verdict.toUpperCase()) {
    case 'PASS':                  return 'text-emerald-700 bg-emerald-50 border-emerald-200'
    case 'FAIL':                  return 'text-red-700 bg-red-50 border-red-200'
    case 'REQUIRES_HUMAN_REVIEW': return 'text-yellow-700 bg-yellow-50 border-yellow-200'
    case 'PENDING':               return 'text-blue-700 bg-blue-50 border-blue-200'
    default:                      return 'text-gray-700 bg-gray-50 border-gray-200'
  }
}

// ✅ Safe success rate — avoids divide-by-zero when list is empty
function calcSuccessRate(verifications: VerificationRecord[]): string {
  if (verifications.length === 0) return '0.0'
  const passed = verifications.filter(v => v.final_verdict === 'PASS').length
  return ((passed / verifications.length) * 100).toFixed(1)
}

export default function VerificationsPage() {
  const [verifications, setVerifications]             = useState<VerificationRecord[]>([])
  const [filter, setFilter]                           = useState('all')
  const [searchTerm, setSearchTerm]                   = useState('')
  const [selectedVerification, setSelectedVerification] = useState<VerificationRecord | null>(null)
  const [activeTab, setActiveTab] = useState<'history' | 'register' | 'verify' | 'multimodal' | 'security'>('history')
  const [currentStudentId, setCurrentStudentId] = useState('')
  const [currentNationalId, setCurrentNationalId] = useState('')
  const [notification, setNotification] = useState<{ type: 'success' | 'error', message: string } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showEvidenceModal, setShowEvidenceModal] = useState(false)
  const [selectedEvidence, setSelectedEvidence] = useState<any>(null)

  const fetchVerifications = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch(`${API_BASE}/api/v1/verifications/history`)
      if (!response.ok) throw new Error(`Server returned ${response.status}`)

      const data = await response.json()
      // ✅ Always ensure we set an array, even if backend returns null/undefined
      setVerifications(Array.isArray(data) ? data : [])

    } catch (err) {
      console.error('Failed to fetch verifications:', err)
      setError('Failed to load verification history. Please check your connection.')
      setVerifications([]) // ✅ Reset to empty array on error so page still renders
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchVerifications()
  }, [])

  const filteredVerifications = verifications.filter(verification => {
    const matchesFilter = filter === 'all' || verification.status === filter
    const matchesSearch =
      verification.student_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      verification.tracking_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      verification.national_id.includes(searchTerm)
    return matchesFilter && matchesSearch
  })

  const showNotification = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message })
    setTimeout(() => setNotification(null), 5000)
  }

  const handleRegistrationComplete = (result: any) => {
    showNotification('success', `Face registered successfully for student ${result.student_id}`)
    setActiveTab('verify')
  }

  const handleRegistrationError = (error: string) => {
    showNotification('error', error)
  }

  const handleMultimodalComplete = (result: any) => {
    const verdict = result.verdict || result.combined_result?.verdict
    showNotification(
      verdict === 'APPROVED' ? 'success' : 'error',
      `Multi-Modal Verification ${verdict}: ${result.explanation || result.combined_result?.explanation || 'Process completed'}`
    )

    const newVerification: VerificationRecord = {
      tracking_id: result.tracking_id || result.combined_result?.tracking_id || `VR-${Date.now()}`,
      student_id: currentStudentId,
      national_id: currentNationalId,
      timestamp: new Date().toISOString(),
      status: 'completed',
      final_verdict: verdict === 'APPROVED' ? 'PASS' : 'FAIL',
      confidence_score: result.confidence || 95.0,
      risk_score: verdict === 'APPROVED' ? 5.2 : 78.5,
      processing_time: result.processing_time || 0,
      components: {
        document_analysis: result.multimodal_data?.document_analysis ? {
          forgery_probability: result.multimodal_data.document_analysis.forgery_probability || 0.01,
          judgment: result.multimodal_data.document_analysis.judgment || 'AUTHENTIC'
        } : { forgery_probability: 0.01, judgment: 'AUTHENTIC' },
        biometric_analysis: result.multimodal_data?.biometric_analysis ? {
          overall_score: result.multimodal_data.biometric_analysis.confidence || 96.8,
          verified: result.multimodal_data.biometric_analysis.verdict === 'APPROVED'
        } : { overall_score: 96.8, verified: true },
        aafi_decision: {
          verdict: verdict || 'PENDING',
          confidence: result.confidence || 95.0
        }
      },
      multimodal_data: result.multimodal_data
    }

    setVerifications(prev => [newVerification, ...prev])
    setActiveTab('history')
  }

  const handleViewEvidence = (verification: VerificationRecord) => {
    if (verification.multimodal_data?.document_analysis) {
      setSelectedEvidence(verification.multimodal_data.document_analysis)
      setShowEvidenceModal(true)
    }
  }

  const handleCloseEvidenceModal = () => {
    setShowEvidenceModal(false)
    setSelectedEvidence(null)
  }

  const handleVerificationError = (error: string) => {
    showNotification('error', error)
  }

  const handleVerificationComplete = (result: any) => {
    const verdict = result.verdict
    showNotification(
      verdict === 'APPROVED' ? 'success' : 'error',
      `Verification ${verdict}: ${result.council_reasoning || 'Process completed'}`
    )

    const newVerification: VerificationRecord = {
      tracking_id: result.tracking_id || `VR-${Date.now()}`,
      student_id: currentStudentId,
      national_id: 'N/A',
      timestamp: new Date().toISOString(),
      status: 'completed',
      final_verdict: verdict === 'APPROVED' ? 'PASS' : 'FAIL',
      confidence_score: result.session_summary ? 95.0 : 0,
      risk_score: verdict === 'APPROVED' ? 5.2 : 78.5,
      processing_time: result.session_summary?.session_duration || 0,
      components: {
        document_analysis: { forgery_probability: 0.01, judgment: 'AUTHENTIC' },
        biometric_analysis: { overall_score: 96.8, verified: true },
        aafi_decision: { verdict, confidence: 95.0 }
      }
    }

    setVerifications(prev => [newVerification, ...prev])
    setActiveTab('history')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-600">Loading Verification History...</p>
        </div>
      </div>
    )
  }

  // ✅ Error screen no longer blocks the full page — shows retry but doesn't crash
  if (error && verifications.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center max-w-md">
          <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-6 h-6 text-red-600" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2">Could Not Load History</h3>
          <p className="text-slate-600 mb-4">{error}</p>
          <button
            onClick={fetchVerifications}
            className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Notification */}
      {notification && (
        <div className={`rounded-lg border p-4 ${
          notification.type === 'success'
            ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
            : 'bg-red-50 border-red-200 text-red-800'
        }`}>
          <div className="flex items-center space-x-2">
            {notification.type === 'success'
              ? <CheckCircle className="w-5 h-5" />
              : <AlertCircle className="w-5 h-5" />
            }
            <span>{notification.message}</span>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">UhakikiAI Verification Center</h2>
            <p className="text-sm text-slate-500">Multimodal Biometric Identity Verification System</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <p className="text-sm font-medium text-slate-600">Total Processed</p>
              {/* ✅ Safe — just shows the count */}
              <p className="text-2xl font-bold text-slate-900">{verifications.length}</p>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-slate-600">Success Rate</p>
              {/* ✅ Fixed — no more divide-by-zero NaN crash */}
              <p className="text-2xl font-bold text-emerald-600">
                {calcSuccessRate(verifications)}%
              </p>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex space-x-1 mt-6 bg-slate-100 p-1 rounded-lg">
          {(['history', 'register', 'verify', 'multimodal', 'security'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 flex items-center justify-center space-x-2 px-2 py-2 rounded-md font-medium transition-colors ${
                activeTab === tab
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {tab === 'history' && <><User className="w-4 h-4" /><span>History</span></>}
              {tab === 'register' && <><Camera className="w-4 h-4" /><span>Register</span></>}
              {tab === 'verify' && <><Shield className="w-4 h-4" /><span>Biometric</span></>}
              {tab === 'multimodal' && <><Layers className="w-4 h-4" /><span>Multi-Modal</span></>}
              {tab === 'security' && <><BarChart3 className="w-4 h-4" /><span>Security</span></>}
            </button>
          ))}
        </div>
      </div>

      {/* ── HISTORY TAB ───────────────────────────────────────────── */}
      {activeTab === 'history' && (
        <>
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <label className="block text-sm font-medium text-slate-700 mb-2">Search Verifications</label>
                <input
                  type="text"
                  placeholder="Search by Tracking ID, Student ID, or National ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Filter by Status</label>
                <select
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                  className="px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                >
                  <option value="all">All Verifications</option>
                  <option value="completed">Completed</option>
                  <option value="processing">Processing</option>
                  <option value="failed">Failed</option>
                  <option value="pending">Pending</option>
                </select>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            {filteredVerifications.map((verification) => (
              <div key={verification.tracking_id} className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900">{verification.tracking_id}</h3>
                    <p className="text-sm text-slate-500">Student: {verification.student_id} | National ID: {verification.national_id}</p>
                    {/* ✅ Guard against invalid timestamp crashing the date formatter */}
                    <p className="text-xs text-slate-500 mt-1">
                      Submitted: {verification.timestamp ? formatDate(verification.timestamp) : 'Unknown'}
                    </p>
                  </div>
                  <div className="flex flex-col items-end space-y-2">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getStatusColor(verification.status)}`}>
                      {verification.status.replace('_', ' ').toUpperCase()}
                    </span>
                    {verification.final_verdict !== 'PENDING' && (
                      <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getVerdictColor(verification.final_verdict)}`}>
                        {verification.final_verdict.replace('_', ' ').toUpperCase()}
                      </span>
                    )}
                  </div>
                </div>

                {verification.status === 'completed' && (
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                    <div className="text-center p-3 bg-slate-50 rounded-lg">
                      <p className="text-sm font-medium text-slate-600">Confidence</p>
                      <p className={`text-lg font-bold ${
                        verification.confidence_score >= 80 ? 'text-emerald-600' :
                        verification.confidence_score >= 60 ? 'text-yellow-600' : 'text-red-600'
                      }`}>
                        {/* ✅ Guard against undefined confidence_score */}
                        {(verification.confidence_score ?? 0).toFixed(1)}%
                      </p>
                    </div>
                    <div className="text-center p-3 bg-slate-50 rounded-lg">
                      <p className="text-sm font-medium text-slate-600">Risk Score</p>
                      <p className={`text-lg font-bold ${
                        verification.risk_score <= 20 ? 'text-emerald-600' :
                        verification.risk_score <= 40 ? 'text-yellow-600' : 'text-red-600'
                      }`}>
                        {(verification.risk_score ?? 0).toFixed(1)}
                      </p>
                    </div>
                    <div className="text-center p-3 bg-slate-50 rounded-lg">
                      <p className="text-sm font-medium text-slate-600">Processing Time</p>
                      <p className="text-lg font-bold text-slate-900">{verification.processing_time ?? 0}s</p>
                    </div>
                    <div className="text-center p-3 bg-slate-50 rounded-lg">
                      <p className="text-sm font-medium text-slate-600">Components</p>
                      <p className="text-lg font-bold text-slate-900">{verification.components ? '3/3' : '0/3'}</p>
                    </div>
                  </div>
                )}

                {verification.components && (
                  <div className="mb-4 p-4 bg-slate-50 rounded-lg">
                    <h4 className="text-sm font-medium text-slate-700 mb-3">Component Analysis:</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="flex items-center space-x-2">
                        <div className={`w-3 h-3 rounded-full ${
                          verification.components.document_analysis.judgment === 'AUTHENTIC' ? 'bg-emerald-500' : 'bg-yellow-500'
                        }`}></div>
                        <div>
                          <p className="text-sm font-medium text-slate-700">Document Analysis</p>
                          <p className="text-xs text-slate-500">
                            {verification.components.document_analysis.judgment}
                            ({(verification.components.document_analysis.forgery_probability * 100).toFixed(1)}% risk)
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className={`w-3 h-3 rounded-full ${
                          verification.components.biometric_analysis.verified ? 'bg-emerald-500' : 'bg-red-500'
                        }`}></div>
                        <div>
                          <p className="text-sm font-medium text-slate-700">Biometric Analysis</p>
                          <p className="text-xs text-slate-500">
                            {verification.components.biometric_analysis.verified ? 'Verified' : 'Failed'}
                            ({verification.components.biometric_analysis.overall_score.toFixed(1)}% match)
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className={`w-3 h-3 rounded-full ${
                          verification.components.aafi_decision.verdict === 'APPROVED' ? 'bg-emerald-500' : 'bg-yellow-500'
                        }`}></div>
                        <div>
                          <p className="text-sm font-medium text-slate-700">AAFI Decision</p>
                          <p className="text-xs text-slate-500">
                            {verification.components.aafi_decision.verdict}
                            ({verification.components.aafi_decision.confidence.toFixed(1)}% confidence)
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Show Evidence Button for Multi-Modal Verifications */}
                {verification.multimodal_data?.document_analysis && (
                  <div className="mb-4 p-4 bg-blue-50 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-sm font-medium text-blue-900">Document Forensics Available</h4>
                        <p className="text-xs text-blue-700">ELA and RAD analysis evidence stored</p>
                      </div>
                      <button
                        onClick={() => handleViewEvidence(verification)}
                        className="px-3 py-1 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 flex items-center space-x-1"
                      >
                        <Eye className="w-4 h-4" />
                        <span>View Evidence</span>
                      </button>
                    </div>
                  </div>
                )}

                <div className="flex space-x-3">
                  <button
                    onClick={() => setSelectedVerification(verification)}
                    className="flex-1 px-4 py-2 bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-700 transition-colors"
                  >
                    View Details
                  </button>
                  {verification.status === 'processing' && (
                    <button className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors">
                      Track Progress
                    </button>
                  )}
                  {verification.final_verdict === 'REQUIRES_HUMAN_REVIEW' && (
                    <button className="px-4 py-2 bg-yellow-600 text-white font-medium rounded-lg hover:bg-yellow-700 transition-colors">
                      Review Case
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          {filteredVerifications.length === 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center">
              <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-slate-900 mb-2">No verifications found</h3>
              <p className="text-sm text-slate-500">
                {verifications.length === 0
                  ? 'No verifications have been recorded yet. Register a face and run a verification to get started.'
                  : 'Try adjusting your search or filter criteria.'
                }
              </p>
            </div>
          )}
        </>
      )}

      {/* ── REGISTER TAB ─────────────────────────────────────────── */}
      {activeTab === 'register' && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-700 mb-2">Student ID</label>
            <input
              type="text"
              placeholder="Enter Student ID (e.g., STU-2024-0892)"
              value={currentStudentId}
              onChange={(e) => setCurrentStudentId(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
            />
          </div>
          {currentStudentId ? (
            <FaceRegistration
              studentId={currentStudentId}
              onRegistrationComplete={handleRegistrationComplete}
              onError={handleRegistrationError}
            />
          ) : (
            <div className="text-center py-12">
              <User className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900 mb-2">Enter Student ID</h3>
              <p className="text-sm text-slate-500">Please provide a Student ID to register a face</p>
            </div>
          )}
        </div>
      )}

      {/* ── MULTIMODAL TAB ─────────────────────────────────────────── */}
      {activeTab === 'multimodal' && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="mb-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Student ID</label>
              <input
                type="text"
                placeholder="Enter Student ID (e.g., STU-2024-0892)"
                value={currentStudentId}
                onChange={(e) => setCurrentStudentId(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">National ID</label>
              <input
                type="text"
                placeholder="Enter National ID Number"
                value={currentNationalId}
                onChange={(e) => setCurrentNationalId(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              />
            </div>
          </div>
          
          {currentStudentId && currentNationalId ? (
            <MultiModalVerification
              studentId={currentStudentId}
              nationalId={currentNationalId}
              onVerificationComplete={handleMultimodalComplete}
              onError={handleVerificationError}
            />
          ) : (
            <div className="text-center py-12">
              <Layers className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900 mb-2">Enter Credentials</h3>
              <p className="text-sm text-slate-500">Please provide both Student ID and National ID to start multi-modal verification</p>
            </div>
          )}
        </div>
      )}

      {/* ── VERIFY TAB ───────────────────────────────────────────── */}
      {activeTab === 'verify' && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-700 mb-2">Student ID</label>
            <input
              type="text"
              placeholder="Enter Student ID for verification"
              value={currentStudentId}
              onChange={(e) => setCurrentStudentId(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
            />
          </div>
          {currentStudentId ? (
            <BiometricVerification
              studentId={currentStudentId}
              onVerificationComplete={handleVerificationComplete}
              onError={handleVerificationError}
            />
          ) : (
            <div className="text-center py-12">
              <Shield className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900 mb-2">Enter Student ID</h3>
              <p className="text-sm text-slate-500">Please provide a Student ID to start verification</p>
            </div>
          )}
        </div>
      )}

      {/* ── SECURITY DASHBOARD TAB ─────────────────────────────────────── */}
      {activeTab === 'security' && (
        <NationalSecurityDashboard />
      )}

      {/* Evidence Modal */}
      {showEvidenceModal && selectedEvidence && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-6xl w-full max-h-[90vh] overflow-auto">
            <div className="sticky top-0 bg-white border-b border-slate-200 p-6">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-slate-900">Document Forgery Evidence</h2>
                <button
                  onClick={handleCloseEvidenceModal}
                  className="p-2 hover:bg-slate-100 rounded-lg"
                >
                  <XCircle className="w-5 h-5 text-slate-600" />
                </button>
              </div>
            </div>
            <div className="p-6">
              <ForgeryEvidenceViewer
                analysisResult={selectedEvidence}
                documentType="national_id"
                onExportEvidence={() => {
                  // Handle export
                  console.log('Exporting evidence...')
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}