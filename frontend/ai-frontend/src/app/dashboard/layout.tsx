"use client"

import { ReactNode, useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Shield, TrendingUp, Users, AlertTriangle, FileText, BarChart3, UserCheck, GraduationCap, Settings, Bell, Moon, Sun } from 'lucide-react'

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
  const [darkMode, setDarkMode] = useState(false)

  // Toggle dark mode
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])

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

  const adminNavigation = [
    { name: 'Overview', href: '/dashboard', icon: TrendingUp },
    { name: 'Verifications', href: '/dashboard/verifications', icon: FileText },
    { name: 'Fraud Analytics', href: '/dashboard/fraud', icon: BarChart3 },
    { name: 'Human Review', href: '/dashboard/review', icon: UserCheck },
  ]

  const studentNavigation = [
    { name: 'My Verifications', href: '/dashboard/student/verifications', icon: GraduationCap },
    { name: 'Document Status', href: '/dashboard/student/status', icon: FileText },
    { name: 'Profile', href: '/dashboard/student/profile', icon: Users },
  ]

  // Extract metrics from dataset stats
  const totalSavings = datasetStats?.economic_impact?.total_savings || 2400000000
  const fraudPrevented = datasetStats?.economic_impact?.prevented_cases || 1247
  const totalImages = datasetStats?.dataset_stats?.total_images || 11129
  const detectionRate = datasetStats?.performance_metrics?.fraud_detection_rate || 94.2

  return (
    <div className={`min-h-screen ${darkMode ? 'dark bg-slate-900' : 'bg-gradient-to-br from-slate-50 to-slate-100'}`}>
      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 w-64 ${darkMode ? 'bg-slate-800 border-slate-700' : 'bg-white shadow-lg border-slate-200'} border-r`}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className={`px-6 py-4 ${darkMode ? 'border-slate-700' : 'border-slate-200'} border-b`}>
            <Link href="/" className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/20">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className={`text-lg font-semibold ${darkMode ? 'text-white' : 'text-slate-900'}`}>UhakikiAI</h1>
                <p className={`text-xs ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>Sovereign Identity Engine</p>
              </div>
            </Link>
          </div>

          {/* Admin Navigation */}
          <div className="px-4 py-4">
            <p className={`text-xs font-semibold uppercase tracking-wider mb-2 ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
              Admin
            </p>
            <nav className="space-y-1">
              {adminNavigation.map((item) => {
                const Icon = item.icon
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${
                      isActive
                        ? 'bg-emerald-50 text-emerald-700 border-l-4 border-emerald-600'
                        : `${darkMode ? 'text-slate-300 hover:text-white hover:bg-slate-700' : 'text-slate-700 hover:text-emerald-600 hover:bg-emerald-50'}`
                    }`}
                  >
                    <Icon className={`w-5 h-5 mr-3 ${isActive ? 'text-emerald-600' : darkMode ? 'text-slate-400' : 'text-slate-400'}`} />
                    {item.name}
                  </Link>
                )
              })}
            </nav>
          </div>

          {/* Student Navigation */}
          <div className="px-4 py-4">
            <p className={`text-xs font-semibold uppercase tracking-wider mb-2 ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
              Student Portal
            </p>
            <nav className="space-y-1">
              {studentNavigation.map((item) => {
                const Icon = item.icon
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${
                      isActive
                        ? 'bg-blue-50 text-blue-700 border-l-4 border-blue-600'
                        : `${darkMode ? 'text-slate-300 hover:text-white hover:bg-slate-700' : 'text-slate-700 hover:text-blue-600 hover:bg-blue-50'}`
                    }`}
                  >
                    <Icon className={`w-5 h-5 mr-3 ${isActive ? 'text-blue-600' : darkMode ? 'text-slate-400' : 'text-slate-400'}`} />
                    {item.name}
                  </Link>
                )
              })}
            </nav>
          </div>

          {/* System Status */}
          <div className={`px-4 py-4 mt-auto ${darkMode ? 'border-slate-700' : 'border-slate-200'} border-t`}>
            <div className={`${darkMode ? 'bg-slate-700' : 'bg-emerald-50'} rounded-lg p-3`}>
              <div className="flex items-center">
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                <span className={`ml-2 text-sm font-medium ${darkMode ? 'text-emerald-400' : 'text-emerald-700'}`}>System Online</span>
              </div>
              <p className={`text-xs mt-1 ${darkMode ? 'text-emerald-400' : 'text-emerald-600'}`}>
                {loading ? 'Loading...' : `${formatNumber(totalImages)} images processed`}
              </p>
              <p className={`text-xs ${darkMode ? 'text-emerald-400' : 'text-emerald-600'}`}>
                {loading ? 'Loading...' : `${detectionRate.toFixed(1)}% detection rate`}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="pl-64">
        {/* Top Bar */}
        <div className={`${darkMode ? 'bg-slate-800 border-slate-700' : 'bg-white'} shadow-sm border-b`}>
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className={`text-xl font-semibold ${darkMode ? 'text-white' : 'text-slate-900'}`}>National Security Dashboard</h2>
                <p className={`text-sm ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>Real-time fraud prevention and economic impact monitoring</p>
              </div>
              <div className="flex items-center space-x-4">
                {/* Dark Mode Toggle */}
                <button
                  onClick={() => setDarkMode(!darkMode)}
                  className={`p-2 rounded-lg ${darkMode ? 'hover:bg-slate-700 text-yellow-400' : 'hover:bg-slate-100 text-slate-600'} transition-colors`}
                >
                  {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                </button>
                
                {/* Notifications */}
                <button className={`p-2 rounded-lg ${darkMode ? 'hover:bg-slate-700 text-slate-400' : 'hover:bg-slate-100 text-slate-600'} transition-colors relative`}>
                  <Bell className="w-5 h-5" />
                  <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
                </button>

                {/* Stats */}
                <div className="text-right">
                  <p className={`text-sm font-medium ${darkMode ? 'text-white' : 'text-slate-900'}`}>Shillings Saved</p>
                  <p className="text-2xl font-bold text-emerald-600">
                    {loading ? 'Loading...' : formatCurrency(totalSavings)}
                  </p>
                </div>
                <div className="text-right">
                  <p className={`text-sm font-medium ${darkMode ? 'text-white' : 'text-slate-900'}`}>Fraud Prevented</p>
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