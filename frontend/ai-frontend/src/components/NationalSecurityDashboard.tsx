"use client"

import { useState, useEffect } from 'react'
import { 
  Shield, 
  AlertTriangle, 
  TrendingUp, 
  MapPin, 
  Users, 
  FileText, 
  Activity,
  Eye,
  Download,
  Calendar,
  BarChart3,
  Globe,
  Lock
} from 'lucide-react'

interface SecurityMetrics {
  totalVerifications: number
  fraudAttempts: number
  fraudPrevented: number
  highRiskCases: number
  averageRiskScore: number
  systemAccuracy: number
  processingTime: number
}

interface FraudPattern {
  id: string
  type: string
  frequency: number
  severity: 'high' | 'medium' | 'low'
  description: string
  trend: 'increasing' | 'decreasing' | 'stable'
  locations: string[]
  affectedDocuments: string[]
}

interface GeographicHotspot {
  county: string
  constituency: string
  riskScore: number
  fraudCases: number
  totalAttempts: number
  riskFactors: string[]
}

interface SecurityAlert {
  id: string
  type: 'critical' | 'high' | 'medium' | 'low'
  title: string
  description: string
  timestamp: string
  location?: string
  affectedUsers: number
  status: 'active' | 'investigating' | 'resolved'
}

export default function NationalSecurityDashboard() {
  const [metrics, setMetrics] = useState<SecurityMetrics>({
    totalVerifications: 0,
    fraudAttempts: 0,
    fraudPrevented: 0,
    highRiskCases: 0,
    averageRiskScore: 0,
    systemAccuracy: 0,
    processingTime: 0
  })

  const [fraudPatterns, setFraudPatterns] = useState<FraudPattern[]>([])
  const [hotspots, setHotspots] = useState<GeographicHotspot[]>([])
  const [alerts, setAlerts] = useState<SecurityAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d' | '90d'>('7d')

  useEffect(() => {
    fetchSecurityData()
  }, [timeRange])

  const fetchSecurityData = async () => {
    try {
      setLoading(true)
      
      // Fetch real security metrics
      const [metricsRes, patternsRes, hotspotsRes, alertsRes] = await Promise.all([
        fetch(`http://localhost:8000/api/v1/security/metrics?timeRange=${timeRange}`),
        fetch(`http://localhost:8000/api/v1/security/fraud-patterns?timeRange=${timeRange}`),
        fetch(`http://localhost:8000/api/v1/security/hotspots?timeRange=${timeRange}`),
        fetch(`http://localhost:8000/api/v1/security/alerts?timeRange=${timeRange}`)
      ])

      // Handle metrics
      if (metricsRes.ok) {
        const metricsData = await metricsRes.json()
        setMetrics(metricsData)
      } else {
        // Fallback mock data
        setMetrics({
          totalVerifications: 1247,
          fraudAttempts: 89,
          fraudPrevented: 78,
          highRiskCases: 12,
          averageRiskScore: 23.4,
          systemAccuracy: 96.8,
          processingTime: 1.8
        })
      }

      // Handle fraud patterns
      if (patternsRes.ok) {
        const patternsData = await patternsRes.json()
        setFraudPatterns(patternsData)
      } else {
        // Fallback mock data
        setFraudPatterns([
          {
            id: '1',
            type: 'Document Synthesis',
            frequency: 34,
            severity: 'high',
            description: 'AI-generated documents with perfect edges and uniform noise',
            trend: 'increasing',
            locations: ['Nairobi', 'Mombasa'],
            affectedDocuments: ['National ID', 'KCSE Certificate']
          },
          {
            id: '2',
            type: 'Deepfake Manipulation',
            frequency: 28,
            severity: 'high',
            description: 'Facial deepfakes in biometric verification',
            trend: 'increasing',
            locations: ['Nairobi', 'Kisumu'],
            affectedDocuments: ['Passport Photos', 'ID Photos']
          },
          {
            id: '3',
            type: 'Identity Farming',
            frequency: 15,
            severity: 'medium',
            description: 'Multiple applications from similar biometric patterns',
            trend: 'stable',
            locations: ['Nakuru', 'Eldoret'],
            affectedDocuments: ['All Document Types']
          }
        ])
      }

      // Handle geographic hotspots
      if (hotspotsRes.ok) {
        const hotspotsData = await hotspotsRes.json()
        setHotspots(hotspotsData)
      } else {
        // Fallback mock data
        setHotspots([
          {
            county: 'Nairobi',
            constituency: 'Westlands',
            riskScore: 78.5,
            fraudCases: 23,
            totalAttempts: 145,
            riskFactors: ['urban_center', 'high_population', 'border_region']
          },
          {
            county: 'Mombasa',
            constituency: 'Kisauni',
            riskScore: 65.2,
            fraudCases: 18,
            totalAttempts: 98,
            riskFactors: ['border_region', 'tourist_destination']
          }
        ])
      }

      // Handle security alerts
      if (alertsRes.ok) {
        const alertsData = await alertsRes.json()
        setAlerts(alertsData)
      } else {
        // Fallback mock data
        setAlerts([
          {
            id: '1',
            type: 'critical',
            title: 'Suspicious Deepfake Pattern Detected',
            description: 'Multiple verification attempts with AI-generated facial features',
            timestamp: new Date().toISOString(),
            location: 'Nairobi',
            affectedUsers: 5,
            status: 'active'
          },
          {
            id: '2',
            type: 'high',
            title: 'Document Forgery Cluster',
            description: 'Cluster of synthesized national ID cards detected',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            location: 'Mombasa',
            affectedUsers: 3,
            status: 'investigating'
          }
        ])
      }

    } catch (error) {
      console.error('Failed to fetch security data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200'
      case 'high': return 'text-red-600 bg-red-50 border-red-200'
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'low': return 'text-emerald-600 bg-emerald-50 border-emerald-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'increasing': return <TrendingUp className="w-4 h-4 text-red-500" />
      case 'decreasing': return <TrendingUp className="w-4 h-4 text-emerald-500 rotate-180" />
      case 'stable': return <Activity className="w-4 h-4 text-blue-500" />
      default: return <Activity className="w-4 h-4 text-gray-500" />
    }
  }

  const exportSecurityReport = async () => {
    const reportData = {
      generated_at: new Date().toISOString(),
      time_range: timeRange,
      metrics,
      fraud_patterns: fraudPatterns,
      geographic_hotspots: hotspots,
      security_alerts: alerts
    }

    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `security_report_${timeRange}_${Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-600">Loading Security Dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Shield className="w-8 h-8 text-emerald-600" />
            <div>
              <h1 className="text-2xl font-bold text-slate-900">National Security Dashboard</h1>
              <p className="text-slate-600">Real-time fraud detection and threat analysis</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as any)}
              className="px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
            </select>
            <button
              onClick={exportSecurityReport}
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 flex items-center space-x-2"
            >
              <Download className="w-4 h-4" />
              <span>Export Report</span>
            </button>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-emerald-100 rounded-lg">
              <Eye className="w-6 h-6 text-emerald-600" />
            </div>
            <span className="text-2xl font-bold text-slate-900">{metrics.totalVerifications.toLocaleString()}</span>
          </div>
          <h3 className="font-medium text-slate-900">Total Verifications</h3>
          <p className="text-sm text-slate-500">Identity checks performed</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-red-100 rounded-lg">
              <AlertTriangle className="w-6 h-6 text-red-600" />
            </div>
            <span className="text-2xl font-bold text-slate-900">{metrics.fraudAttempts}</span>
          </div>
          <h3 className="font-medium text-slate-900">Fraud Attempts</h3>
          <p className="text-sm text-slate-500">Suspicious activities detected</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-emerald-100 rounded-lg">
              <Lock className="w-6 h-6 text-emerald-600" />
            </div>
            <span className="text-2xl font-bold text-slate-900">{metrics.fraudPrevented}</span>
          </div>
          <h3 className="font-medium text-slate-900">Fraud Prevented</h3>
          <p className="text-sm text-slate-500">Successfully blocked attempts</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-blue-100 rounded-lg">
              <BarChart3 className="w-6 h-6 text-blue-600" />
            </div>
            <span className="text-2xl font-bold text-slate-900">{metrics.systemAccuracy.toFixed(1)}%</span>
          </div>
          <h3 className="font-medium text-slate-900">System Accuracy</h3>
          <p className="text-sm text-slate-500">Detection accuracy rate</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Fraud Patterns */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-slate-900">Fraud Patterns</h2>
            <FileText className="w-5 h-5 text-slate-400" />
          </div>
          <div className="space-y-4">
            {fraudPatterns.map((pattern) => (
              <div key={pattern.id} className="p-4 border border-slate-200 rounded-lg">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h4 className="font-medium text-slate-900">{pattern.type}</h4>
                    <p className="text-sm text-slate-600 mt-1">{pattern.description}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(pattern.severity)}`}>
                      {pattern.severity.toUpperCase()}
                    </span>
                    {getTrendIcon(pattern.trend)}
                  </div>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-500">Frequency: {pattern.frequency} cases</span>
                  <span className="text-slate-500">
                    Locations: {pattern.locations.join(', ')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Geographic Hotspots */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-slate-900">Geographic Hotspots</h2>
            <MapPin className="w-5 h-5 text-slate-400" />
          </div>
          <div className="space-y-4">
            {hotspots.map((hotspot, index) => (
              <div key={index} className="p-4 border border-slate-200 rounded-lg">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h4 className="font-medium text-slate-900">
                      {hotspot.county}, {hotspot.constituency}
                    </h4>
                    <div className="flex items-center space-x-4 mt-1 text-sm text-slate-600">
                      <span>Risk Score: {hotspot.riskScore.toFixed(1)}</span>
                      <span>{hotspot.fraudCases} cases</span>
                    </div>
                  </div>
                  <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                    hotspot.riskScore > 70 ? 'bg-red-100 text-red-700' :
                    hotspot.riskScore > 50 ? 'bg-yellow-100 text-yellow-700' :
                    'bg-emerald-100 text-emerald-700'
                  }`}>
                    {hotspot.riskScore > 70 ? 'HIGH RISK' :
                     hotspot.riskScore > 50 ? 'MEDIUM RISK' : 'LOW RISK'}
                  </div>
                </div>
                <div className="text-sm text-slate-500">
                  Risk Factors: {hotspot.riskFactors.join(', ')}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Security Alerts */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-slate-900">Security Alerts</h2>
          <AlertTriangle className="w-5 h-5 text-slate-400" />
        </div>
        <div className="space-y-4">
          {alerts.map((alert) => (
            <div key={alert.id} className={`p-4 border-2 rounded-lg ${getSeverityColor(alert.type)}`}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h4 className="font-medium text-slate-900">{alert.title}</h4>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(alert.type)}`}>
                      {alert.type.toUpperCase()}
                    </span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      alert.status === 'active' ? 'bg-red-100 text-red-700' :
                      alert.status === 'investigating' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-emerald-100 text-emerald-700'
                    }`}>
                      {alert.status.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 mb-2">{alert.description}</p>
                  <div className="flex items-center space-x-4 text-sm text-slate-500">
                    <span className="flex items-center space-x-1">
                      <Calendar className="w-4 h-4" />
                      <span>{new Date(alert.timestamp).toLocaleString()}</span>
                    </span>
                    {alert.location && (
                      <span className="flex items-center space-x-1">
                        <MapPin className="w-4 h-4" />
                        <span>{alert.location}</span>
                      </span>
                    )}
                    <span className="flex items-center space-x-1">
                      <Users className="w-4 h-4" />
                      <span>{alert.affectedUsers} affected</span>
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
