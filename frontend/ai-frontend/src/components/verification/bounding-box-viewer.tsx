"use client"

import { useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface BoundingBox {
  label: string
  x: number
  y: number
  width: number
  height: number
}

interface HeatmapRegion {
  x: number
  y: number
  radius: number
}

interface BoundingBoxViewerProps {
  boxes: BoundingBox[]
  heatmapRegions?: HeatmapRegion[]
  showHeatmap?: boolean
}

const boxColors: Record<string, string> = {
  'Photo': '#10b981',    // Emerald
  'Name': '#3b82f6',     // Blue
  'ID Number': '#8b5cf6', // Purple
  'Signature': '#f59e0b', // Amber
  'default': '#10b981',
}

export function BoundingBoxViewer({ boxes, heatmapRegions = [], showHeatmap = true }: BoundingBoxViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  // Draw heatmap on canvas
  useEffect(() => {
    if (!showHeatmap || heatmapRegions.length === 0) return

    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Draw heatmap regions
    heatmapRegions.forEach((region, index) => {
      const gradient = ctx.createRadialGradient(
        region.x, region.y, 0,
        region.x, region.y, region.radius
      )
      gradient.addColorStop(0, 'rgba(239, 68, 68, 0.8)') // Red center
      gradient.addColorStop(0.5, 'rgba(239, 68, 68, 0.4)')
      gradient.addColorStop(1, 'rgba(239, 68, 0, 0)')   // Transparent edge

      ctx.fillStyle = gradient
      ctx.beginPath()
      ctx.arc(region.x, region.y, region.radius, 0, Math.PI * 2)
      ctx.fill()
    })
  }, [heatmapRegions, showHeatmap])

  return (
    <div className="absolute inset-0 pointer-events-none">
      {/* Heatmap Canvas */}
      {showHeatmap && heatmapRegions.length > 0 && (
        <canvas
          ref={canvasRef}
          width={400}
          height={300}
          className="absolute inset-0 w-full h-full"
        />
      )}

      {/* Bounding Boxes */}
      <AnimatePresence>
        {boxes.map((box, index) => (
          <motion.div
            key={box.label}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.1 + 0.3 }}
            className="absolute"
            style={{
              left: `${box.x}%`,
              top: `${box.y}%`,
              width: `${box.width}%`,
              height: `${box.height}%`,
            }}
          >
            {/* Box Border */}
            <div
              className="absolute inset-0 border-2 rounded"
              style={{ borderColor: boxColors[box.label] || boxColors.default }}
            />
            
            {/* Corner Accents */}
            <div
              className="absolute -top-0.5 -left-0.5 w-3 h-3"
              style={{ backgroundColor: boxColors[box.label] || boxColors.default }}
            />
            <div
              className="absolute -top-0.5 -right-0.5 w-3 h-3"
              style={{ backgroundColor: boxColors[box.label] || boxColors.default }}
            />
            <div
              className="absolute -bottom-0.5 -left-0.5 w-3 h-3"
              style={{ backgroundColor: boxColors[box.label] || boxColors.default }}
            />
            <div
              className="absolute -bottom-0.5 -right-0.5 w-3 h-3"
              style={{ backgroundColor: boxColors[box.label] || boxColors.default }}
            />

            {/* Label */}
            <div
              className="absolute -top-7 left-0 px-2 py-0.5 text-xs font-medium text-white rounded-t"
              style={{ backgroundColor: boxColors[box.label] || boxColors.default }}
            >
              {box.label}
            </div>
          </motion.div>
        ))}
      </AnimatePresence>

      {/* Legend */}
      {boxes.length > 0 && (
        <div className="absolute bottom-2 right-2 bg-slate-900/90 rounded-lg p-2 text-xs">
          <div className="text-slate-400 mb-1">Detected Regions</div>
          {boxes.map(box => (
            <div key={box.label} className="flex items-center gap-1.5">
              <div
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: boxColors[box.label] || boxColors.default }}
              />
              <span className="text-slate-300">{box.label}</span>
            </div>
          ))}
          {heatmapRegions.length > 0 && (
            <div className="flex items-center gap-1.5 mt-1 pt-1 border-t border-slate-700">
              <div className="w-2 h-2 rounded-full bg-red-500" />
              <span className="text-slate-300">Tampering</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// Simple bounding box without canvas for lighter weight
export function SimpleBoundingBoxViewer({ boxes }: { boxes: BoundingBox[] }) {
  return (
    <div className="absolute inset-0 pointer-events-none">
      {boxes.map((box, index) => (
        <motion.div
          key={box.label}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: index * 0.1 }}
          className="absolute border-2 border-emerald-400 rounded"
          style={{
            left: `${box.x}%`,
            top: `${box.y}%`,
            width: `${box.width}%`,
            height: `${box.height}%`,
          }}
        >
          <div className="absolute -top-6 left-0 bg-emerald-500 text-white text-xs px-1.5 py-0.5 rounded-t">
            {box.label}
          </div>
        </motion.div>
      ))}
    </div>
  )
}
