"use client"

import { useState, useEffect } from 'react'

// Mock data for human review cases
const mockReviewCases = [
  {
    id: 'HR-001',
    student_id: 'STU-2024-0892',
    national_id: '3456789012',
    risk_score: 78.5,
    priority: 'critical',
    assigned_to: 'Officer K. Mwangi',
    created_at: '2024-06-15T09:30:00Z',
    status: 'pending',
    notes: ['High-risk document anomalies detected', 'Biometric mismatch indicators', 'Multiple application attempts']
  },
  {
    id: 'HR-002', 
    student_id: 'STU-2024-1034',
    national_id: '23456789012',
    risk_score: 62.3,
    priority: 'high',
    created_at: '2024-06-15T10:45:00Z',
    status: 'in_review',
    notes: ['Suspicious geographic patterns', 'Inconsistent external data']
  },
  {
    id: 'HR-003',
    student_id: 'STU-2024-0765', 
    national_id: '123456789012',
    risk_score: 45.7,
    priority: 'medium',
    assigned_to: 'Officer A. Otieno',
    created_at: '2024-06-15T11:20:00Z',
    status: 'completed',
    notes: ['Minor document inconsistencies', 'Resolved after manual review']
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
  const [selectedCase, setSelectedCase] = useState(null)
  const [filter, setFilter] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')

  const filteredCases = mockReviewCases.filter(case_ => {
    const matchesFilter = filter === 'all' || case_.priority === filter
    const matchesSearch = case_.student_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          case_.national_id.includes(searchTerm)
    return matchesFilter && matchesSearch
  })

  const handleCaseReview = (caseId: string) => {
    // In real implementation, this would open detailed review interface
    console.log('Opening case for review:', caseId)
  }

  const handleAssignCase = (caseId: string, officer: string) => {
    // In real implementation, this would assign case to officer
    console.log('Assigning case:', caseId, 'to officer:', officer)
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
              <p className="text-2xl font-bold text-yellow-600">{mockReviewCases.filter(c => c.status === 'pending').length}</p>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-slate-600">In Progress</p>
              <p className="text-2xl font-bold text-blue-600">{mockReviewCases.filter(c => c.status === 'in_review').length}</p>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-slate-600">Completed Today</p>
              <p className="text-2xl font-bold text-emerald-600">{mockReviewCases.filter(c => c.status === 'completed').length}</p>
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
        {filteredCases.map((case_) => (
          <div key={case_.id} className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow">
            {/* Case Header */}
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-slate-900">{case_.student_id}</h3>
                <p className="text-sm text-slate-500">National ID: {case_.national_id}</p>
              </div>
              <div className="flex flex-col items-end space-y-2">
                <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getPriorityColor(case_.priority)}`}>
                  {case_.priority.toUpperCase()}
                </span>
                <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getStatusColor(case_.status)}`}>
                  {case_.status.replace('_', ' ').toUpperCase()}
                </span>
              </div>
            </div>

            {/* Risk Score */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-700">Risk Score</span>
                <span className={`text-lg font-bold ${
                  case_.risk_score >= 70 ? 'text-red-600' :
                  case_.risk_score >= 50 ? 'text-orange-600' :
                  case_.risk_score >= 30 ? 'text-yellow-600' : 'text-green-600'
                }`}>
                  {case_.risk_score.toFixed(1)}
                </span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    case_.risk_score >= 70 ? 'bg-red-500' :
                    case_.risk_score >= 50 ? 'bg-orange-500' :
                    case_.risk_score >= 30 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(case_.risk_score, 100)}%` }}
                ></div>
              </div>
            </div>

            {/* Assignment */}
            {case_.assigned_to && (
              <div className="mb-4 p-3 bg-slate-50 rounded-lg">
                <p className="text-sm font-medium text-slate-700">Assigned to: {case_.assigned_to}</p>
              </div>
            )}

            {/* Notes */}
            <div className="mb-4">
              <h4 className="text-sm font-medium text-slate-700 mb-2">Review Notes:</h4>
              <ul className="space-y-1">
                {case_.notes.map((note, index) => (
                  <li key={index} className="text-sm text-slate-600 flex items-start">
                    <span className="w-2 h-2 bg-emerald-500 rounded-full mt-1.5 mr-2 flex-shrink-0"></span>
                    {note}
                  </li>
                ))}
              </ul>
            </div>

            {/* Actions */}
            <div className="flex space-x-3">
              <button
                onClick={() => handleCaseReview(case_.id)}
                className="flex-1 px-4 py-2 bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-700 transition-colors"
              >
                Review Case
              </button>
              {case_.status === 'pending' && (
                <button
                  onClick={() => handleAssignCase(case_.id, 'Available Officer')}
                  className="px-4 py-2 bg-slate-600 text-white font-medium rounded-lg hover:bg-slate-700 transition-colors"
                >
                  Assign
                </button>
              )}
            </div>

            {/* Timestamp */}
            <div className="mt-4 pt-4 border-t border-slate-200">
              <p className="text-xs text-slate-500">
                Created: {new Date(case_.created_at).toLocaleString('en-KE')}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {filteredCases.length === 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-slate-900 mb-2">No cases found</h3>
          <p className="text-sm text-slate-500">Try adjusting your search or filter criteria</p>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg hover:bg-emerald-100 transition-colors">
            <h4 className="font-medium text-emerald-700 mb-1">Assign Critical Cases</h4>
            <p className="text-sm text-emerald-600">Auto-assign high-priority cases</p>
          </button>
          <button className="p-4 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 transition-colors">
            <h4 className="font-medium text-blue-700 mb-1">Bulk Review</h4>
            <p className="text-sm text-blue-600">Review multiple cases</p>
          </button>
          <button className="p-4 bg-slate-50 border border-slate-200 rounded-lg hover:bg-slate-100 transition-colors">
            <h4 className="font-medium text-slate-700 mb-1">Generate Report</h4>
            <p className="text-sm text-slate-600">Export review statistics</p>
          </button>
        </div>
      </div>
    </div>
  )
}
