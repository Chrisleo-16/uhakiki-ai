"use client"

import { useState, useEffect } from 'react'

// Mock fraud analytics data
const mockFraudTrends = [
  { date: '2024-01', fraudAttempts: 342, fraudPrevented: 298, riskScore: 28.5, savings: 89000000 },
  { date: '2024-02', fraudAttempts: 387, fraudPrevented: 312, riskScore: 31.2, savings: 95000000 },
  { date: '2024-03', fraudAttempts: 423, fraudPrevented: 367, riskScore: 26.8, savings: 112000000 },
  { date: '2024-04', fraudAttempts: 398, fraudPrevented: 341, riskScore: 29.1, savings: 105000000 },
  { date: '2024-05', fraudAttempts: 456, fraudPrevented: 389, riskScore: 32.4, savings: 128000000 },
  { date: '2024-06', fraudAttempts: 412, fraudPrevented: 356, riskScore: 24.7, savings: 98000000 },
]

const mockHotspots = [
  { county: 'Nairobi', constituency: 'Kamukunji', riskScore: 67.8, fraudCases: 89, lat: -1.2921, lng: 36.8219 },
  { county: 'Mombasa', constituency: 'Mvita', riskScore: 58.3, fraudCases: 67, lat: -4.0435, lng: 39.6682 },
  { county: 'Kisumu', constituency: 'Kisumu Central', riskScore: 45.2, fraudCases: 43, lat: -0.0917, lng: 34.7680 },
  { county: 'Nakuru', constituency: 'Nakuru Town East', riskScore: 39.7, fraudCases: 38, lat: -0.3031, lng: 36.0800 },
  { county: 'Kiambu', constituency: 'Thika', riskScore: 35.1, fraudCases: 29, lat: -1.0320, lng: 37.0715 },
  { county: 'Uasin Gishu', constituency: 'Eldoret North', riskScore: 32.4, fraudCases: 25, lat: 0.5143, lng: 35.2698 },
]

const mockFraudRings = [
  { id: 'FR-001', name: 'Education Cartel Network', members: 47, detectedDate: '2024-03-15', riskLevel: 'critical', totalAmount: 45000000, status: 'disrupted', patterns: ['Document synthesis', 'Identity farming', 'Coordinated applications'] },
  { id: 'FR-002', name: 'Identity Farming Operation', members: 23, detectedDate: '2024-05-22', riskLevel: 'high', totalAmount: 28000000, status: 'investigating', patterns: ['Voice spoofing', 'Multiple applications', 'Geographic clustering'] },
  { id: 'FR-003', name: 'Document Synthesis Ring', members: 15, detectedDate: '2024-06-08', riskLevel: 'medium', totalAmount: 12000000, status: 'active', patterns: ['Deepfake documents', 'Template reuse', 'Batch processing'] },
  { id: 'FR-004', name: 'Scholarship Fraud Network', members: 31, detectedDate: '2024-04-12', riskLevel: 'high', totalAmount: 35000000, status: 'disrupted', patterns: ['False claims', 'Collusion', 'System exploitation'] },
]

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
  const [totalSavings, setTotalSavings] = useState(627000000)

  // Calculate total savings from trends
  useEffect(() => {
    const savings = mockFraudTrends.reduce((sum, trend) => sum + trend.savings, 0)
    setTotalSavings(savings)
  }, [])

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
              <p className="text-2xl font-bold text-red-600">{mockFraudRings.length}</p>
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
          {mockFraudTrends.map((trend, index) => (
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
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Geographic Hotspots */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Identity Farming Hotspots</h3>
          <div className="space-y-3">
            {mockHotspots.map((hotspot, index) => (
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
            ))}
          </div>
        </div>

        {/* Fraud Ring Intelligence */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Fraud Ring Intelligence</h3>
          <div className="space-y-3">
            {mockFraudRings.map((ring) => (
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
                    {ring.patterns.map((pattern, idx) => (
                      <span key={idx} className="text-xs bg-slate-200 text-slate-700 px-2 py-1 rounded">
                        {pattern}
                      </span>
                    ))}
                  </div>
                  <p className="text-sm font-medium text-emerald-600">{formatCurrency(ring.totalAmount)}</p>
                </div>
              </div>
            ))}
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
              {mockFraudTrends.reduce((sum, trend) => sum + trend.fraudPrevented, 0)}
            </p>
            <p className="text-sm text-blue-700">Fraud Cases Prevented</p>
            <p className="text-xs text-blue-600 mt-1">Across all counties</p>
          </div>
          <div className="text-center p-4 bg-yellow-50 rounded-lg">
            <p className="text-2xl font-bold text-yellow-600">
              {mockFraudRings.reduce((sum, ring) => sum + ring.members, 0)}
            </p>
            <p className="text-sm text-yellow-700">Fraud Ring Members</p>
            <p className="text-xs text-yellow-600 mt-1">Identified & tracked</p>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <p className="text-2xl font-bold text-red-600">
              {mockFraudRings.filter(ring => ring.status === 'active').length}
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
