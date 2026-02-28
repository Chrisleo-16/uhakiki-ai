"use client"

import { motion } from 'framer-motion'
import { ScanLine } from 'lucide-react'

interface ScannerProps {
  active?: boolean
}

export function Scanner({ active = true }: ScannerProps) {
  if (!active) return null

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden">
      {/* Scanning Line */}
      <motion.div
        className="absolute left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-emerald-400 to-transparent"
        initial={{ top: '0%' }}
        animate={{ top: ['0%', '100%', '0%'] }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: 'easeInOut'
        }}
      />
      
      {/* Glow Effect */}
      <motion.div
        className="absolute left-0 right-0 h-20 bg-gradient-to-b from-emerald-400/20 to-transparent"
        initial={{ top: '0%' }}
        animate={{ top: ['0%', '100%', '0%'] }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: 'easeInOut'
        }}
      />
      
      {/* Corner Markers */}
      <div className="absolute top-4 left-4 w-8 h-8 border-l-2 border-t-2 border-emerald-400" />
      <div className="absolute top-4 right-4 w-8 h-8 border-r-2 border-t-2 border-emerald-400" />
      <div className="absolute bottom-4 left-4 w-8 h-8 border-l-2 border-b-2 border-emerald-400" />
      <div className="absolute bottom-4 right-4 w-8 h-8 border-r-2 border-b-2 border-emerald-400" />
      
      {/* Scan Text */}
      <motion.div
        className="absolute top-4 left-1/2 -translate-x-1/2 text-xs font-mono text-emerald-400 bg-slate-900/80 px-2 py-1 rounded"
        initial={{ opacity: 0 }}
        animate={{ opacity: [0.5, 1, 0.5] }}
        transition={{
          duration: 1,
          repeat: Infinity,
          ease: 'easeInOut'
        }}
      >
        SCANNING...
      </motion.div>
    </div>
  )
}

export function ScanningIndicator() {
  return (
    <div className="flex items-center gap-2 text-emerald-600">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
      >
        <ScanLine className="w-5 h-5" />
      </motion.div>
      <span className="text-sm font-medium">AI Analysis in Progress</span>
    </div>
  )
}
