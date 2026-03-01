"use client"

import { useState, useRef } from 'react'
import { Upload, Camera, CheckCircle, AlertCircle, Loader2, Image as ImageIcon, Shield, Eye, EyeOff } from 'lucide-react'

interface RegistrationResult {
  status: string
  student_id: string
  face_extraction: {
    face_detected: boolean
    confidence: number
    encoding_length: number
  }
  message: string
}

interface FaceRegistrationProps {
  studentId: string
  onRegistrationComplete: (result: RegistrationResult) => void
  onError: (error: string) => void
}

export default function FaceRegistration({ 
  studentId, 
  onRegistrationComplete, 
  onError 
}: FaceRegistrationProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<RegistrationResult | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [showFullImage, setShowFullImage] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      if (!file.type.startsWith('image/')) {
        onError('Please select an image file (JPEG, PNG, etc.)')
        return
      }

      if (file.size > 10 * 1024 * 1024) {
        onError('File size must be less than 10MB')
        return
      }

      setSelectedFile(file)
      setUploadResult(null)
      
      const reader = new FileReader()
      reader.onload = (e) => {
        setPreviewUrl(e.target?.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  const resetForm = () => {
    setSelectedFile(null)
    setPreviewUrl(null)
    setUploadResult(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  const handleUpload = async () => {
    if (!selectedFile || !studentId) {
      onError('Please select a file and provide student ID')
      return
    }

    setIsUploading(true)
    setUploadResult(null)

    try {
      const formData = new FormData()
      formData.append('student_id', studentId)
      formData.append('id_card', selectedFile)

      const response = await fetch(`${API_BASE}/api/v1/extract-reference-face`, {
        method: 'POST',
        body: formData,
      })

      // Parse JSON once to avoid "body already used" errors
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed')
      }

      const result: RegistrationResult = data
      setUploadResult(result)
      
      if (result.status === 'SUCCESS') {
        onRegistrationComplete(result)
      } else {
        onError(result.message || 'Registration failed')
      }

    } catch (error) {
      console.error('Upload error:', error)
      onError(error instanceof Error ? error.message : 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  } // <--- Added missing brace here to fix the scope error

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">
          Reference Face Registration
        </h2>
        <p className="text-slate-600">
          Upload your ID card to extract and store your reference face for biometric verification
        </p>
      </div>

      {/* Upload Section */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="space-y-4">
          {/* File Input */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              ID Card Image
            </label>
            <div className="flex items-center space-x-4">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileSelect}
                className="hidden"
                id="id-card-upload"
              />
              <label
                htmlFor="id-card-upload"
                className="flex-1 px-4 py-3 border-2 border-dashed border-slate-300 rounded-lg cursor-pointer hover:border-emerald-500 transition-colors"
              >
                <div className="flex items-center justify-center space-x-2">
                  <Upload className="w-5 h-5 text-slate-400" />
                  <span className="text-slate-600">
                    {selectedFile ? selectedFile.name : 'Choose ID card image'}
                  </span>
                </div>
              </label>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Supported formats: JPEG, PNG. Maximum file size: 10MB
            </p>
          </div>

          {/* Preview with Privacy Protection */}
          {previewUrl && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-slate-700">
                  ID Card Preview
                </label>
                <button
                  type="button"
                  onClick={() => setShowFullImage(!showFullImage)}
                  className="flex items-center space-x-1 px-3 py-1 text-xs bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                >
                  {showFullImage ? (
                    <>
                      <EyeOff className="w-3 h-3" />
                      <span>Hide Details</span>
                    </>
                  ) : (
                    <>
                      <Eye className="w-3 h-3" />
                      <span>Show Full</span>
                    </>
                  )}
                </button>
              </div>
              
              <div className="relative aspect-[3/2] bg-slate-100 rounded-lg overflow-hidden">
                {/* Privacy overlay - only shown when not showing full image */}
                {!showFullImage && (
                  <div className="absolute inset-0 z-10 pointer-events-none">
                    <div className="w-full h-full backdrop-blur-md bg-white/40"></div>
                    {/* Privacy notice overlay */}
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="bg-slate-900/85 text-white px-4 py-3 rounded-xl text-sm font-medium backdrop-blur-sm">
                        <div className="flex items-center space-x-2">
                          <Shield className="w-4 h-4" />
                          <span>Privacy Protected</span>
                        </div>
                        <p className="text-xs mt-1 opacity-90">Face extraction processing only</p>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* The actual image (always sent to backend unmodified) */}
                <img
                  src={previewUrl}
                  alt="ID card preview"
                  className={`w-full h-full object-contain transition-all duration-300 ${
                    showFullImage ? 'opacity-100' : 'opacity-30'
                  }`}
                />
              </div>
              
              <div className="mt-2 p-3 bg-slate-50 rounded-lg border border-slate-200">
                <div className="flex items-start space-x-2">
                  <Shield className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                  <div className="text-xs text-slate-600">
                    <p className="font-medium text-slate-700 mb-1">
                      {showFullImage ? '⚠️ Full ID Visible' : '✓ Privacy Protected'}
                    </p>
                    {!showFullImage ? (
                      <p>ID card details are hidden for privacy. The full image is securely processed for face extraction only.</p>
                    ) : (
                      <p className="text-amber-700">Full ID card is visible. Ensure no unauthorized viewing.</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Student ID Display */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Student ID
            </label>
            <div className="px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg">
              <span className="font-mono text-slate-900">{studentId || 'Not provided'}</span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex space-x-4">
            <button
              onClick={handleUpload}
              disabled={!selectedFile || !studentId || isUploading}
              className="flex-1 px-4 py-3 bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <Camera className="w-5 h-5" />
                  <span>Extract & Register Face</span>
                </>
              )}
            </button>
            
            {selectedFile && (
              <button
                onClick={resetForm}
                disabled={isUploading}
                className="px-4 py-3 bg-slate-600 text-white font-medium rounded-lg hover:bg-slate-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Upload Result */}
      {uploadResult && (
        <div className={`rounded-xl border-2 p-6 ${
          uploadResult.status === 'SUCCESS' 
            ? 'bg-emerald-50 border-emerald-200' 
            : 'bg-red-50 border-red-200'
        }`}>
          <div className="flex items-start space-x-3">
            {uploadResult.status === 'SUCCESS' ? (
              <CheckCircle className="w-6 h-6 text-emerald-600 mt-1" />
            ) : (
              <AlertCircle className="w-6 h-6 text-red-600 mt-1" />
            )}
            
            <div className="flex-1">
              <h3 className={`text-lg font-semibold mb-2 ${
                uploadResult.status === 'SUCCESS' ? 'text-emerald-900' : 'text-red-900'
              }`}>
                {uploadResult.status === 'SUCCESS' ? 'Registration Successful' : 'Registration Failed'}
              </h3>
              
              <p className={`mb-4 ${
                uploadResult.status === 'SUCCESS' ? 'text-emerald-700' : 'text-red-700'
              }`}>
                {uploadResult.message}
              </p>
              
              {uploadResult.status === 'SUCCESS' && uploadResult.face_extraction && (
                <div className="space-y-2">
                  <h4 className="font-medium text-emerald-900">Face Extraction Details:</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-emerald-700">Face Detected:</span>
                      <span className="ml-2 font-medium text-emerald-900">
                        {uploadResult.face_extraction.face_detected ? 'Yes' : 'No'}
                      </span>
                    </div>
                    <div>
                      <span className="text-emerald-700">Confidence:</span>
                      <span className="ml-2 font-medium text-emerald-900">
                        {Math.round(uploadResult.face_extraction.confidence * 100)}%
                      </span>
                    </div>
                    <div>
                      <span className="text-emerald-700">Encoding Length:</span>
                      <span className="ml-2 font-medium text-emerald-900">
                        {uploadResult.face_extraction.encoding_length} dimensions
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <div className="flex items-start space-x-3">
          <ImageIcon className="w-6 h-6 text-blue-600 mt-1" />
          <div>
            <h3 className="text-lg font-semibold text-blue-900 mb-2">
              ID Card Guidelines
            </h3>
            <ul className="text-blue-700 space-y-1 text-sm">
              <li>• Ensure the ID card photo is clear and well-lit</li>
              <li>• The face should be facing forward and clearly visible</li>
              <li>• Avoid blurry images or glare on the photo</li>
              <li>• Make sure the entire ID card is visible in the image</li>
              <li>• High-resolution images provide better extraction results</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}