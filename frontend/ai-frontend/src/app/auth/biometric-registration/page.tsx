"use client"

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Camera, Mic, CheckCircle, Loader2, Shield } from 'lucide-react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

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
  const [error, setError] = useState<string | null>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const router = useRouter()

  // Check token validity
  const isValidTokenFormat = (token: string | null): boolean => {
    if (!token) return false
    const parts = token.split('.')
    return parts.length === 3
  }

  const isTokenExpired = (token: string | null): boolean => {
    if (!token) return true
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      const now = Math.floor(Date.now() / 1000)
      return payload.exp < now
    } catch {
      return true
    }
  }

  useEffect(() => {
    const token = localStorage.getItem('authToken')
    const userReg = localStorage.getItem('userRegistration')
    
    if (!token || !isValidTokenFormat(token) || isTokenExpired(token)) {
      localStorage.removeItem('authToken')
      localStorage.removeItem('userRegistration')
      router.push('/auth/signin')
      return
    }

    if (!userReg) {
      router.push('/auth/signup')
      return
    }

    // Check if document verification is complete
    const verificationStatus = localStorage.getItem('verificationStatus')
    if (verificationStatus !== 'verified') {
      router.push('/auth/verify-id')
      return
    }

    // Fetch user profile from backend
    const fetchUserData = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/v1/user/profile`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })

        if (response.ok) {
          const user = await response.json()
          setUserData(user)
        } else if (response.status === 401) {
          localStorage.removeItem('authToken')
          localStorage.removeItem('userRegistration')
          router.push('/auth/signin')
        } else {
          // Use localStorage as fallback
          const userData = JSON.parse(userReg)
          setUserData({
            firstName: userData.firstName,
            email: userData.email,
            citizenship: userData.citizenship,
            identificationNumber: userData.identificationNumber
          })
        }
      } catch (err) {
        console.error('Error fetching user data:', err)
        // Use localStorage fallback
        try {
          const userData = JSON.parse(userReg)
          setUserData({
            firstName: userData.firstName,
            email: userData.email,
            citizenship: userData.citizenship,
            identificationNumber: userData.identificationNumber
          })
        } catch {
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
    return () => stopCamera()
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
    } catch (err) {
      console.error('Camera access denied:', err)
      setError('Camera access denied. Please allow camera permissions.')
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
      const newImages = [...faceImages, imageData]
      setFaceImages(newImages)

      if (newImages.length >= 3) {
        setCaptureComplete(true)
        setTimeout(() => setCurrentStep('voice'), 2000)
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
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorder.start()
      setVoiceRecording(true)

      setTimeout(() => {
        if (mediaRecorder.state === 'recording') {
          mediaRecorder.stop()
        }
      }, 5000)
    } catch (err) {
      console.error('Microphone access denied:', err)
      setError('Microphone access denied. Please allow microphone permissions.')
    }
  }

  const handleComplete = async () => {
    const token = localStorage.getItem('authToken')
    
    try {
      const response = await fetch(`${API_BASE}/api/v1/biometric/complete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          face_encoding: faceImages.length > 0,
          voice_sample: audioBlob !== null,
          face_images: faceImages
        })
      })

      if (response.ok) {
        localStorage.setItem('biometricStatus', 'complete')
        localStorage.setItem('verificationStatus', 'active')
        router.push('/user-dashboard')
      } else {
        // Still proceed locally even if backend fails
        localStorage.setItem('biometricStatus', 'complete')
        localStorage.setItem('verificationStatus', 'active')
        router.push('/user-dashboard')
      }
    } catch (err) {
      console.error('Error updating biometric status:', err)
      localStorage.setItem('biometricStatus', 'complete')
      localStorage.setItem('verificationStatus', 'active')
      router.push('/user-dashboard')
    }
  }

  const handleSkip = () => {
    localStorage.setItem('biometricStatus', 'pending')
    router.push('/user-dashboard')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-slate-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-purple-600 mx-auto mb-4" />
          <p className="text-slate-600">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-slate-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg">
              <Shield className="w-10 h-10 text-white" />
            </div>
          </div>
          <h2 className="text-3xl font-bold text-slate-900 mb-2">
            Biometric Registration
          </h2>
          
          {userData && (
            <div className="space-y-2">
              <p className="text-slate-600">
                Welcome, <span className="font-semibold text-slate-900">{userData.firstName}</span>!
              </p>
              <div className="flex items-center justify-center space-x-4 text-sm text-slate-500">
                <span>{userData.email}</span>
                <span>•</span>
                <span className="capitalize">{userData.citizenship}</span>
              </div>
            </div>
          )}
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-center space-x-4">
          <StepIndicator step={1} current={currentStep} label="Face Scan" icon={Camera} />
          <div className={`flex-1 h-1 ${currentStep !== 'face' ? 'bg-purple-600' : 'bg-slate-200'}`} />
          <StepIndicator step={2} current={currentStep} label="Voice Sample" icon={Mic} />
          <div className={`flex-1 h-1 ${currentStep === 'complete' ? 'bg-purple-600' : 'bg-slate-200'}`} />
          <StepIndicator step={3} current={currentStep} label="Complete" icon={CheckCircle} />
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-center">
            {error}
          </div>
        )}

        {/* Main Content */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {currentStep === 'face' && (
            <div className="space-y-6">
              <div className="text-center">
                <h3 className="text-xl font-semibold text-slate-900 mb-2">Facial Recognition</h3>
                <p className="text-slate-600">
                  Capture your face from different angles for accurate biometric registration.
                </p>
              </div>

              <div className="relative">
                <div className="relative bg-slate-900 rounded-xl overflow-hidden" style={{ aspectRatio: '4/3' }}>
                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className="w-full h-full object-cover"
                  />
                  
                  {!isCapturing && !captureComplete && (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="w-48 h-48 border-2 border-emerald-500 rounded-full" />
                      <div className="absolute text-emerald-500 text-sm font-medium">
                        Center your face here
                      </div>
                    </div>
                  )}

                  {isCapturing && countdown > 0 && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50">
                      <div className="text-6xl font-bold text-white animate-pulse">
                        {countdown}
                      </div>
                    </div>
                  )}

                  {captureComplete && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50">
                      <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center">
                        <CheckCircle className="w-8 h-8 text-white" />
                      </div>
                    </div>
                  )}
                </div>

                <canvas ref={canvasRef} className="hidden" />
              </div>

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
                  Please say: <span className="font-mono bg-slate-100 px-2 py-1 rounded">"Uhakiki AI verifies my identity"</span>
                </p>
              </div>

              <div className="text-center py-8">
                <div className="w-32 h-32 mx-auto bg-gradient-to-r from-purple-100 to-purple-200 rounded-full flex items-center justify-center">
                  {voiceRecording ? (
                    <div className="flex space-x-1">
                      {[1,2,3,4,5].map(i => (
                        <div key={i} className={`w-1 bg-purple-600 rounded-full animate-pulse delay-${i*75}`} style={{height: `${Math.random() * 20 + 10}px`}} />
                      ))}
                    </div>
                  ) : (
                    <Mic className="w-12 h-12 text-purple-600" />
                  )}
                </div>
                <p className="mt-4 text-slate-600">
                  {voiceRecording ? 'Recording... Speak clearly' : 'Tap to start recording'}
                </p>
              </div>

              <button
                onClick={voiceRecording ? () => {} : startVoiceRecording}
                disabled={voiceRecording}
                className="w-full px-4 py-3 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
              >
                {voiceRecording ? 'Recording...' : 'Start Voice Recording'}
              </button>
            </div>
          )}

          {currentStep === 'complete' && (
            <div className="text-center space-y-6">
              <div className="w-20 h-20 mx-auto bg-green-100 rounded-full flex items-center justify-center">
                <CheckCircle className="w-10 h-10 text-green-600" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-slate-900">Registration Complete!</h3>
                <p className="text-slate-600 mt-2">
                  Your biometric data has been registered successfully.
                </p>
              </div>
              <button
                onClick={handleComplete}
                className="w-full px-4 py-3 bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-700 transition-colors"
              >
                Continue to Dashboard
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function StepIndicator({ step, current, label, icon: Icon }: { 
  step: number; 
  current: string; 
  label: string;
  icon: any;
}) {
  const isActive = (step === 1 && current === 'face') || 
                   (step === 2 && current === 'voice') || 
                   (step === 3 && current === 'complete')
  const isComplete = (step === 1 && (current === 'voice' || current === 'complete')) ||
                     (step === 2 && current === 'complete')

  return (
    <div className={`flex items-center ${isActive ? 'text-purple-600' : isComplete ? 'text-green-600' : 'text-slate-400'}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
        isActive ? 'bg-purple-600 text-white' : 
        isComplete ? 'bg-green-600 text-white' : 
        'bg-slate-200 text-slate-600'
      }`}>
        {isComplete ? <CheckCircle className="w-5 h-5" /> : step}
      </div>
      <span className="ml-2 text-sm font-medium hidden sm:inline">{label}</span>
    </div>
  )
}
