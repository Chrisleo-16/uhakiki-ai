"use client"

import { useState, useEffect } from 'react'

// API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Types for fraud analytics data
type FraudTrend = {
  date: string
  fraudAttempts: number
  fraudPrevented: number
  riskScore: number
  savings: number
}

type Hotspot = {
  county: string
  constituency: string
  riskScore: number
  fraudCases: number
  lat?: number
  lng?: number
}

type FraudRing = {
  id: string
  name: string
  members: number
  detectedDate: string
  riskLevel: 'critical' | 'high' | 'medium' | 'low'
  totalAmount: number
  status: 'disrupted' | 'investigating' | 'active'
  patterns: string[]
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-KE', {
    style: 'currency',
    currency: 'KES',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

function getRiskColor(score: number): string {
  if (score >= 60) return 'text-red-600 bg-red-50 border-red-200'
  if (score >= 40) return 'text-orange-600 bg-orange-50 border-orange-200'
  if (score >= 20) return 'text-yellow-600 bg-yellow-50 border-yellow-200'
  return 'text-green-600 bg-green-50 border-green-200'
}

function getRiskLevelColor(level: string): string {
  switch (level) {
    case 'critical': return 'text-red-700 bg-red-50 border-red-200'
    case 'high': return 'text-orange-700 bg-orange-50 border-orange-200'
    case 'medium': return 'text-yellow-700 bg-yellow-50 border-yellow-200'
    case 'low': return 'text-green-700 bg-green-50 border-green-200'
    default: return 'text-gray-700 bg-gray-50 border-gray-200'
  }
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'disrupted': return 'text-emerald-700 bg-emerald-50 border-emerald-200'
    case 'investigating': return 'text-yellow-700 bg-yellow-50 border-yellow-200'
    case 'active': return 'text-red-700 bg-red-50 border-red-200'
    default: return 'text-gray-700 bg-gray-50 border-gray-200'
  }
}

export default function FraudAnalyticsPage() {
  const [selectedTimeframe, setSelectedTimeframe] = useState('6months')
  const [fraudTrends, setFraudTrends] = useState<FraudTrend[]>([])
  const [hotspots, setHotspots] = useState<Hotspot[]>([])
  const [fraudRings, setFraudRings] = useState<FraudRing[]>([])
  const [totalSavings, setTotalSavings] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch fraud analytics data from backend
  const fetchFraudData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const [trendsResponse, hotspotsResponse, ringsResponse] = await Promise.all([
        fetch(`${API_BASE}/api/v1/fraud-trends`).then(res => res.json()),
        fetch(`${API_BASE}/api/v1/hotspots`).then(res => res.json()),
        fetch(`${API_BASE}/api/v1/fraud-rings`).then(res => res.json())
      ])
      
      setFraudTrends(trendsResponse || [])
      setHotspots(hotspotsResponse || [])
      setFraudRings(ringsResponse || [])
      
      // Calculate total savings
      const savings = trendsResponse.reduce((sum: number, trend: FraudTrend) => sum + (trend.savings || 0), 0)
      setTotalSavings(savings)
      
    } catch (err) {
      console.error('Failed to fetch fraud data:', err)
      setError('Failed to load fraud analytics data. Please check your connection.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchFraudData()
  }, [selectedTimeframe])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-600">Loading Fraud Analytics...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center max-w-md">
          <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2">Analytics Error</h3>
          <p className="text-slate-600 mb-4">{error}</p>
          <button
            onClick={fetchFraudData}
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
            <h2 className="text-xl font-semibold text-slate-900">Fraud Analytics & Intelligence</h2>
            <p className="text-sm text-slate-500">Advanced fraud pattern detection and economic impact analysis</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <p className="text-sm font-medium text-slate-600">Total Savings</p>
              <p className="text-2xl font-bold text-emerald-600">{formatCurrency(totalSavings)}</p>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-slate-600">Fraud Rings Detected</p>
              <p className="text-2xl font-bold text-red-600">{fraudRings.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Timeframe Selector */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Analysis Period</h3>
            <p className="text-sm text-slate-500">Select timeframe for fraud trend analysis</p>
          </div>
          <div className="flex space-x-2">
            {['1month', '3months', '6months', '1year'].map((period) => (
              <button
                key={period}
                onClick={() => setSelectedTimeframe(period)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  selectedTimeframe === period
                    ? 'bg-emerald-600 text-white'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                {period === '1month' ? '1 Month' : 
                 period === '3months' ? '3 Months' :
                 period === '6months' ? '6 Months' : '1 Year'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Fraud Trends Chart */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Fraud Detection Trends</h3>
        <div className="space-y-3">
          {fraudTrends.length > 0 ? (
            fraudTrends.map((trend, index) => (
            <div key={trend.date} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors">
              <div className="flex items-center space-x-4">
                <div className={`w-3 h-3 rounded-full ${trend.riskScore > 30 ? 'bg-red-500' : 'bg-emerald-500'}`}></div>
                <div>
                  <p className="text-sm font-medium text-slate-900">{trend.date}</p>
                  <p className="text-xs text-slate-500">Risk Score: {trend.riskScore}</p>
                </div>
              </div>
              <div className="flex items-center space-x-6">
                <div className="text-center">
                  <p className="text-sm font-medium text-slate-900">{trend.fraudAttempts}</p>
                  <p className="text-xs text-slate-500">Attempts</p>
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium text-emerald-600">{trend.fraudPrevented}</p>
                  <p className="text-xs text-slate-500">Prevented</p>
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium text-emerald-600">{((trend.fraudPrevented / trend.fraudAttempts) * 100).toFixed(1)}%</p>
                  <p className="text-xs text-slate-500">Success Rate</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-emerald-600">{formatCurrency(trend.savings)}</p>
                  <p className="text-xs text-slate-500">Savings</p>
                </div>
              </div>
            </div>
          ))
            ) : (
              <div className="text-center py-8">
                <p className="text-slate-500">No fraud trends data available</p>
              </div>
            )}
          </div>
        </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Geographic Hotspots */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Identity Farming Hotspots</h3>
          <div className="space-y-3">
            {hotspots.length > 0 ? (
              hotspots.map((hotspot, index) => (
              <div key={`${hotspot.county}-${hotspot.constituency}`} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors">
                <div className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${hotspot.riskScore > 50 ? 'bg-red-600' : hotspot.riskScore > 30 ? 'bg-yellow-600' : 'bg-emerald-600'}`}></div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">{hotspot.county}</p>
                    <p className="text-xs text-slate-500">{hotspot.constituency}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`text-sm font-medium px-2 py-1 rounded-full text-xs ${getRiskColor(hotspot.riskScore)}`}>
                    Risk: {hotspot.riskScore}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">{hotspot.fraudCases} cases</p>
                </div>
              </div>
            ))
            ) : (
              <div className="text-center py-8">
                <p className="text-slate-500">No hotspot data available</p>
              </div>
            )}
          </div>
        </div>

        {/* Fraud Ring Intelligence */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Fraud Ring Intelligence</h3>
          <div className="space-y-3">
            {fraudRings.length > 0 ? (
              fraudRings.map((ring) => (
              <div key={ring.id} className="p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="text-sm font-medium text-slate-900">{ring.name}</p>
                    <p className="text-xs text-slate-500">{ring.members} members • Detected {ring.detectedDate}</p>
                  </div>
                  <div className="flex flex-col items-end space-y-1">
                    <span className={`text-xs font-medium px-2 py-1 rounded-full ${getRiskLevelColor(ring.riskLevel)}`}>
                      {ring.riskLevel.toUpperCase()}
                    </span>
                    <span className={`text-xs font-medium px-2 py-1 rounded-full ${getStatusColor(ring.status)}`}>
                      {ring.status.toUpperCase()}
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex flex-wrap gap-1">
                    {ring.patterns?.map((pattern, idx) => (
                      <span key={idx} className="text-xs bg-slate-200 text-slate-700 px-2 py-1 rounded">
                        {pattern}
                      </span>
                    )) || <span className="text-xs text-slate-500">No patterns detected</span>}
                  </div>
                  <p className="text-sm font-medium text-emerald-600">{formatCurrency(ring.totalAmount)}</p>
                </div>
              </div>
            ))
            ) : (
              <div className="text-center py-8">
                <p className="text-slate-500">No fraud ring data available</p>
              </div>
            )}
          </div>
        </div>
      </div>

        {/* Economic Impact Analysis */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Economic Impact Analysis</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-emerald-50 rounded-lg">
            <p className="text-2xl font-bold text-emerald-600">{formatCurrency(totalSavings)}</p>
            <p className="text-sm text-emerald-700">Total Savings</p>
            <p className="text-xs text-emerald-600 mt-1">6-month period</p>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <p className="text-2xl font-bold text-blue-600">
              {fraudTrends.reduce((sum, trend) => sum + trend.fraudPrevented, 0)}
            </p>
            <p className="text-sm text-blue-700">Fraud Cases Prevented</p>
            <p className="text-xs text-blue-600 mt-1">Across all counties</p>
          </div>
          <div className="text-center p-4 bg-yellow-50 rounded-lg">
            <p className="text-2xl font-bold text-yellow-600">
              {fraudRings.reduce((sum, ring) => sum + ring.members, 0)}
            </p>
            <p className="text-sm text-yellow-700">Fraud Ring Members</p>
            <p className="text-xs text-yellow-600 mt-1">Identified & tracked</p>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <p className="text-2xl font-bold text-red-600">
              {fraudRings.filter(ring => ring.status === 'active').length}
            </p>
            <p className="text-sm text-red-700">Active Investigations</p>
            <p className="text-xs text-red-600 mt-1">Currently monitoring</p>
          </div>
        </div>
      </div>

      {/* Pattern Analysis */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Common Fraud Patterns</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <h4 className="font-medium text-red-700 mb-2">Document Synthesis</h4>
            <p className="text-sm text-red-600 mb-2">AI-generated or manipulated documents</p>
            <div className="flex items-center justify-between">
              <span className="text-xs text-red-500">High Priority</span>
              <span className="text-sm font-bold text-red-600">67 cases</span>
            </div>
          </div>
          <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
            <h4 className="font-medium text-orange-700 mb-2">Identity Farming</h4>
            <p className="text-sm text-orange-600 mb-2">Multiple applications with synthetic identities</p>
            <div className="flex items-center justify-between">
              <span className="text-xs text-orange-500">Medium Priority</span>
              <span className="text-sm font-bold text-orange-600">45 cases</span>
            </div>
          </div>
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <h4 className="font-medium text-yellow-700 mb-2">Voice Spoofing</h4>
            <p className="text-sm text-yellow-600 mb-2">Synthetic or replayed voice samples</p>
            <div className="flex items-center justify-between">
              <span className="text-xs text-yellow-500">Emerging Threat</span>
              <span className="text-sm font-bold text-yellow-600">23 cases</span>
            </div>
          </div>
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h4 className="font-medium text-blue-700 mb-2">Geographic Clustering</h4>
            <p className="text-sm text-blue-600 mb-2">Coordinated applications from same areas</p>
            <div className="flex items-center justify-between">
              <span className="text-xs text-blue-500">Monitoring</span>
              <span className="text-sm font-bold text-blue-600">89 cases</span>
            </div>
          </div>
          <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
            <h4 className="font-medium text-purple-700 mb-2">Template Reuse</h4>
            <p className="text-sm text-purple-600 mb-2">Repeated document patterns detected</p>
            <div className="flex items-center justify-between">
              <span className="text-xs text-purple-500">Low Priority</span>
              <span className="text-sm font-bold text-purple-600">34 cases</span>
            </div>
          </div>
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg">
            <h4 className="font-medium text-slate-700 mb-2">System Exploitation</h4>
            <p className="text-sm text-slate-600 mb-2">Technical vulnerabilities being leveraged</p>
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500">Investigating</span>
              <span className="text-sm font-bold text-slate-600">12 cases</span>
            </div>
          </div>
        </div>
      </div>
  </div>
  )
}
