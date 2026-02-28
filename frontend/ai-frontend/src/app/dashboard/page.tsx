"use client"

import { useState, useEffect } from 'react'
import { Shield, TrendingUp, Users, AlertTriangle, MapPin, Clock, CheckCircle, XCircle, Loader2, ArrowRight, FileCheck, GraduationCap } from 'lucide-react'
import Link from 'next/link'
import { uhakikiAPI, type VerificationMetrics, type RealTimeStats, type FraudTrend, type GeographicHotspot, type FraudRing } from '../../lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { KenyaMap } from '@/components/verification'
import { Progress } from '@/components/ui/progress'

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-KE', {
    style: 'currency',
    currency: 'KES',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

function formatNumber(num: number): string {
  if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B'
  if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M'
  if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K'
  return num.toString()
}

function getRiskColor(score: number): string {
  if (score >= 60) return 'text-red-600 bg-red-50 border-red-200'
  if (score >= 40) return 'text-orange-600 bg-orange-50 border-orange-200'
  if (score >= 20) return 'text-yellow-600 bg-yellow-50 border-yellow-200'
  return 'text-green-600 bg-green-50 border-green-200'
}

export default function DashboardOverview() {
  const [metrics, setMetrics] = useState<VerificationMetrics | null>(null)
  const [realTimeStats, setRealTimeStats] = useState<RealTimeStats | null>(null)
  const [fraudTrends, setFraudTrends] = useState<FraudTrend[]>([])
  const [hotspots, setHotspots] = useState<GeographicHotspot[]>([])
  const [fraudRings, setFraudRings] = useState<FraudRing[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date())

  // Fetch data from backend
  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Parallel API calls for better performance
      const [
        metricsData,
        realTimeData,
        trendsData,
        hotspotsData,
        ringsData
      ] = await Promise.all([
        uhakikiAPI.getVerificationMetrics(),
        uhakikiAPI.getRealTimeStats(),
        uhakikiAPI.getFraudTrends(),
        uhakikiAPI.getGeographicHotspots(),
        uhakikiAPI.getFraudRings()
      ])

      setMetrics(metricsData)
      setRealTimeStats(realTimeData)
      setFraudTrends(trendsData)
      setHotspots(hotspotsData)
      setFraudRings(ringsData)
      setLastUpdated(new Date())
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err)
      setError('Failed to load dashboard data. Please check your connection.')
    } finally {
      setLoading(false)
    }
  }

  // Initial data fetch
  useEffect(() => {
    fetchDashboardData()
  }, [])

  // Real-time updates for stats
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const stats = await uhakikiAPI.getRealTimeStats()
        setRealTimeStats(stats)
        setLastUpdated(new Date())
      } catch (err) {
        console.error('Failed to update real-time stats:', err)
      }
    }, 5000) // Update every 5 seconds

    return () => clearInterval(interval)
  }, [])

  // Refresh all data
  const handleRefresh = () => {
    fetchDashboardData()
  }

  if (loading && !metrics) {
    return (
      <div className="space-y-6">
        {/* Header Skeleton */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <Skeleton className="h-8 w-64 mb-2" />
                <Skeleton className="h-4 w-96" />
              </div>
              <div className="flex items-center gap-4">
                <Skeleton className="h-12 w-32" />
                <Skeleton className="h-12 w-32" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Metrics Skeletons */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <Skeleton className="h-20 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Chart Skeleton */}
        <Card>
          <CardContent className="p-6">
            <Skeleton className="h-64 w-full" />
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center max-w-md">
          <XCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-2">Dashboard Error</h3>
          <p className="text-slate-600 mb-4">{error}</p>
          <button
            onClick={handleRefresh}
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
      {/* Header with Refresh */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">UhakikiAI Command Center</h2>
            <p className="text-sm text-slate-500">Real-time fraud detection and identity verification dashboard</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <p className="text-xs text-slate-500">Last Updated</p>
              <p className="text-sm font-medium text-slate-600">
                {lastUpdated.toLocaleTimeString()}
              </p>
            </div>
            <button
              onClick={handleRefresh}
              className="px-3 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors flex items-center space-x-2"
              disabled={loading}
            >
              <Loader2 className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Connection Status */}
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${metrics ? 'bg-emerald-500' : 'bg-red-500'}`}></div>
          <span className="text-sm text-slate-600">
            {metrics ? 'Connected to UhakikiAI Backend' : 'Backend Connection Lost'}
          </span>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-600">Total Verifications</p>
              <p className="text-2xl font-bold text-slate-900">
                {metrics ? formatNumber(metrics.totalVerifications) : '--'}
              </p>
              <p className="text-xs text-emerald-600 mt-1">Live from backend</p>
            </div>
            <div className="w-12 h-12 bg-emerald-50 rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-emerald-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-600">Fraud Prevented</p>
              <p className="text-2xl font-bold text-slate-900">
                {metrics ? formatNumber(metrics.fraudPrevented) : '--'}
              </p>
              <p className="text-xs text-red-600 mt-1">
                {metrics ? `${((metrics.fraudPrevented / metrics.totalVerifications) * 100).toFixed(1)}% detection rate` : '--'}
              </p>
            </div>
            <div className="w-12 h-12 bg-red-50 rounded-lg flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-red-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-600">Shillings Saved</p>
              <p className="text-2xl font-bold text-emerald-600">
                {metrics ? formatCurrency(metrics.shillingsSaved) : '--'}
              </p>
              <p className="text-xs text-emerald-600 mt-1">KES funding gap bridged</p>
            </div>
            <div className="w-12 h-12 bg-emerald-50 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-emerald-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-600">System Health</p>
              <p className="text-2xl font-bold text-slate-900">
                {metrics ? `${metrics.systemHealth}%` : '--'}
              </p>
              <p className="text-xs text-emerald-600 mt-1">
                {metrics ? (metrics.systemHealth >= 95 ? 'Optimal' : 'Good') : '--'}
              </p>
            </div>
            <div className="w-12 h-12 bg-slate-50 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-slate-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Real-time Statistics */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Real-time System Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="text-center">
            <p className="text-sm font-medium text-slate-600">Active Verifications</p>
            <p className="text-xl font-bold text-blue-600">
              {realTimeStats ? realTimeStats.activeVerifications : '--'}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-slate-600">Queue Length</p>
            <p className="text-xl font-bold text-yellow-600">
              {realTimeStats ? realTimeStats.queueLength : '--'}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-slate-600">Avg Processing Time</p>
            <p className="text-xl font-bold text-slate-900">
              {realTimeStats ? `${realTimeStats.averageProcessingTime}s` : '--'}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-slate-600">System Load</p>
            <p className="text-xl font-bold text-slate-900">
              {realTimeStats ? `${realTimeStats.systemLoad.toFixed(1)}%` : '--'}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-slate-600">Error Rate</p>
            <p className="text-xl font-bold text-red-600">
              {realTimeStats ? `${realTimeStats.errorRate}%` : '--'}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-slate-600">Throughput</p>
            <p className="text-xl font-bold text-emerald-600">
              {realTimeStats ? `${realTimeStats.throughput}/min` : '--'}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Fraud Trends Chart */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Fraud Detection Trends</h3>
          <div className="space-y-3">
            {fraudTrends.slice(-6).map((trend, index) => (
              <div key={trend.date} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${trend.riskScore > 30 ? 'bg-red-500' : 'bg-emerald-500'}`}></div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">{trend.date}</p>
                    <p className="text-xs text-slate-500">Risk Score: {trend.riskScore}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-slate-900">{trend.fraudPrevented}/{trend.fraudAttempts}</p>
                  <p className="text-xs text-emerald-600">{((trend.fraudPrevented / trend.fraudAttempts) * 100).toFixed(1)}% prevented</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Geographic Hotspots - Kenya Map */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900">Geographic Risk Map</h3>
            <Badge variant="outline" className="text-xs">
              Kenya Counties
            </Badge>
          </div>
          <KenyaMap />
        </div>
      </div>

      {/* Fraud Rings Detection */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Organized Fraud Ring Patterns</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-700">Ring ID</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-700">Name</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-700">Members</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-700">Risk Level</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-700">Total Amount</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-700">Status</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-700">Detected</th>
              </tr>
            </thead>
            <tbody>
              {fraudRings.map((ring) => (
                <tr key={ring.id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="py-3 px-4 text-sm text-slate-900">{ring.id}</td>
                  <td className="py-3 px-4 text-sm text-slate-900">{ring.name}</td>
                  <td className="py-3 px-4 text-sm text-slate-900">{ring.members}</td>
                  <td className="py-3 px-4">
                    <span className={`text-sm font-medium px-2 py-1 rounded-full text-xs ${getRiskColor(ring.riskLevel === 'critical' ? 85 : ring.riskLevel === 'high' ? 65 : 45)}`}>
                      {ring.riskLevel.toUpperCase()}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-sm text-slate-900">{formatCurrency(ring.totalAmount)}</td>
                  <td className="py-3 px-4">
                    <span className={`text-sm font-medium px-2 py-1 rounded-full text-xs ${
                      ring.status === 'disrupted' ? 'bg-emerald-100 text-emerald-700' :
                      ring.status === 'investigating' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      {ring.status.replace('_', ' ').toUpperCase()}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-sm text-slate-500">{ring.detectedDate}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <QuickActions />
    </div>
  )
}

// Quick Actions Component for easy verification access
function QuickActions() {
  return (
    <div className="fixed bottom-6 right-6">
      <div className="flex flex-col gap-3">
        <Link href="/auth/verify-id">
          <Button className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg shadow-emerald-500/25 hover-lift gap-2">
            <FileCheck className="w-5 h-5" />
            Verify Document
          </Button>
        </Link>
        <Link href="/dashboard/student/verifications">
          <Button variant="outline" className="shadow-lg gap-2">
            <GraduationCap className="w-5 h-5" />
            Student Portal
          </Button>
        </Link>
      </div>
    </div>
  )
}
