"use client"

import { useState, useRef, useCallback } from 'react'
import { Upload, FileText, AlertCircle, CheckCircle, Loader2, X } from 'lucide-react'

interface DocumentUploadProps {
  onDocumentUploaded: (documentData: {
    file: File
    type: string
    preview: string
  }) => void
  onDocumentAnalyzed: (analysisResult: any) => void
  onError: (error: string) => void
  isAnalyzing?: boolean
}

const DOCUMENT_TYPES = [
  { id: 'national_id', label: 'National ID Card', icon: '🆔' },
  { id: 'passport', label: 'Passport', icon: '📄' },
  { id: 'kcse_certificate', label: 'KCSE Certificate', icon: '🎓' },
  { id: 'admission_letter', label: 'Admission Letter', icon: '📋' },
  { id: 'helb_statement', label: 'HELB Statement', icon: '💰' }
]

export default function DocumentUpload({ 
  onDocumentUploaded, 
  onDocumentAnalyzed,
  onError,
  isAnalyzing = false 
}: DocumentUploadProps) {
  const [selectedDocument, setSelectedDocument] = useState<File | null>(null)
  const [documentType, setDocumentType] = useState<string>('national_id')
  const [preview, setPreview] = useState<string>('')
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = useCallback((file: File) => {
    // Validate file type
    if (!file.type.startsWith('image/')) {
      onError('Please upload an image file (JPEG, PNG, etc.)')
      return
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      onError('File size must be less than 10MB')
      return
    }

    setSelectedDocument(file)
    
    // Create preview
    const reader = new FileReader()
    reader.onload = (e) => {
      const previewUrl = e.target?.result as string
      setPreview(previewUrl)
      onDocumentUploaded({
        file,
        type: documentType,
        preview: previewUrl
      })
    }
    reader.readAsDataURL(file)
  }, [documentType, onDocumentUploaded, onError])

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0])
    }
  }, [handleFileSelect])

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0])
    }
  }, [handleFileSelect])

  const analyzeDocument = async () => {
    if (!selectedDocument) {
      onError('Please select a document first')
      return
    }

    try {
      const formData = new FormData()
      formData.append('document', selectedDocument)
      formData.append('document_type', documentType)

      const response = await fetch('http://localhost:8000/api/v1/verify/document', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`)
      }

      const analysisResult = await response.json()
      onDocumentAnalyzed(analysisResult)

    } catch (error) {
      console.error('Document analysis failed:', error)
      onError('Failed to analyze document. Please try again.')
    }
  }

  const clearDocument = () => {
    setSelectedDocument(null)
    setPreview('')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="space-y-6">
      {/* Document Type Selection */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Document Type</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {DOCUMENT_TYPES.map((type) => (
            <button
              key={type.id}
              onClick={() => setDocumentType(type.id)}
              className={`p-3 rounded-lg border-2 transition-all ${
                documentType === type.id
                  ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                  : 'border-slate-200 hover:border-slate-300 text-slate-600'
              }`}
            >
              <div className="text-2xl mb-1">{type.icon}</div>
              <div className="text-sm font-medium">{type.label}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Document Upload Area */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Upload Document</h3>
        
        {!selectedDocument ? (
          <div
            className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive
                ? 'border-emerald-500 bg-emerald-50'
                : 'border-slate-300 hover:border-slate-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileInputChange}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              disabled={isAnalyzing}
            />
            
            <Upload className="w-12 h-12 text-slate-400 mx-auto mb-4" />
            <p className="text-lg font-medium text-slate-900 mb-2">
              Drop your document here or click to browse
            </p>
            <p className="text-sm text-slate-500">
              Supports JPEG, PNG, WebP (max 10MB)
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Document Preview */}
            <div className="relative">
              <img
                src={preview}
                alt="Document preview"
                className="w-full h-auto rounded-lg border border-slate-200"
              />
              <button
                onClick={clearDocument}
                className="absolute top-2 right-2 p-2 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors"
                disabled={isAnalyzing}
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Document Info */}
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <FileText className="w-5 h-5 text-slate-600" />
                <div>
                  <p className="font-medium text-slate-900">{selectedDocument.name}</p>
                  <p className="text-sm text-slate-500">
                    {(selectedDocument.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              <div className="px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-sm font-medium">
                {DOCUMENT_TYPES.find(t => t.id === documentType)?.label}
              </div>
            </div>

            {/* Analyze Button */}
            <button
              onClick={analyzeDocument}
              disabled={isAnalyzing}
              className="w-full px-6 py-3 bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Analyzing Document...</span>
                </>
              ) : (
                <>
                  <CheckCircle className="w-5 h-5" />
                  <span>Analyze for Forgery</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Security Guidelines */}
      <div className="bg-blue-50 rounded-xl border border-blue-200 p-6">
        <div className="flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <h4 className="font-medium text-blue-900 mb-2">Security Guidelines</h4>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• Ensure document is well-lit and all text is clearly visible</li>
              <li>• Remove any obstructions or glare from the document</li>
              <li>• Use original documents - photocopies may have lower accuracy</li>
              <li>• System will detect digital manipulation, deepfakes, and forgeries</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
