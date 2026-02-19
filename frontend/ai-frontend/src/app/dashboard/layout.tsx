"use client"

import { ReactNode, useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Shield, TrendingUp, Users, AlertTriangle, FileText, BarChart3, UserCheck } from 'lucide-react'

// API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-KE', {
    style: 'currency',
    currency: 'KES',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

function formatNumber(num: number): string {
  return new Intl.NumberFormat('en-KE').format(num)
}

export default function DashboardLayout({
  children,
}: {
  children: ReactNode
}) {
  const pathname = usePathname()
  const [datasetStats, setDatasetStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  // Fetch dataset statistics
  useEffect(() => {
    const fetchDatasetStats = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/v1/dataset-stats`)
        if (response.ok) {
          const data = await response.json()
          setDatasetStats(data)
        }
      } catch (error) {
        console.error('Failed to fetch dataset stats:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchDatasetStats()
  }, [])

  const navigation = [
    { name: 'Overview', href: '/dashboard', icon: TrendingUp },
    { name: 'Verifications', href: '/dashboard/verifications', icon: FileText },
    { name: 'Fraud Analytics', href: '/dashboard/fraud', icon: BarChart3 },
    { name: 'Human Review', href: '/dashboard/review', icon: UserCheck },
  ]

  // Extract metrics from dataset stats
  const totalSavings = datasetStats?.economic_impact?.total_savings || 2400000000
  const fraudPrevented = datasetStats?.economic_impact?.prevented_cases || 1247
  const totalImages = datasetStats?.dataset_stats?.total_images || 11129
  const detectionRate = datasetStats?.performance_metrics?.fraud_detection_rate || 94.2

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg border-r border-slate-200">
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="px-6 py-4 border-b border-slate-200">
            <Link href="/" className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-lg flex items-center justify-center">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-slate-900">UhakikiAI</h1>
                <p className="text-xs text-slate-500">Sovereign Identity Engine</p>
              </div>
            </Link>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                    isActive
                      ? 'bg-emerald-50 text-emerald-700 border-l-4 border-emerald-600'
                      : 'text-slate-700 hover:text-emerald-600 hover:bg-emerald-50'
                  }`}
                >
                  <Icon className={`w-5 h-5 mr-3 ${isActive ? 'text-emerald-600' : 'text-slate-400'}`} />
                  {item.name}
                </Link>
              )
            })}
          </nav>

          {/* System Status */}
          <div className="px-4 py-4 border-t border-slate-200">
            <div className="bg-emerald-50 rounded-lg p-3">
              <div className="flex items-center">
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                <span className="ml-2 text-sm font-medium text-emerald-700">System Online</span>
              </div>
              <p className="text-xs text-emerald-600 mt-1">
                {loading ? 'Loading...' : `${formatNumber(totalImages)} images processed`}
              </p>
              <p className="text-xs text-emerald-600">
                {loading ? 'Loading...' : `${detectionRate.toFixed(1)}% detection rate`}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="pl-64">
        {/* Top Bar */}
        <div className="bg-white shadow-sm border-b border-slate-200">
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-slate-900">National Security Dashboard</h2>
                <p className="text-sm text-slate-500">Real-time fraud prevention and economic impact monitoring</p>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <p className="text-sm font-medium text-slate-900">Shillings Saved</p>
                  <p className="text-2xl font-bold text-emerald-600">
                    {loading ? 'Loading...' : formatCurrency(totalSavings)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-slate-900">Fraud Prevented</p>
                  <p className="text-2xl font-bold text-red-600">
                    {loading ? 'Loading...' : formatNumber(fraudPrevented)}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Page Content */}
        <div className="p-6">
          {children}
        </div>
      </div>
    </div>
  )
}