"use client"

import { useState, useEffect } from 'react'
import BiometricVerification from '@/src/components/BiometricVerification'
import FaceRegistration from '@/src/components/FaceRegistration'
import { User, Camera, Shield, CheckCircle, AlertCircle } from 'lucide-react'

// Mock verification data
const mockVerifications = [
  {
    tracking_id: 'VR-2024-0892',
    student_id: 'STU-2024-0892',
    national_id: '3456789012',
    timestamp: '2024-06-15T09:30:00Z',
    status: 'completed',
    final_verdict: 'PASS',
    confidence_score: 94.2,
    risk_score: 12.5,
    processing_time: 2.3,
    components: {
      document_analysis: { forgery_probability: 0.02, judgment: 'AUTHENTIC' },
      biometric_analysis: { overall_score: 96.8, verified: true },
      aafi_decision: { verdict: 'APPROVED', confidence: 94.2 }
    }
  },
  {
    tracking_id: 'VR-2024-1034',
    student_id: 'STU-2024-1034',
    national_id: '23456789012',
    timestamp: '2024-06-15T10:45:00Z',
    status: 'processing',
    final_verdict: 'PENDING',
    confidence_score: 0,
    risk_score: 0,
    processing_time: 0,
    components: null
  },
  {
    tracking_id: 'VR-2024-0765',
    student_id: 'STU-2024-0765',
    national_id: '123456789012',
    timestamp: '2024-06-15T11:20:00Z',
    status: 'completed',
    final_verdict: 'REQUIRES_HUMAN_REVIEW',
    confidence_score: 67.8,
    risk_score: 45.3,
    processing_time: 4.1,
    components: {
      document_analysis: { forgery_probability: 0.34, judgment: 'SUSPICIOUS' },
      biometric_analysis: { overall_score: 78.2, verified: true },
      aafi_decision: { verdict: 'REQUIRES_REVIEW', confidence: 67.8 }
    }
  }
]

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-KE', {
    style: 'currency',
    currency: 'KES',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
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
    case 'completed':
      return 'text-emerald-700 bg-emerald-50 border-emerald-200'
    case 'processing':
      return 'text-blue-700 bg-blue-50 border-blue-200'
    case 'failed':
      return 'text-red-700 bg-red-50 border-red-200'
    case 'pending':
      return 'text-yellow-700 bg-yellow-50 border-yellow-200'
    default:
      return 'text-gray-700 bg-gray-50 border-gray-200'
  }
}

function getVerdictColor(verdict: string): string {
  switch (verdict.toUpperCase()) {
    case 'PASS':
      return 'text-emerald-700 bg-emerald-50 border-emerald-200'
    case 'FAIL':
      return 'text-red-700 bg-red-50 border-red-200'
    case 'REQUIRES_HUMAN_REVIEW':
      return 'text-yellow-700 bg-yellow-50 border-yellow-200'
    case 'PENDING':
      return 'text-blue-700 bg-blue-50 border-blue-200'
    default:
      return 'text-gray-700 bg-gray-50 border-gray-200'
  }
}

export default function VerificationsPage() {
  const [verifications, setVerifications] = useState(mockVerifications)
  const [filter, setFilter] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedVerification, setSelectedVerification] = useState<typeof mockVerifications[0] | null>(null)
  const [activeTab, setActiveTab] = useState<'history' | 'register' | 'verify'>('history')
  const [currentStudentId, setCurrentStudentId] = useState('')
  const [notification, setNotification] = useState<{ type: 'success' | 'error', message: string } | null>(null)

  const filteredVerifications = verifications.filter(verification => {
    const matchesFilter = filter === 'all' || verification.status === filter
    const matchesSearch = verification.student_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
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

  const handleVerificationComplete = (result: any) => {
    const verdict = result.verdict
    showNotification(
      verdict === 'APPROVED' ? 'success' : 'error',
      `Verification ${verdict}: ${result.council_reasoning || 'Process completed'}`
    )
    
    // Add to verification history
    const newVerification = {
      tracking_id: `VR-${Date.now()}`,
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
        aafi_decision: { verdict: verdict, confidence: 95.0 }
      }
    }
    
    setVerifications(prev => [newVerification, ...prev])
    setActiveTab('history')
  }

  const handleVerificationError = (error: string) => {
    showNotification('error', error)
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
            {notification.type === 'success' ? (
              <CheckCircle className="w-5 h-5" />
            ) : (
              <AlertCircle className="w-5 h-5" />
            )}
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
              <p className="text-2xl font-bold text-slate-900">{verifications.length}</p>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-slate-600">Success Rate</p>
              <p className="text-2xl font-bold text-emerald-600">
                {((verifications.filter(v => v.final_verdict === 'PASS').length / verifications.length) * 100).toFixed(1)}%
              </p>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex space-x-1 mt-6 bg-slate-100 p-1 rounded-lg">
          <button
            onClick={() => setActiveTab('history')}
            className={`flex-1 flex items-center justify-center space-x-2 px-4 py-2 rounded-md font-medium transition-colors ${
              activeTab === 'history'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <User className="w-4 h-4" />
            <span>Verification History</span>
          </button>
          <button
            onClick={() => setActiveTab('register')}
            className={`flex-1 flex items-center justify-center space-x-2 px-4 py-2 rounded-md font-medium transition-colors ${
              activeTab === 'register'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Camera className="w-4 h-4" />
            <span>Register Face</span>
          </button>
          <button
            onClick={() => setActiveTab('verify')}
            className={`flex-1 flex items-center justify-center space-x-2 px-4 py-2 rounded-md font-medium transition-colors ${
              activeTab === 'verify'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Shield className="w-4 h-4" />
            <span>Live Verification</span>
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'history' && (
        <>
          {/* Filters and Search */}
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

          {/* Verifications List */}
          <div className="space-y-4">
            {filteredVerifications.map((verification) => (
              <div key={verification.tracking_id} className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow">
                {/* Verification Header */}
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900">{verification.tracking_id}</h3>
                    <p className="text-sm text-slate-500">Student: {verification.student_id} | National ID: {verification.national_id}</p>
                    <p className="text-xs text-slate-500 mt-1">Submitted: {formatDate(verification.timestamp)}</p>
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

                {/* Processing Metrics */}
                {verification.status === 'completed' && (
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                    <div className="text-center p-3 bg-slate-50 rounded-lg">
                      <p className="text-sm font-medium text-slate-600">Confidence</p>
                      <p className={`text-lg font-bold ${
                        verification.confidence_score >= 80 ? 'text-emerald-600' :
                        verification.confidence_score >= 60 ? 'text-yellow-600' : 'text-red-600'
                      }`}>
                        {verification.confidence_score.toFixed(1)}%
                      </p>
                    </div>
                    <div className="text-center p-3 bg-slate-50 rounded-lg">
                      <p className="text-sm font-medium text-slate-600">Risk Score</p>
                      <p className={`text-lg font-bold ${
                        verification.risk_score <= 20 ? 'text-emerald-600' :
                        verification.risk_score <= 40 ? 'text-yellow-600' : 'text-red-600'
                      }`}>
                        {verification.risk_score.toFixed(1)}
                      </p>
                    </div>
                    <div className="text-center p-3 bg-slate-50 rounded-lg">
                      <p className="text-sm font-medium text-slate-600">Processing Time</p>
                      <p className="text-lg font-bold text-slate-900">{verification.processing_time}s</p>
                    </div>
                    <div className="text-center p-3 bg-slate-50 rounded-lg">
                      <p className="text-sm font-medium text-slate-600">Components</p>
                      <p className="text-lg font-bold text-slate-900">
                        {verification.components ? '3/3' : '0/3'}
                      </p>
                    </div>
                  </div>
                )}

                {/* Component Analysis */}
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

                {/* Actions */}
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

          {/* Empty State */}
          {filteredVerifications.length === 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center">
              <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-slate-900 mb-2">No verifications found</h3>
              <p className="text-sm text-slate-500">Try adjusting your search or filter criteria</p>
            </div>
          )}
        </>
      )}

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
              <p className="text-sm text-slate-500">Please provide a Student ID to register face</p>
            </div>
          )}
        </div>
      )}

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

      {/* Quick Stats */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Verification Statistics</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-emerald-50 rounded-lg">
            <p className="text-2xl font-bold text-emerald-600">
              {verifications.filter(v => v.final_verdict === 'PASS').length}
            </p>
            <p className="text-sm text-emerald-700">Successful Verifications</p>
          </div>
          <div className="text-center p-4 bg-yellow-50 rounded-lg">
            <p className="text-2xl font-bold text-yellow-600">
              {verifications.filter(v => v.final_verdict === 'REQUIRES_HUMAN_REVIEW').length}
            </p>
            <p className="text-sm text-yellow-700">Requires Review</p>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <p className="text-2xl font-bold text-red-600">
              {verifications.filter(v => v.final_verdict === 'FAIL').length}
            </p>
            <p className="text-sm text-red-700">Failed Verifications</p>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <p className="text-2xl font-bold text-blue-600">
              {verifications.filter(v => v.status === 'processing').length}
            </p>
            <p className="text-sm text-blue-700">In Progress</p>
          </div>
        </div>
      </div>
    </div>
  )
}
