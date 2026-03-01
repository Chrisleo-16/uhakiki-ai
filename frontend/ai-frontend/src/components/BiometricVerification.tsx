"use client"

import { useState, useEffect, useRef, useCallback } from 'react'
import { Camera, CameraOff, AlertCircle, CheckCircle, XCircle, Loader2 } from 'lucide-react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface VerificationStatus {
  status: string
  message: string
  confidence?: number
  current_challenge?: string
  frame_count?: number
  session_duration?: number
}

interface BiometricVerificationProps {
  studentId: string
  onVerificationComplete: (result: any) => void
  onError: (error: string) => void
}

export default function BiometricVerification({ 
  studentId, 
  onVerificationComplete, 
  onError 
}: BiometricVerificationProps) {
  const [isConnected, setIsConnected] = useState(false)
  const [isVerifying, setIsVerifying] = useState(false)
  const [verificationStatus, setVerificationStatus] = useState<VerificationStatus | null>(null)
  const [webcamEnabled, setWebcamEnabled] = useState(false)
  const [finalVerdict, setFinalVerdict] = useState<'APPROVED' | 'FLAGGED' | null>(null)
  
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const websocketRef = useRef<WebSocket | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // Initialize webcam
  const initializeWebcam = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        } 
      })
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        streamRef.current = stream
        setWebcamEnabled(true)
      }
    } catch (error) {
      console.error('Webcam initialization failed:', error)
      onError('Failed to access webcam. Please ensure camera permissions are granted.')
    }
  }

  // Stop webcam
  const stopWebcam = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
    setWebcamEnabled(false)
  }

  // Capture frame from webcam
  const captureFrame = (): string | null => {
    if (!videoRef.current || !canvasRef.current) return null
    
    const video = videoRef.current
    const canvas = canvasRef.current
    const context = canvas.getContext('2d')
    
    if (!context) return null
    
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    context.drawImage(video, 0, 0, canvas.width, canvas.height)
    
    return canvas.toDataURL('image/jpeg', 0.8)
  }

  // Start verification process
  const startVerification = async () => {
    if (!studentId) {
      onError('Student ID is required for verification')
      return
    }

    setIsVerifying(true)
    setFinalVerdict(null)
    setVerificationStatus(null)

    try {
      // Initialize webcam if not already enabled
      if (!webcamEnabled) {
        await initializeWebcam()
        // Wait a moment for webcam to initialize
        await new Promise(resolve => setTimeout(resolve, 1000))
      }

      // Connect to WebSocket
      const wsUrl = `ws://${API_BASE.replace('http://', '').replace('https://', '')}/ws/mbic/${studentId}`
      const websocket = new WebSocket(wsUrl)
      websocketRef.current = websocket

      websocket.onopen = () => {
        setIsConnected(true)
        console.log('Connected to MBIC verification service')
        
        // Start sending frames every 200ms
        intervalRef.current = setInterval(() => {
          const frame = captureFrame()
          if (frame && websocket.readyState === WebSocket.OPEN) {
            websocket.send(frame)
          }
        }, 200)
      }

      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          setVerificationStatus(data)

          // Handle different status messages
          switch (data.status) {
            case 'AUTHENTICATED':
              console.log('Biometric authentication successful')
              break
            
            case 'FINAL_VERDICT':
              setFinalVerdict(data.verdict)
              setIsVerifying(false)
              stopVerification()
              onVerificationComplete(data)
              break
            
            case 'ERROR':
              onError(data.message || 'Verification error occurred')
              setIsVerifying(false)
              stopVerification()
              break
            
            case 'SUSPICIOUS_ACTIVITY':
              console.warn('Suspicious activity detected:', data.security_flag)
              break
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error)
        onError('Connection to verification service failed')
        setIsVerifying(false)
        stopVerification()
      }

      websocket.onclose = () => {
        setIsConnected(false)
        console.log('Disconnected from MBIC verification service')
      }

    } catch (error) {
      console.error('Verification setup failed:', error)
      onError('Failed to start verification process')
      setIsVerifying(false)
    }
  }

  // Stop verification process
  const stopVerification = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    
    if (websocketRef.current) {
      websocketRef.current.close()
      websocketRef.current = null
    }
    
    setIsConnected(false)
    setIsVerifying(false)
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopVerification()
      stopWebcam()
    }
  }, [])

  // Get status icon and color
  const getStatusIcon = () => {
    if (finalVerdict === 'APPROVED') {
      return <CheckCircle className="w-8 h-8 text-emerald-500" />
    } else if (finalVerdict === 'FLAGGED') {
      return <XCircle className="w-8 h-8 text-red-500" />
    } else if (verificationStatus?.status === 'SUSPICIOUS_ACTIVITY') {
      return <AlertCircle className="w-6 h-6 text-yellow-500 animate-pulse" />
    } else if (isVerifying) {
      return <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
    }
    return null
  }

  const getStatusColor = () => {
    if (finalVerdict === 'APPROVED') return 'text-emerald-600 bg-emerald-50 border-emerald-200'
    if (finalVerdict === 'FLAGGED') return 'text-red-600 bg-red-50 border-red-200'
    if (verificationStatus?.status === 'SUSPICIOUS_ACTIVITY') return 'text-yellow-600 bg-yellow-50 border-yellow-200'
    if (isVerifying) return 'text-blue-600 bg-blue-50 border-blue-200'
    return 'text-gray-600 bg-gray-50 border-gray-200'
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">
          Multimodal Biometric Identity Verification
        </h2>
        <p className="text-slate-600">
          Real-time face recognition and liveness detection for secure identity verification
        </p>
      </div>

      {/* Video Section */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="relative">
          {/* Webcam Feed */}
          <div className="relative aspect-video bg-slate-900 rounded-lg overflow-hidden">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
              style={{ display: webcamEnabled ? 'block' : 'none' }}
            />
            
            {/* Placeholder when webcam is off */}
            {!webcamEnabled && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <CameraOff className="w-16 h-16 text-slate-400 mx-auto mb-4" />
                  <p className="text-slate-400">Webcam is disabled</p>
                </div>
              </div>
            )}

            {/* Status Overlay */}
            {isVerifying && (
              <div className="absolute top-4 left-4 right-4">
                <div className={`px-4 py-2 rounded-lg border ${getStatusColor()}`}>
                  <div className="flex items-center space-x-2">
                    {getStatusIcon()}
                    <span className="font-medium">
                      {verificationStatus?.message || 'Initializing...'}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Challenge Display */}
            {verificationStatus?.current_challenge && isVerifying && !finalVerdict && (
              <div className="absolute bottom-4 left-4 right-4">
                <div className="bg-blue-600 text-white px-4 py-3 rounded-lg text-center">
                  <p className="font-semibold">Please: {verificationStatus.current_challenge.replace('_', ' ')}</p>
                </div>
              </div>
            )}
          </div>

          {/* Hidden canvas for frame capture */}
          <canvas ref={canvasRef} className="hidden" />
        </div>

        {/* Controls */}
        <div className="flex justify-center space-x-4 mt-6">
          {!isVerifying ? (
            <button
              onClick={startVerification}
              disabled={!studentId}
              className="px-6 py-3 bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
            >
              <Camera className="w-5 h-5" />
              <span>Start Verification</span>
            </button>
          ) : (
            <button
              onClick={stopVerification}
              className="px-6 py-3 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2"
            >
              <CameraOff className="w-5 h-5" />
              <span>Stop Verification</span>
            </button>
          )}
        </div>
      </div>

      {/* Status Details */}
      {verificationStatus && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Verification Status</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium text-slate-600">Current Status</p>
              <p className="text-lg font-semibold text-slate-900">
                {verificationStatus.status?.replace('_', ' ') || 'Unknown'}
              </p>
            </div>
            
            {verificationStatus.confidence && (
              <div>
                <p className="text-sm font-medium text-slate-600">Confidence Score</p>
                <div className="flex items-center space-x-2">
                  <div className="flex-1 bg-slate-200 rounded-full h-2">
                    <div 
                      className="bg-emerald-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${(verificationStatus.confidence || 0) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium text-slate-900">
                    {Math.round((verificationStatus.confidence || 0) * 100)}%
                  </span>
                </div>
              </div>
            )}
            
            {verificationStatus.frame_count && (
              <div>
                <p className="text-sm font-medium text-slate-600">Frames Processed</p>
                <p className="text-lg font-semibold text-slate-900">{verificationStatus.frame_count}</p>
              </div>
            )}
            
            {verificationStatus.session_duration && (
              <div>
                <p className="text-sm font-medium text-slate-600">Session Duration</p>
                <p className="text-lg font-semibold text-slate-900">
                  {Math.round(verificationStatus.session_duration)}s
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Final Verdict */}
      {finalVerdict && (
        <div className={`rounded-xl border-2 p-8 text-center ${
          finalVerdict === 'APPROVED' 
            ? 'bg-emerald-50 border-emerald-200' 
            : 'bg-red-50 border-red-200'
        }`}>
          {finalVerdict === 'APPROVED' ? (
            <CheckCircle className="w-16 h-16 text-emerald-600 mx-auto mb-4" />
          ) : (
            <XCircle className="w-16 h-16 text-red-600 mx-auto mb-4" />
          )}
          
          <h3 className={`text-2xl font-bold mb-2 ${
            finalVerdict === 'APPROVED' ? 'text-emerald-900' : 'text-red-900'
          }`}>
            {finalVerdict === 'APPROVED' ? 'Identity Verified' : 'Verification Failed'}
          </h3>
          
          <p className={`text-lg ${
            finalVerdict === 'APPROVED' ? 'text-emerald-700' : 'text-red-700'
          }`}>
            {finalVerdict === 'APPROVED' 
              ? 'Your identity has been successfully verified through multimodal biometric analysis.'
              : 'Identity verification could not be completed. Please try again or contact support.'
            }
          </p>
        </div>
      )}
    </div>
  )
}
