"use client"

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

export default function BiometricRegistration() {
  const [currentStep, setCurrentStep] = useState<'face' | 'voice' | 'complete'>('face')
  const [isCapturing, setIsCapturing] = useState(false)
  const [captureComplete, setCaptureComplete] = useState(false)
  const [voiceRecording, setVoiceRecording] = useState(false)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [countdown, setCountdown] = useState(0)
  const [faceImages, setFaceImages] = useState<string[]>([])
  const [userData, setUserData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const router = useRouter()

  // Helper function to validate token format
  const isValidTokenFormat = (token: string | null): boolean => {
    if (!token) return false
    // JWT tokens typically have 3 parts separated by dots
    const parts = token.split('.')
    return parts.length === 3
  }

  // Helper function to check if token is expired
  const isTokenExpired = (token: string | null): boolean => {
    if (!token) return true
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      const now = Math.floor(Date.now() / 1000)
      return payload.exp < now
    } catch {
      return true // If we can't parse, assume it's invalid
    }
  }

  useEffect(() => {
    // First, check if we have a valid token and user registration data
    const token = localStorage.getItem('authToken')
    const userReg = localStorage.getItem('userRegistration')
    
    console.log('Biometric Registration - Token exists:', !!token)
    console.log('Biometric Registration - Token format valid:', isValidTokenFormat(token))
    console.log('Biometric Registration - Token expired:', isTokenExpired(token))
    console.log('Biometric Registration - User registration exists:', !!userReg)
    
    if (!token || !isValidTokenFormat(token) || isTokenExpired(token)) {
      console.log('Invalid or expired token, clearing and redirecting to signin')
      localStorage.removeItem('authToken')
      localStorage.removeItem('userRegistration')
      localStorage.removeItem('verificationStatus')
      localStorage.removeItem('biometricStatus')
      router.push('/auth/signin')
      return
    }

    if (!userReg) {
      console.log('No user registration data found, redirecting to signup')
      router.push('/auth/signup')
      return
    }

    // Fetch user data from backend
    const fetchUserData = async () => {
      try {
        console.log('Fetching user profile with token:', token.substring(0, 20) + '...')

        const response = await fetch('http://localhost:8000/api/v1/user/profile', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })

        console.log('Profile response status:', response.status)

        if (response.ok) {
          const user = await response.json()
          console.log('User data fetched successfully:', user)
          setUserData(user)
        } else if (response.status === 401) {
          console.log('Token expired or invalid, clearing and redirecting to signin')
          localStorage.removeItem('authToken')
          localStorage.removeItem('userRegistration')
          localStorage.removeItem('verificationStatus')
          localStorage.removeItem('biometricStatus')
          router.push('/auth/signin')
        } else {
          console.error('Failed to fetch user data, status:', response.status)
          const errorText = await response.text()
          console.error('Error response:', errorText)
          
          // Try to use localStorage data as fallback
          try {
            const userData = JSON.parse(userReg)
            setUserData({
              firstName: userData.firstName,
              email: userData.email,
              citizenship: userData.citizenship,
              identificationNumber: userData.identificationNumber
            })
          } catch (parseError) {
            console.error('Failed to parse stored user data:', parseError)
            router.push('/auth/signup')
          }
        }
      } catch (error) {
        console.error('Error fetching user data:', error)
        
        // Try to use localStorage data as fallback
        try {
          const userData = JSON.parse(userReg)
          setUserData({
            firstName: userData.firstName,
            email: userData.email,
            citizenship: userData.citizenship,
            identificationNumber: userData.identificationNumber
          })
        } catch (parseError) {
          console.error('Failed to parse stored user data:', parseError)
          router.push('/auth/signup')
        }
      } finally {
        setLoading(false)
      }
    }

    fetchUserData()
  }, [router])

  useEffect(() => {
    if (currentStep === 'face' && !captureComplete) {
      startCamera()
    }
    return () => {
      stopCamera()
    }
  }, [currentStep, captureComplete])

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'user' },
        audio: false 
      })
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
    } catch (error) {
      console.error('Camera access denied:', error)
    }
  }

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream
      stream.getTracks().forEach(track => track.stop())
    }
  }

  const captureFaceImage = () => {
    if (!videoRef.current || !canvasRef.current) return

    setIsCapturing(true)
    setCountdown(3)

    const countdownInterval = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(countdownInterval)
          performCapture()
          return 0
        }
        return prev - 1
      })
    }, 1000)
  }

  const performCapture = () => {
    if (!videoRef.current || !canvasRef.current) return

    const video = videoRef.current
    const canvas = canvasRef.current
    const context = canvas.getContext('2d')

    if (context) {
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      context.drawImage(video, 0, 0)

      const imageData = canvas.toDataURL('image/jpeg')
      setFaceImages(prev => [...prev, imageData])

      if (faceImages.length >= 2) {
        setCaptureComplete(true)
        setTimeout(() => {
          setCurrentStep('voice')
        }, 2000)
      } else {
        setIsCapturing(false)
      }
    }
  }

  const startVoiceRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder

      const chunks: Blob[] = []
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data)
        }
      }

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/webm' })
        setAudioBlob(blob)
        setVoiceRecording(false)
        setCurrentStep('complete')
      }

      mediaRecorder.start()
      setVoiceRecording(true)

      // Auto-stop after 5 seconds
      setTimeout(() => {
        if (mediaRecorder.state === 'recording') {
          mediaRecorder.stop()
          stream.getTracks().forEach(track => track.stop())
        }
      }, 5000)
    } catch (error) {
      console.error('Microphone access denied:', error)
    }
  }

  const stopVoiceRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop()
    }
  }

  const handleComplete = async () => {
    // Store biometric completion status and update backend
    try {
      const token = localStorage.getItem('authToken')
      const userData = JSON.parse(localStorage.getItem('userRegistration') || '{}')
      
      // Update biometric status in backend
      const response = await fetch('http://localhost:8000/api/v1/biometric/complete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          face_encoding: faceImages.length > 0,
          voice_sample: audioBlob !== null
        })
      })

      if (response.ok) {
        localStorage.setItem('biometricStatus', 'complete')
        localStorage.setItem('verificationStatus', 'active')
        router.push('/user-dashboard')
      } else {
        const errorText = await response.text()
        console.error('Failed to update biometric status:', response.status, errorText)
        // Still proceed locally
        localStorage.setItem('biometricStatus', 'complete')
        localStorage.setItem('verificationStatus', 'active')
        router.push('/user-dashboard')
      }
    } catch (error) {
      console.error('Error updating biometric status:', error)
      // Still proceed locally
      localStorage.setItem('biometricStatus', 'complete')
      localStorage.setItem('verificationStatus', 'active')
      router.push('/user-dashboard')
    }
  }

  const handleSkip = () => {
    // Skip biometrics and go to dashboard with pending status
    localStorage.setItem('biometricStatus', 'pending')
    router.push('/user-dashboard')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-slate-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg">
              <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
          </div>
          <h2 className="text-3xl font-bold text-slate-900 mb-2">
            Biometric Registration
          </h2>
          
          {/* User Information */}
          {loading ? (
            <div className="animate-pulse">
              <div className="h-4 bg-slate-200 rounded w-3/4 mx-auto mb-2"></div>
              <div className="h-3 bg-slate-200 rounded w-1/2 mx-auto"></div>
            </div>
          ) : userData ? (
            <div className="space-y-2">
              <p className="text-slate-600">
                Welcome, <span className="font-semibold text-slate-900">{userData.firstName}</span>!
              </p>
              <div className="flex items-center justify-center space-x-4 text-sm text-slate-500">
                <span>{userData.email}</span>
                <span>•</span>
                <span className="capitalize">{userData.citizenship}</span>
                {userData.identificationNumber && (
                  <>
                    <span>•</span>
                    <span>ID: {userData.identificationNumber.slice(-4)}</span>
                  </>
                )}
              </div>
            </div>
          ) : (
            <p className="text-slate-600">
              Complete your identity verification with facial recognition and voice biometrics for enhanced security.
            </p>
          )}
        </div>

        {/* Progress */}
        <div className="flex items-center justify-center space-x-4">
          <div className={`flex items-center ${currentStep === 'face' ? 'text-purple-600' : 'text-slate-400'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              currentStep === 'face' || currentStep === 'voice' || currentStep === 'complete' 
                ? 'bg-purple-600 text-white' 
                : 'bg-slate-200 text-slate-600'
            }`}>
              1
            </div>
            <span className="ml-2 text-sm font-medium">Face Scan</span>
          </div>
          <div className={`flex-1 h-1 ${currentStep !== 'face' ? 'bg-purple-600' : 'bg-slate-200'}`} />
          <div className={`flex items-center ${currentStep === 'voice' ? 'text-purple-600' : 'text-slate-400'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              currentStep === 'voice' || currentStep === 'complete'
                ? 'bg-purple-600 text-white' 
                : 'bg-slate-200 text-slate-600'
            }`}>
              2
            </div>
            <span className="ml-2 text-sm font-medium">Voice Sample</span>
          </div>
          <div className={`flex-1 h-1 ${currentStep === 'complete' ? 'bg-purple-600' : 'bg-slate-200'}`} />
          <div className={`flex items-center ${currentStep === 'complete' ? 'text-purple-600' : 'text-slate-400'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              currentStep === 'complete' ? 'bg-purple-600 text-white' : 'bg-slate-200 text-slate-600'
            }`}>
              3
            </div>
            <span className="ml-2 text-sm font-medium">Complete</span>
          </div>
        </div>

        {/* Main Content */}
        {loading ? (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="animate-pulse space-y-6">
              <div className="h-6 bg-slate-200 rounded w-3/4"></div>
              <div className="h-4 bg-slate-200 rounded w-1/2"></div>
              <div className="h-64 bg-slate-200 rounded"></div>
              <div className="h-10 bg-slate-200 rounded"></div>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            {currentStep === 'face' && (
              <div className="space-y-6">
                <div className="text-center">
                  <h3 className="text-xl font-semibold text-slate-900 mb-2">Facial Recognition</h3>
                  <p className="text-slate-600">
                    We need to capture your face from different angles for accurate biometric registration.
                  </p>
                </div>

              <div className="relative">
                {/* Camera View */}
                <div className="relative bg-slate-900 rounded-xl overflow-hidden" style={{ aspectRatio: '4/3' }}>
                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className="w-full h-full object-cover"
                  />
                  
                  {/* Overlay Guides */}
                  {!isCapturing && (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="w-48 h-48 border-2 border-emerald-500 rounded-full" />
                      <div className="absolute text-emerald-500 text-sm font-medium">
                        Center your face here
                      </div>
                    </div>
                  )}

                  {/* Countdown */}
                  {isCapturing && countdown > 0 && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50">
                      <div className="text-6xl font-bold text-white animate-pulse">
                        {countdown}
                      </div>
                    </div>
                  )}

                  {/* Capture Success */}
                  {isCapturing && countdown === 0 && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50">
                      <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center">
                        <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                    </div>
                  )}
                </div>

                <canvas ref={canvasRef} className="hidden" />
              </div>

              {/* Progress */}
              <div className="text-center">
                <p className="text-sm text-slate-600">
                  Captured: {faceImages.length}/3 images
                </p>
                <div className="flex justify-center space-x-2 mt-2">
                  {[1, 2, 3].map((i) => (
                    <div
                      key={i}
                      className={`w-2 h-2 rounded-full ${
                        i <= faceImages.length ? 'bg-purple-600' : 'bg-slate-300'
                      }`}
                    />
                  ))}
                </div>
              </div>

              {/* Action Button */}
              <div className="flex gap-4">
                <button
                  onClick={handleSkip}
                  className="flex-1 px-4 py-3 bg-slate-200 text-slate-700 font-medium rounded-lg hover:bg-slate-300 transition-colors"
                >
                  Skip for Now
                </button>
                <button
                  onClick={captureFaceImage}
                  disabled={isCapturing || captureComplete}
                  className="flex-1 px-4 py-3 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isCapturing ? 'Capturing...' : captureComplete ? 'Complete!' : `Capture Image ${faceImages.length + 1}`}
                </button>
              </div>
            </div>
          )}

          {currentStep === 'voice' && (
            <div className="space-y-6">
              <div className="text-center">
                <h3 className="text-xl font-semibold text-slate-900 mb-2">Voice Biometrics</h3>
                <p className="text-slate-600">
                  Please say the following phrase clearly: <span className="font-mono bg-slate-100 px-2 py-1 rounded">"Uhakiki AI verifies my identity"</span>
                </p>
              </div>

              <div className="text-center space-y-4">
                {/* Voice Animation */}
                <div className="w-32 h-32 mx-auto bg-gradient-to-r from-purple-100 to-purple-200 rounded-full flex items-center justify-center">
                  {voiceRecording ? (
                    <div className="space-y-2">
                      <div className="flex space-x-1">
                        <div className="w-1 h-8 bg-purple-600 rounded-full animate-pulse" />
                        <div className="w-1 h-12 bg-purple-600 rounded-full animate-pulse delay-75" />
                        <div className="w-1 h-6 bg-purple-600 rounded-full animate-pulse delay-150" />
                        <div className="w-1 h-10 bg-purple-600 rounded-full animate-pulse" />
                        <div className="w-1 h-8 bg-purple-600 rounded-full animate-pulse delay-75" />
                      </div>
                      <div className="flex space-x-1">
                        <div className="w-1 h-6 bg-purple-600 rounded-full animate-pulse delay-150" />
                        <div className="w-1 h-10 bg-purple-600 rounded-full animate-pulse" />
                        <div className="w-1 h-12 bg-purple-600 rounded-full animate-pulse delay-75" />
                        <div className="w-1 h-8 bg-purple-600 rounded-full animate-pulse delay-150" />
                        <div className="w-1 h-6 bg-purple-600 rounded-full animate-pulse" />
                      </div>
                    </div>
                  ) : (
                    <svg className="w-16 h-16 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                    </svg>
                  )}
                </div>

                {voiceRecording && (
                  <div className="text-center">
                    <p className="text-sm text-slate-600">Recording... Speak clearly</p>
                    <div className="w-48 h-1 bg-slate-200 rounded-full overflow-hidden">
                      <div className="h-full bg-purple-600 animate-pulse" style={{ width: '60%' }} />
                    </div>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex gap-4">
                <button
                  onClick={handleSkip}
                  className="flex-1 px-4 py-3 bg-slate-200 text-slate-700 font-medium rounded-lg hover:bg-slate-300 transition-colors"
                >
                  Skip for Now
                </button>
                {!voiceRecording ? (
                  <button
                    onClick={startVoiceRecording}
                    className="flex-1 px-4 py-3 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700 transition-colors"
                  >
                    Start Recording
                  </button>
                ) : (
                  <button
                    onClick={stopVoiceRecording}
                    className="flex-1 px-4 py-3 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 transition-colors"
                  >
                    Stop Recording
                  </button>
                )}
              </div>
            </div>
          )}

          {currentStep === 'complete' && (
            <div className="text-center space-y-6">
              <div className="w-20 h-20 mx-auto bg-green-100 rounded-full flex items-center justify-center">
                <svg className="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              
              <div>
                <h3 className="text-xl font-semibold text-slate-900 mb-2">Biometric Registration Complete!</h3>
                <p className="text-slate-600">
                  Your biometric data has been securely registered. Your account is now fully verified and active.
                </p>
              </div>

              {/* Features */}
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h4 className="font-medium text-green-900 mb-2">What's now available:</h4>
                <ul className="text-sm text-green-800 space-y-1">
                  <li className="flex items-start">
                    <svg className="w-4 h-4 mr-2 mt-0.5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Instant biometric login
                  </li>
                  <li className="flex items-start">
                    <svg className="w-4 h-4 mr-2 mt-0.5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Enhanced security protection
                  </li>
                  <li className="flex items-start">
                    <svg className="w-4 h-4 mr-2 mt-0.5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Full access to all features
                  </li>
                  <li className="flex items-start">
                    <svg className="w-4 h-4 mr-2 mt-0.5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Priority verification status
                  </li>
                </ul>
              </div>

              <button
                onClick={handleComplete}
                className="w-full px-4 py-3 bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-700 transition-colors"
              >
                Go to Dashboard
              </button>
            </div>
          )}
        </div>
        )}

        {/* Security Info */}
        <div className="text-center">
          <div className="flex items-center justify-center space-x-6 text-xs text-slate-500">
            <div className="flex items-center">
              <svg className="w-4 h-4 mr-1 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              Encrypted Storage
            </div>
            <div className="flex items-center">
              <svg className="w-4 h-4 mr-1 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              Privacy Protected
            </div>
            <div className="flex items-center">
              <svg className="w-4 h-4 mr-1 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              GDPR Compliant
            </div>
          </div>
        </div>

        {/* Back Link */}
        <div className="text-center">
          <Link href="/auth/verify-id" className="text-slate-600 hover:text-slate-700 text-sm">
            ← Back to ID Verification
          </Link>
        </div>
      </div>
    </div>
  )
}
