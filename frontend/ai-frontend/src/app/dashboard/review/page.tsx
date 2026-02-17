"use client"

import { useState, useEffect } from 'react'
import { uhakikiAPI, type ReviewCase, type ReviewStats } from '../../../lib/api'
import { AlertTriangle, Clock, User, CheckCircle, XCircle, Loader2, Eye } from 'lucide-react'

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-KE', {
    style: 'currency',
    currency: 'KES',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

function getPriorityColor(priority: string): string {
  switch (priority) {
    case 'critical': return 'text-red-700 bg-red-50 border-red-200'
    case 'high': return 'text-orange-700 bg-orange-50 border-orange-200'
    case 'medium': return 'text-yellow-700 bg-yellow-50 border-yellow-200'
    case 'low': return 'text-green-700 bg-green-50 border-green-200'
    default: return 'text-gray-700 bg-gray-50 border-gray-200'
  }
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'pending': return 'text-yellow-700 bg-yellow-50 border-yellow-200'
    case 'in_review': return 'text-blue-700 bg-blue-50 border-blue-200'
    case 'completed': return 'text-green-700 bg-green-50 border-green-200'
    default: return 'text-gray-700 bg-gray-50 border-gray-200'
  }
}

export default function HumanReviewDashboard() {
  const [cases, setCases] = useState<ReviewCase[]>([])
  const [stats, setStats] = useState<ReviewStats | null>(null)
  const [selectedCase, setSelectedCase] = useState<ReviewCase | null>(null)
  const [filter, setFilter] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch review cases and stats
  const fetchReviewData = async () => {
    try {
      setLoading(true)
      setError(null)

      const [casesData, statsData] = await Promise.all([
        uhakikiAPI.getReviewCases('pending', 100),
        uhakikiAPI.getReviewStats()
      ])

      setCases(casesData)
      setStats(statsData)
    } catch (err) {
      console.error('Failed to fetch review data:', err)
      setError('Failed to load review data. Please check your connection.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchReviewData()
  }, [])

  const filteredCases = cases.filter((case_: ReviewCase) => {
    const matchesFilter = filter === 'all' || case_.priority === filter
    const matchesSearch = case_.student_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          case_.national_id.includes(searchTerm)
    return matchesFilter && matchesSearch
  })

  const handleCaseReview = async (caseId: string) => {
    try {
      const caseDetails = await uhakikiAPI.getReviewCase(caseId)
      setSelectedCase(caseDetails)
    } catch (err) {
      console.error('Failed to fetch case details:', err)
    }
  }

  const handleAssignCase = async (caseId: string, officer: string) => {
    try {
      await uhakikiAPI.assignReviewCase(caseId, officer)
      fetchReviewData() // Refresh data
    } catch (err) {
      console.error('Failed to assign case:', err)
    }
  }

  const handleCompleteReview = async (caseId: string, verdict: string, notes: string[]) => {
    try {
      await uhakikiAPI.completeReview(caseId, verdict, notes)
      setSelectedCase(null)
      fetchReviewData() // Refresh data
    } catch (err) {
      console.error('Failed to complete review:', err)
    }
  }

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-emerald-600 mx-auto mb-4" />
          <p className="text-slate-600">Loading Review Dashboard...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center max-w-md">
          <XCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-2">Review Error</h3>
          <p className="text-slate-600 mb-4">{error}</p>
          <button
            onClick={fetchReviewData}
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
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">Human Review Queue</h2>
            <p className="text-sm text-slate-500">Cases requiring human intervention and oversight</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <p className="text-sm font-medium text-slate-600">Pending Review</p>
              <p className="text-2xl font-bold text-yellow-600">{stats?.pending_cases || 0}</p>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-slate-600">In Progress</p>
              <p className="text-2xl font-bold text-blue-600">{stats?.assigned_cases || 0}</p>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-slate-600">Completed Today</p>
              <p className="text-2xl font-bold text-emerald-600">{stats?.completed_cases || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-slate-700 mb-2">Search Cases</label>
            <input
              type="text"
              placeholder="Search by Student ID or National ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Filter by Priority</label>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
            >
              <option value="all">All Cases</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>
      </div>

      {/* Cases Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {filteredCases.map((case_: ReviewCase) => (
          <div key={case_.id} className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="flex items-center space-x-2 mb-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getPriorityColor(case_.priority)}`}>
                    {case_.priority.toUpperCase()}
                  </span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(case_.status)}`}>
                    {case_.status.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
                <h3 className="text-lg font-semibold text-slate-900">{case_.student_id}</h3>
                <p className="text-sm text-slate-500">ID: {case_.national_id}</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-red-600">{case_.risk_score}</p>
                <p className="text-xs text-slate-500">Risk Score</p>
              </div>
            </div>

            <div className="space-y-3 mb-4">
              <div className="flex items-center text-sm text-slate-600">
                <User className="w-4 h-4 mr-2" />
                Assigned to: {case_.assigned_to || 'Unassigned'}
              </div>
              <div className="flex items-center text-sm text-slate-600">
                <Clock className="w-4 h-4 mr-2" />
                Created: {new Date(case_.created_at).toLocaleDateString()}
              </div>
            </div>

            <div className="mb-4">
              <p className="text-sm font-medium text-slate-700 mb-2">Review Notes:</p>
              <div className="space-y-1">
                {case_.notes.slice(0, 2).map((note: string, index: number) => (
                  <p key={index} className="text-xs text-slate-600 bg-slate-50 p-2 rounded">
                    {note}
                  </p>
                ))}
                {case_.notes.length > 2 && (
                  <p className="text-xs text-slate-500">+{case_.notes.length - 2} more notes...</p>
                )}
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleCaseReview(case_.id)}
                className="flex-1 px-3 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors flex items-center justify-center space-x-1"
              >
                <Eye className="w-4 h-4" />
                <span>Review Case</span>
              </button>
              <button
                onClick={() => handleAssignCase(case_.id, 'Officer J. Kamau')}
                className="px-3 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
              >
                Assign
              </button>
            </div>
          </div>
        ))}
      </div>

      {filteredCases.length === 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center">
          <AlertTriangle className="w-12 h-12 text-slate-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-2">No Cases Found</h3>
          <p className="text-slate-600">No review cases match your current filters.</p>
        </div>
      )}

      {/* Case Detail Modal */}
      {selectedCase && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-slate-900">Case Review: {selectedCase.student_id}</h3>
                <button
                  onClick={() => setSelectedCase(null)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <XCircle className="w-6 h-6" />
                </button>
              </div>

              <div className="space-y-6">
                {/* Case Details */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium text-slate-700">Student ID</p>
                    <p className="text-slate-900">{selectedCase.student_id}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-700">National ID</p>
                    <p className="text-slate-900">{selectedCase.national_id}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-700">Risk Score</p>
                    <p className="text-2xl font-bold text-red-600">{selectedCase.risk_score}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-700">Priority</p>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getPriorityColor(selectedCase.priority)}`}>
                      {selectedCase.priority.toUpperCase()}
                    </span>
                  </div>
                </div>

                {/* All Notes */}
                <div>
                  <p className="text-sm font-medium text-slate-700 mb-2">All Review Notes:</p>
                  <div className="space-y-2">
                    {selectedCase.notes.map((note: string, index: number) => (
                      <p key={index} className="text-sm text-slate-600 bg-slate-50 p-3 rounded">
                        {note}
                      </p>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => handleCompleteReview(selectedCase.id, 'APPROVED', ['Manual review completed - no issues found'])}
                    className="flex-1 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
                  >
                    Approve Case
                  </button>
                  <button
                    onClick={() => handleCompleteReview(selectedCase.id, 'REJECTED', ['Fraud indicators confirmed - case rejected'])}
                    className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                  >
                    Reject Case
                  </button>
                  <button
                    onClick={() => handleCompleteReview(selectedCase.id, 'REQUIRES_FURTHER_INVESTIGATION', ['Additional verification required'])}
                    className="flex-1 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors"
                  >
                    Request More Info
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
