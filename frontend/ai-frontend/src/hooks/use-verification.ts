import { useState, useCallback } from 'react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface VerificationResult {
  authentic: boolean
  confidence: number
  mse_score?: number
  extracted_name?: string
  id_number?: string
  county?: string
  dob?: string
  timestamp: string
}

export interface RiskFactor {
  factor: string
  score: number
  status: 'pass' | 'warning' | 'fail'
}

export function useVerification() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<VerificationResult | null>(null)

  const verifyDocument = useCallback(async (file: File) => {
    setIsLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`${API_BASE}/api/v1/document/verify`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Verification failed: ${response.statusText}`)
      }

      const data = await response.json()
      
      setResult({
        authentic: data.authentic ?? true,
        confidence: data.confidence ?? 95,
        mse_score: data.mse_score,
        extracted_name: data.extracted_name,
        id_number: data.id_number,
        county: data.county,
        dob: data.dob,
        timestamp: new Date().toISOString(),
      })

      return data
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An error occurred'
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const reset = useCallback(() => {
    setResult(null)
    setError(null)
    setIsLoading(false)
  }, [])

  return {
    verifyDocument,
    isLoading,
    error,
    result,
    reset,
  }
}

export function useDashboardMetrics() {
  const [metrics, setMetrics] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchMetrics = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE}/api/v1/analytics/overview`)
      if (!response.ok) {
        throw new Error('Failed to fetch metrics')
      }
      const data = await response.json()
      setMetrics(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }, [])

  return { metrics, loading, error, fetchMetrics }
}

export function useRealTimeStats() {
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/analytics/realtime`)
      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (err) {
      console.error('Failed to fetch real-time stats:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  return { stats, loading, fetchStats }
}
