"use client"

import { motion } from 'framer-motion'
import { AlertTriangle, CheckCircle, AlertCircle } from 'lucide-react'

interface RiskGaugeProps {
  score: number
  size?: 'sm' | 'md' | 'lg'
}

export function RiskGauge({ score, size = 'md' }: RiskGaugeProps) {
  const getRiskLevel = (score: number) => {
    if (score < 20) return { level: 'Low Risk', color: '#10b981', icon: CheckCircle }
    if (score < 50) return { level: 'Medium Risk', color: '#f59e0b', icon: AlertCircle }
    return { level: 'High Risk', color: '#ef4444', icon: AlertTriangle }
  }

  const { level, color, icon: Icon } = getRiskLevel(score)
  
  const dimensions = {
    sm: { size: 80, strokeWidth: 6, fontSize: 'text-sm' },
    md: { size: 120, strokeWidth: 8, fontSize: 'text-lg' },
    lg: { size: 160, strokeWidth: 10, fontSize: 'text-xl' },
  }

  const { size: dimension, strokeWidth, fontSize } = dimensions[size]
  const radius = (dimension - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const progress = ((100 - score) / 100) * circumference

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: dimension, height: dimension }}>
        {/* Background Circle */}
        <svg width={dimension} height={dimension} className="transform -rotate-90">
          <circle
            cx={dimension / 2}
            cy={dimension / 2}
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth={strokeWidth}
            className="text-slate-200"
          />
          {/* Progress Circle */}
          <motion.circle
            cx={dimension / 2}
            cy={dimension / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: progress }}
            transition={{ duration: 1, ease: 'easeOut' }}
          />
        </svg>

        {/* Center Content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.5, type: 'spring' }}
          >
            <Icon className="w-6 h-6" style={{ color }} />
          </motion.div>
          <motion.span
            className={`${fontSize} font-bold`}
            style={{ color }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7 }}
          >
            {score}
          </motion.span>
        </div>
      </div>

      {/* Risk Label */}
      <motion.div
        className="mt-2 flex items-center gap-1"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
      >
        <span className="text-sm font-medium" style={{ color }}>
          {level}
        </span>
      </motion.div>
    </div>
  )
}

// Simple circular progress for smaller spaces
export function CircularProgress({ 
  value, 
  size = 40, 
  color = '#10b981',
  showValue = true 
}: { 
  value: number
  size?: number
  color?: string
  showValue?: boolean
}) {
  const strokeWidth = size / 8
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const progress = ((100 - value) / 100) * circumference

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-slate-200"
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: progress }}
          transition={{ duration: 0.8 }}
        />
      </svg>
      {showValue && (
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xs font-bold" style={{ color }}>
            {value}%
          </span>
        </div>
      )}
    </div>
  )
}
