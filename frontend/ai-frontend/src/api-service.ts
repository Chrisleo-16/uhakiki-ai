// Simple API service for UhakikiAI backend
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface ApiResponse<T> {
  data?: T
  error?: string
  message?: string
}

export interface VerificationRequest {
  national_id: string
  student_id: string
  document_image: File
  face_image?: File
  voice_audio?: File
  liveness_video?: File
}

export interface DashboardMetrics {
  total_verifications: number
  fraud_prevented: number
  shillings_saved: number
  average_risk_score: number
  processing_time: number
  system_health: number
}

class ApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      return { data }
    } catch (error) {
      console.error('API request failed:', error)
      return { error: error instanceof Error ? error.message : 'Unknown error' }
    }
  }

  async uploadFile<T>(
    endpoint: string,
    formData: FormData
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      return { data }
    } catch (error) {
      console.error('File upload failed:', error)
      return { error: error instanceof Error ? error.message : 'Upload failed' }
    }
  }

  // Dashboard endpoints
  async getDashboardMetrics(): Promise<ApiResponse<DashboardMetrics>> {
    return this.request<DashboardMetrics>('/api/v1/health')
  }

  async getVerificationStatus(trackingId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/v1/verification-status/${trackingId}`)
  }

  // Verification endpoints
  async submitVerification(request: VerificationRequest): Promise<ApiResponse<any>> {
    const formData = new FormData()
    
    formData.append('national_id', request.national_id)
    formData.append('student_id', request.student_id)
    formData.append('document_image', request.document_image)
    
    if (request.face_image) {
      formData.append('face_image', request.face_image)
    }
    
    if (request.voice_audio) {
      formData.append('voice_audio', request.voice_audio)
    }
    
    if (request.liveness_video) {
      formData.append('liveness_video', request.liveness_video)
    }

    return this.uploadFile<any>('/api/v1/comprehensive-verification', formData)
  }

  async enrollVoiceProfile(studentId: string, audioSamples: File[]): Promise<ApiResponse<any>> {
    const formData = new FormData()
    formData.append('student_id', studentId)
    
    audioSamples.forEach((audio, index) => {
      formData.append(`audio_samples`, audio)
    })

    return this.uploadFile<any>('/api/v1/enroll-voice-profile', formData)
  }

  // Document analysis
  async analyzeDocument(document: File): Promise<ApiResponse<any>> {
    const formData = new FormData()
    formData.append('document', document)

    return this.uploadFile<any>('/api/v1/verify/document', formData)
  }

  // System health
  async getSystemHealth(): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v1/health')
  }
}

export const apiService = new ApiService()
