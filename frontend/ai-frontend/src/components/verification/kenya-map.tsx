"use client"

import { useState } from 'react'
import { motion } from 'framer-motion'

interface CountyData {
  name: string
  risk: 'low' | 'medium' | 'high'
  verifications: number
  fraudRate: number
  coordinates: { x: number; y: number }
}

// Kenyan counties with approximate positions (simplified SVG coordinates)
const kenyanCounties: CountyData[] = [
  { name: 'Mombasa', risk: 'high', verifications: 2450, fraudRate: 12.3, coordinates: { x: 120, y: 320 } },
  { name: 'Nairobi', risk: 'high', verifications: 8900, fraudRate: 8.7, coordinates: { x: 180, y: 220 } },
  { name: 'Kisumu', risk: 'medium', verifications: 1200, fraudRate: 5.2, coordinates: { x: 220, y: 280 } },
  { name: 'Nakuru', risk: 'medium', verifications: 1800, fraudRate: 4.8, coordinates: { x: 160, y: 200 } },
  { name: 'Eldoret', risk: 'low', verifications: 950, fraudRate: 2.1, coordinates: { x: 140, y: 140 } },
  { name: 'Malindi', risk: 'medium', verifications: 680, fraudRate: 4.2, coordinates: { x: 80, y: 340 } },
  { name: 'Kakamega', risk: 'low', verifications: 720, fraudRate: 1.8, coordinates: { x: 200, y: 250 } },
  { name: 'Meru', risk: 'low', verifications: 540, fraudRate: 1.5, coordinates: { x: 260, y: 120 } },
  { name: 'Kitale', risk: 'low', verifications: 380, fraudRate: 1.2, coordinates: { x: 80, y: 100 } },
  { name: 'Garissa', risk: 'medium', verifications: 290, fraudRate: 3.8, coordinates: { x: 200, y: 380 } },
]

interface KenyaMapProps {
  selectedCounty?: string
  onCountySelect?: (county: string) => void
}

export function KenyaMap({ selectedCounty, onCountySelect }: KenyaMapProps) {
  const [hoveredCounty, setHoveredCounty] = useState<string | null>(null)

  const getRiskColor = (risk: 'low' | 'medium' | 'high') => {
    switch (risk) {
      case 'low': return '#10b981'
      case 'medium': return '#f59e0b'
      case 'high': return '#ef4444'
    }
  }

  return (
    <div className="relative w-full aspect-[4/3] bg-slate-50 rounded-lg overflow-hidden">
      {/* Simplified Kenya Outline */}
      <svg viewBox="0 0 400 400" className="w-full h-full">
        {/* Background */}
        <rect width="400" height="400" fill="#f8fafc" />
        
        {/* Kenya simplified shape */}
        <path
          d="M150 20 L250 20 L280 80 L300 150 L280 200 L260 250 L220 320 L180 350 L120 340 L80 280 L60 200 L80 120 L120 50 Z"
          fill="#e2e8f0"
          stroke="#94a3b8"
          strokeWidth="2"
        />

        {/* County markers */}
        {kenyanCounties.map((county) => (
          <g key={county.name}>
            {/* Pulse animation for high risk */}
            {county.risk === 'high' && (
              <motion.circle
                cx={county.coordinates.x}
                cy={county.coordinates.y}
                r="20"
                fill={getRiskColor(county.risk)}
                opacity="0.3"
                animate={{ r: [15, 25, 15], opacity: [0.3, 0.1, 0.3] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
            )}
            
            {/* County dot */}
            <motion.circle
              cx={county.coordinates.x}
              cy={county.coordinates.y}
              r={selectedCounty === county.name || hoveredCounty === county.name ? 12 : 8}
              fill={getRiskColor(county.risk)}
              className="cursor-pointer"
              whileHover={{ scale: 1.3 }}
              onClick={() => onCountySelect?.(county.name)}
              onMouseEnter={() => setHoveredCounty(county.name)}
              onMouseLeave={() => setHoveredCounty(null)}
            />
          </g>
        ))}

        {/* Labels for major counties */}
        {kenyanCounties.filter(c => c.verifications > 1000).map((county) => (
          <text
            key={`label-${county.name}`}
            x={county.coordinates.x}
            y={county.coordinates.y - 15}
            textAnchor="middle"
            className="text-[8px] fill-slate-600 font-medium"
          >
            {county.name}
          </text>
        ))}
      </svg>

      {/* Legend */}
      <div className="absolute bottom-2 left-2 bg-white/90 backdrop-blur rounded-lg p-2 text-xs">
        <div className="font-semibold mb-1">Risk Level</div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-emerald-500" />
          <span>Low</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-amber-500" />
          <span>Medium</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <span>High</span>
        </div>
      </div>

      {/* County Info Tooltip */}
      {(hoveredCounty || selectedCounty) && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute top-2 right-2 bg-white/95 backdrop-blur rounded-lg p-3 shadow-lg text-xs min-w-[150px]"
        >
          {(() => {
            const county = kenyanCounties.find(
              c => c.name === hoveredCounty || c.name === selectedCounty
            )
            if (!county) return null
            return (
              <>
                <div className="font-semibold text-slate-900">{county.name}</div>
                <div className="mt-2 space-y-1">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Verifications</span>
                    <span className="font-medium">{county.verifications.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Fraud Rate</span>
                    <span className={`font-medium ${
                      county.fraudRate > 5 ? 'text-red-600' : 
                      county.fraudRate > 3 ? 'text-amber-600' : 'text-emerald-600'
                    }`}>
                      {county.fraudRate}%
                    </span>
                  </div>
                </div>
              </>
            )
          })()}
        </motion.div>
      )}
    </div>
  )
}

// County risk data for verification details
export function getCountyRiskData(countyName: string): CountyData | undefined {
  return kenyanCounties.find(c => c.name.toLowerCase() === countyName.toLowerCase())
}
