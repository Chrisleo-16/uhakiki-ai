"use client"

import { VerificationStepper } from '@/components/verification'
import { Shield } from 'lucide-react'

export default function VerifyIDPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm dark:bg-slate-900/80 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/20">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-slate-900 dark:text-white">UhakikiAI</h1>
                <p className="text-xs text-slate-500 dark:text-slate-400">Document Verification</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-slate-600 dark:text-slate-300">Secure Verification Portal</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="py-10 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          {/* Page Title */}
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-slate-900 dark:text-white sm:text-4xl">
              Identity Document Verification
            </h2>
            <p className="mt-3 text-lg text-slate-600 dark:text-slate-300">
              Upload your identity document for AI-powered authenticity verification
            </p>
          </div>

          {/* Verification Stepper */}
          <VerificationStepper />
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-20 border-t bg-white/50 dark:bg-slate-900/50">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between text-sm text-slate-500 dark:text-slate-400">
            <p>© 2024 UhakikiAI. All rights reserved.</p>
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                System Online
              </span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
