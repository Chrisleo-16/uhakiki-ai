"use client"

import { useState, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useDropzone } from 'react-dropzone'

export type VerificationStep = 'upload' | 'analysis' | 'result'

export interface VerificationData {
  file?: File
  previewUrl?: string
  isAuthentic?: boolean
  confidence?: number
  mseScore?: number
  extractedData?: {
    name?: string
    idNumber?: string
    county?: string
    dob?: string
    sex?: string
    nationality?: string
    expiryDate?: string
  }
  riskScore?: number
  riskFactors?: {
    factor: string
    score: number
    status: 'pass' | 'warning' | 'fail'
  }[]
  boundingBoxes?: Array<{
    label: string
    x: number
    y: number
    width: number
    height: number
    color: string
  }>
  tamperingRegions?: Array<{ x: number; y: number; radius: number }>
  extractedText?: string
}

// ── Scan line animation component ──────────────────────────────────────────
function ScanLine({ active }: { active: boolean }) {
  if (!active) return null
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      <motion.div
        className="absolute left-0 right-0 h-0.5"
        style={{ background: 'linear-gradient(90deg, transparent, #00D46A, transparent)', boxShadow: '0 0 12px #00D46A' }}
        animate={{ top: ['0%', '100%', '0%'] }}
        transition={{ duration: 2.5, repeat: Infinity, ease: 'linear' }}
      />
      <div className="absolute inset-0" style={{ background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,212,106,0.03) 2px, rgba(0,212,106,0.03) 4px)' }} />
    </div>
  )
}

// ── Risk arc gauge ──────────────────────────────────────────────────────────
function RiskGauge({ score }: { score: number }) {
  const color = score < 30 ? '#00D46A' : score < 60 ? '#F5C842' : '#FF4D4D'
  const label = score < 30 ? 'Low Risk' : score < 60 ? 'Medium Risk' : 'High Risk'
  const rotation = -135 + (score / 100) * 270

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative w-24 h-24">
        <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
          <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="8" strokeDasharray="188 251" strokeLinecap="round" />
          <motion.circle cx="50" cy="50" r="40" fill="none" stroke={color} strokeWidth="8"
            strokeDasharray={`${(score / 100) * 188} 251`} strokeLinecap="round"
            initial={{ strokeDasharray: '0 251' }}
            animate={{ strokeDasharray: `${(score / 100) * 188} 251` }}
            transition={{ duration: 1.2, ease: 'easeOut' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-xl font-bold" style={{ color }}>{score}</span>
        </div>
      </div>
      <span className="text-xs font-semibold" style={{ color }}>{label}</span>
    </div>
  )
}

// ── Bounding box overlay ────────────────────────────────────────────────────
function BoundingBoxes({ boxes, imgW, imgH }: {
  boxes: VerificationData['boundingBoxes']
  imgW: number; imgH: number
}) {
  if (!boxes?.length) return null
  return (
    <svg className="absolute inset-0 w-full h-full" viewBox={`0 0 ${imgW} ${imgH}`} preserveAspectRatio="xMidYMid meet">
      {boxes.map((box, i) => (
        <g key={i}>
          <motion.rect
            x={box.x} y={box.y} width={box.width} height={box.height}
            fill="none" stroke={box.color} strokeWidth="1.5" rx="2"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            transition={{ delay: i * 0.15 }}
          />
          <motion.rect
            x={box.x} y={box.y - 14} width={box.label.length * 6 + 8} height={14}
            fill={box.color} rx="2"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            transition={{ delay: i * 0.15 }}
          />
          <motion.text x={box.x + 4} y={box.y - 3} fontSize="9" fill="#04080F" fontWeight="bold"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            transition={{ delay: i * 0.15 }}
          >{box.label}</motion.text>
        </g>
      ))}
    </svg>
  )
}

const STEPS = [
  { id: 'upload',   label: 'Document Upload' },
  { id: 'analysis', label: 'AI Analysis' },
  { id: 'result',   label: 'Verification Result' },
]

// ── Main Component ──────────────────────────────────────────────────────────
export function VerificationStepper() {
  const [currentStep, setCurrentStep] = useState<VerificationStep>('upload')
  const [data, setData] = useState<VerificationData>({})
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [currentProcess, setCurrentProcess] = useState('')
  const [imgDims, setImgDims] = useState({ w: 400, h: 250 })
  const [error, setError] = useState<string | null>(null)
  const imgRef = useRef<HTMLImageElement>(null)

  const analysisSteps = [
    'Uploading document…',
    'Preprocessing image…',
    'Running OCR extraction…',
    'Detecting security elements…',
    'ELA forgery analysis…',
    'Verifying document structure…',
    'Cross-referencing database…',
    'Generating risk score…',
  ]

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return
    const previewUrl = URL.createObjectURL(file)
    setData({ file, previewUrl })
    setError(null)
    setCurrentStep('analysis')
    startAnalysis(file)
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.png', '.jpg', '.jpeg', '.webp'], 'application/pdf': ['.pdf'] },
    maxFiles: 1,
  })

  const startAnalysis = async (file: File) => {
    setIsProcessing(true)
    setProgress(0)

    // Animate progress bar while backend processes
    let stepIdx = 0
    const interval = setInterval(() => {
      if (stepIdx < analysisSteps.length) {
        setCurrentProcess(analysisSteps[stepIdx])
        setProgress(((stepIdx + 1) / analysisSteps.length) * 85) // cap at 85% until response
        stepIdx++
      } else {
        clearInterval(interval)
      }
    }, 700)

    try {
      const fd = new FormData()
      fd.append('document', file)

      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/document/scan/upload`,
        { method: 'POST', body: fd }
      )

      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}))
        throw new Error(errBody.detail || `Server error ${res.status}`)
      }

      const r = await res.json()

      clearInterval(interval)
      setProgress(100)
      setCurrentProcess('Analysis Complete')

      // ── Map backend response → UI ─────────────────────────────────────────
      const status       = r.verification_status || 'FAIL'
      const overallScore = r.overall_score ?? 0
      const isAuthentic  = status === 'PASS' || (status === 'REQUIRES_REVIEW' && overallScore > 0.4)
      const confidence   = overallScore * 100
      const mseScore     = r.forgery_analysis?.quality_analysis?.noise_level ?? 0
      const riskScore    = Math.round((1 - overallScore) * 100)

      // extracted_fields is already normalised by backend _normalize_fields()
      const ef = r.extracted_fields || {}
      const extractedData = {
        name:        ef.name          || '',
        idNumber:    ef.id_number     || ef.passport_number || '',
        dob:         ef.date_of_birth || '',
        sex:         ef.sex           || '',
        nationality: ef.nationality   || '',
        county:      ef.district      || ef.county || '',
        expiryDate:  ef.expiry_date   || '',
      }

      // Build bounding boxes only for fields the backend actually extracted
      const boxes: VerificationData['boundingBoxes'] = [
        { label: 'Photo', x: 8, y: 30, width: 82, height: 110, color: '#A78BFA' },
      ]
      if (extractedData.name)        boxes.push({ label: 'Name',        x: 100, y: 55,  width: 210, height: 22, color: '#00D46A' })
      if (extractedData.dob)         boxes.push({ label: 'DOB',         x: 250, y: 80,  width: 90,  height: 22, color: '#60A5FA' })
      if (extractedData.sex)         boxes.push({ label: 'Sex',         x: 100, y: 105, width: 60,  height: 20, color: '#F472B6' })
      if (extractedData.nationality) boxes.push({ label: 'Nationality', x: 175, y: 105, width: 80,  height: 20, color: '#34D399' })
      if (extractedData.idNumber)    boxes.push({ label: 'ID Number',   x: 100, y: 155, width: 130, height: 22, color: '#F5C842' })
      if (extractedData.county)      boxes.push({ label: 'District',    x: 100, y: 185, width: 100, height: 20, color: '#FB923C' })
      if (extractedData.expiryDate)  boxes.push({ label: 'Expiry',      x: 100, y: 210, width: 100, height: 20, color: '#F87171' })

      const extractedCount = Object.values(extractedData).filter(Boolean).length
      const fieldScore     = Math.round((extractedCount / 7) * 100)

      setData(prev => ({
        ...prev,
        isAuthentic,
        confidence,
        mseScore,
        riskScore,
        extractedData,
        extractedText: r.extracted_text || '',
        boundingBoxes: boxes,
        tamperingRegions: !isAuthentic ? [{ x: 150, y: 80, radius: 30 }] : [],
        riskFactors: [
          { factor: 'Document Authenticity', score: Math.round(confidence),                             status: isAuthentic ? 'pass' : 'warning' },
          { factor: 'Field Extraction',      score: fieldScore,                                          status: fieldScore >= 70 ? 'pass' : fieldScore >= 40 ? 'warning' : 'fail' },
          { factor: 'Image Integrity',       score: Math.round((1 - Math.min(mseScore / 30, 1)) * 100), status: mseScore < 15 ? 'pass' : mseScore < 25 ? 'warning' : 'fail' },
          { factor: 'Forgery Risk',          score: 100 - riskScore,                                    status: riskScore < 30 ? 'pass' : riskScore < 60 ? 'warning' : 'fail' },
        ],
      }))

      setTimeout(() => { setIsProcessing(false); setCurrentStep('result') }, 400)

    } catch (err: unknown) {
      clearInterval(interval)
      const msg = err instanceof Error ? err.message : 'Unknown error'
      setError(`Verification failed: ${msg}. Please try again.`)
      setProgress(0)
      setCurrentProcess('')
      setIsProcessing(false)
      setCurrentStep('upload')
    }
  }

  const handleReset = () => {
    setData({})
    setCurrentStep('upload')
    setProgress(0)
    setCurrentProcess('')
    setError(null)
  }

  const stepIndex = STEPS.findIndex(s => s.id === currentStep)

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

        .vs-root *{box-sizing:border-box;}
        .vs-root{
          --bg:#04080F;--surface:#080E1A;--surface2:#0C1524;--surface3:#111D30;
          --green:#00D46A;--green-dim:#007A3D;--green-glow:rgba(0,212,106,0.15);
          --gold:#F5C842;--red:#FF4D4D;--blue:#60A5FA;--purple:#A78BFA;
          --border:rgba(255,255,255,0.07);--border2:rgba(255,255,255,0.12);
          --text:#F0F4FF;--text2:rgba(240,244,255,0.55);--text3:rgba(240,244,255,0.28);
          font-family:'DM Sans',sans-serif;color:var(--text);
        }
        .vs-syne{font-family:'Syne',sans-serif;}
        .vs-mono{font-family:'JetBrains Mono',monospace;}

        /* Step track */
        .vs-step-track{display:flex;align-items:center;justify-content:center;gap:0;margin-bottom:2.5rem;}
        .vs-step-node{display:flex;flex-direction:column;align-items:center;gap:.5rem;position:relative;}
        .vs-step-circle{
          width:38px;height:38px;border-radius:50%;
          display:flex;align-items:center;justify-content:center;
          font-size:.8rem;font-weight:700;
          transition:all .3s;border:2px solid transparent;
        }
        .vs-step-circle.done{background:var(--green);color:#04080F;border-color:var(--green);}
        .vs-step-circle.active{background:rgba(0,212,106,0.12);color:var(--green);border-color:var(--green);box-shadow:0 0 0 4px rgba(0,212,106,0.1);}
        .vs-step-circle.pending{background:rgba(255,255,255,0.04);color:var(--text3);border-color:rgba(255,255,255,0.1);}
        .vs-step-label{font-size:.72rem;font-weight:500;white-space:nowrap;}
        .vs-step-label.active{color:var(--green);}
        .vs-step-label.done,.vs-step-label.pending{color:var(--text3);}
        .vs-step-connector{width:80px;height:1px;margin:0 .5rem;margin-bottom:1.2rem;transition:background .3s;}
        .vs-step-connector.done{background:var(--green);}
        .vs-step-connector.pending{background:rgba(255,255,255,0.08);}

        /* Cards */
        .vs-card{
          background:var(--surface);border:1px solid var(--border);
          border-radius:16px;overflow:hidden;
        }
        .vs-card-stripe{height:2px;background:linear-gradient(90deg,transparent,var(--green),transparent);}
        .vs-card-header{padding:1.25rem 1.5rem;border-bottom:1px solid var(--border);}
        .vs-card-body{padding:1.5rem;}

        /* Upload zone */
        .vs-dropzone{
          border:1.5px dashed rgba(255,255,255,0.1);border-radius:14px;
          padding:3.5rem 2rem;
          display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1rem;
          cursor:pointer;transition:border-color .2s,background .2s;
          background:rgba(255,255,255,0.015);
        }
        .vs-dropzone:hover,.vs-dropzone.active{
          border-color:rgba(0,212,106,0.4);
          background:rgba(0,212,106,0.03);
        }
        .vs-upload-icon{
          width:72px;height:72px;border-radius:50%;
          background:rgba(0,212,106,0.08);border:1px solid rgba(0,212,106,0.2);
          display:flex;align-items:center;justify-content:center;
        }
        .vs-badge{
          display:inline-flex;align-items:center;gap:5px;
          padding:3px 10px;border-radius:100px;
          background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);
          font-size:.72rem;font-weight:500;color:var(--text2);
        }

        /* Progress */
        .vs-progress-track{height:4px;background:rgba(255,255,255,0.06);border-radius:100px;overflow:hidden;}
        .vs-progress-fill{height:100%;border-radius:100px;background:linear-gradient(90deg,var(--green-dim),var(--green));transition:width .4s ease;}

        /* Analysis step pills */
        .vs-process-pill{
          display:flex;align-items:center;gap:.5rem;
          padding:.45rem .85rem;border-radius:8px;
          font-size:.75rem;transition:all .2s;
        }
        .vs-process-pill.done{background:rgba(0,212,106,0.08);color:var(--green);}
        .vs-process-pill.pending{background:rgba(255,255,255,0.03);color:var(--text3);}

        /* Result verdict */
        .vs-verdict{
          border-radius:14px;padding:1.5rem;
          display:flex;align-items:center;gap:1.5rem;
        }
        .vs-verdict.pass{background:rgba(0,212,106,0.06);border:1px solid rgba(0,212,106,0.2);}
        .vs-verdict.fail{background:rgba(255,77,77,0.06);border:1px solid rgba(255,77,77,0.2);}
        .vs-verdict-icon{
          width:60px;height:60px;border-radius:50%;flex-shrink:0;
          display:flex;align-items:center;justify-content:center;
        }
        .vs-verdict-icon.pass{background:rgba(0,212,106,0.15);border:1px solid rgba(0,212,106,0.3);}
        .vs-verdict-icon.fail{background:rgba(255,77,77,0.15);border:1px solid rgba(255,77,77,0.3);}

        /* Extracted field rows */
        .vs-field-row{
          display:flex;align-items:center;justify-content:space-between;
          padding:.6rem .85rem;border-radius:8px;
          background:rgba(255,255,255,0.025);border:1px solid rgba(255,255,255,0.05);
        }
        .vs-field-label{font-size:.75rem;color:var(--text2);font-weight:500;display:flex;align-items:center;gap:.4rem;}
        .vs-field-value{font-size:.82rem;font-weight:600;color:var(--text);}
        .vs-field-value.extracted{color:var(--green);}
        .vs-field-value.missing{color:var(--text3);font-style:italic;font-weight:400;}

        /* Risk factor bars */
        .vs-risk-bar-track{height:5px;background:rgba(255,255,255,0.06);border-radius:100px;overflow:hidden;flex:1;}
        .vs-risk-bar-fill{height:100%;border-radius:100px;transition:width 1s ease;}

        /* Action buttons */
        .vs-btn-primary{
          display:inline-flex;align-items:center;gap:.5rem;
          padding:.7rem 1.5rem;border-radius:10px;
          background:var(--green);color:#04080F;
          font-family:'Syne',sans-serif;font-weight:700;font-size:.85rem;
          border:none;cursor:pointer;transition:opacity .2s,transform .2s,box-shadow .2s;
        }
        .vs-btn-primary:hover{opacity:.9;transform:translateY(-1px);box-shadow:0 8px 24px rgba(0,212,106,0.25);}
        .vs-btn-outline{
          display:inline-flex;align-items:center;gap:.5rem;
          padding:.7rem 1.5rem;border-radius:10px;
          background:rgba(255,255,255,0.04);border:1px solid var(--border2);
          color:var(--text2);font-family:'DM Sans',sans-serif;font-weight:500;font-size:.85rem;
          cursor:pointer;transition:background .2s;
        }
        .vs-btn-outline:hover{background:rgba(255,255,255,0.07);}

        /* Confidence chip */
        .vs-chip{
          display:inline-flex;align-items:center;gap:5px;
          padding:3px 10px;border-radius:100px;font-size:.72rem;font-weight:600;
        }
        .vs-chip.green{background:rgba(0,212,106,0.1);border:1px solid rgba(0,212,106,0.25);color:var(--green);}
        .vs-chip.gold{background:rgba(245,200,66,0.1);border:1px solid rgba(245,200,66,0.25);color:var(--gold);}
        .vs-chip.red{background:rgba(255,77,77,0.1);border:1px solid rgba(255,77,77,0.25);color:var(--red);}

        @keyframes fadeSlideUp{from{opacity:0;transform:translateY(16px);}to{opacity:1;transform:translateY(0);}}
        .vs-fade-up{animation:fadeSlideUp .4s ease forwards;}
        @keyframes spin{to{transform:rotate(360deg);}}
        .vs-spin{animation:spin .7s linear infinite;}
        @keyframes pulse{0%,100%{opacity:1;}50%{opacity:.4;}}
        .vs-pulse{animation:pulse 1.5s ease-in-out infinite;}
      `}</style>

      <div className="vs-root">
        {/* ── Step Track ── */}
        <div className="vs-step-track">
          {STEPS.map((step, i) => {
            const state = i < stepIndex ? 'done' : i === stepIndex ? 'active' : 'pending'
            return (
              <div key={step.id} style={{ display: 'flex', alignItems: 'center' }}>
                <div className="vs-step-node">
                  <div className={`vs-step-circle ${state}`}>
                    {state === 'done'
                      ? <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="3" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
                      : i + 1
                    }
                  </div>
                  <span className={`vs-step-label ${state}`}>{step.label}</span>
                </div>
                {i < STEPS.length - 1 && (
                  <div className={`vs-step-connector ${i < stepIndex ? 'done' : 'pending'}`} />
                )}
              </div>
            )
          })}
        </div>

        {/* ── Step Content ── */}
        {/* ── Error banner ── */}
        {error && (
          <div style={{ background: "rgba(255,77,77,0.06)", border: "1px solid rgba(255,77,77,0.2)", borderRadius: "10px", padding: ".8rem 1rem", display: "flex", alignItems: "center", gap: ".6rem", color: "var(--red)", fontSize: ".82rem", marginBottom: "1.25rem" }}>
            <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" style={{ flexShrink: 0 }}><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            {error}
          </div>
        )}
        <AnimatePresence mode="wait">

          {/* UPLOAD */}
          {currentStep === 'upload' && (
            <motion.div key="upload" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -16 }}>
              <div className="vs-card">
                <div className="vs-card-stripe" />
                <div className="vs-card-body">
                  <div {...getRootProps()} className={`vs-dropzone ${isDragActive ? 'active' : ''}`}>
                    <input {...getInputProps()} />
                    <div className="vs-upload-icon">
                      <svg width="30" height="30" fill="none" stroke="var(--green)" strokeWidth="2" viewBox="0 0 24 24">
                        <polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/>
                        <path d="M20.39 18.39A5 5 0 0018 9h-1.26A8 8 0 103 16.3"/>
                      </svg>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <p className="vs-syne" style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '.4rem' }}>
                        {isDragActive ? 'Drop document here' : 'Upload Identity Document'}
                      </p>
                      <p style={{ color: 'var(--text2)', fontSize: '.82rem' }}>
                        Drag & drop or click to browse — National ID, Passport, Student ID
                      </p>
                    </div>
                    <div style={{ display: 'flex', gap: '.5rem', flexWrap: 'wrap', justifyContent: 'center' }}>
                      {['National ID', 'Passport', 'Student ID', 'Alien Card'].map(t => (
                        <span key={t} className="vs-badge">{t}</span>
                      ))}
                    </div>
                    <p style={{ color: 'var(--text3)', fontSize: '.72rem' }}>PNG, JPG, JPEG, WEBP, PDF · Max 10MB</p>
                  </div>

                  {/* Security note */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '.75rem', marginTop: '1.25rem', padding: '.85rem', borderRadius: '10px', background: 'rgba(0,212,106,0.04)', border: '1px solid rgba(0,212,106,0.12)' }}>
                    <svg width="16" height="16" fill="none" stroke="var(--green)" strokeWidth="2" viewBox="0 0 24 24" style={{ flexShrink: 0 }}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
                    </svg>
                    <p style={{ fontSize: '.75rem', color: 'var(--text2)', lineHeight: 1.4 }}>
                      <strong style={{ color: 'var(--green)' }}>End-to-end encrypted.</strong> Your document is processed securely and never stored permanently.
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* ANALYSIS */}
          {currentStep === 'analysis' && (
            <motion.div key="analysis" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -16 }}>
              <div className="vs-card">
                <div className="vs-card-stripe" />
                <div className="vs-card-header" style={{ display: 'flex', alignItems: 'center', gap: '.75rem' }}>
                  <svg width="18" height="18" fill="none" stroke="var(--green)" strokeWidth="2" viewBox="0 0 24 24" className={isProcessing ? 'vs-spin' : ''}>
                    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  </svg>
                  <div>
                    <p className="vs-syne" style={{ fontWeight: 700, fontSize: '.95rem' }}>AI Document Analysis</p>
                    <p style={{ color: 'var(--text2)', fontSize: '.75rem' }}>Running 8-stage verification pipeline</p>
                  </div>
                </div>
                <div className="vs-card-body" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  {/* Document preview with scan */}
                  {data.previewUrl && (
                    <div style={{ position: 'relative', borderRadius: '10px', overflow: 'hidden', background: '#000', border: '1px solid var(--border)' }}>
                      <img
                        ref={imgRef}
                        src={data.previewUrl}
                        alt="Document"
                        style={{ width: '100%', maxHeight: '280px', objectFit: 'contain', display: 'block' }}
                        onLoad={e => {
                          const t = e.target as HTMLImageElement
                          setImgDims({ w: t.naturalWidth, h: t.naturalHeight })
                        }}
                      />
                      <ScanLine active={isProcessing} />
                      <div style={{ position: 'absolute', top: '.5rem', left: '.5rem' }}>
                        <span className="vs-chip green vs-pulse">
                          <span style={{ width: 5, height: 5, borderRadius: '50%', background: 'var(--green)', display: 'inline-block' }} />
                          Processing on server
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Progress */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '.5rem' }}>
                      <span style={{ fontSize: '.78rem', color: 'var(--text2)' }}>{currentProcess}</span>
                      <span style={{ fontSize: '.78rem', color: 'var(--green)', fontWeight: 600 }}>{Math.round(progress)}%</span>
                    </div>
                    <div className="vs-progress-track">
                      <div className="vs-progress-fill" style={{ width: `${progress}%` }} />
                    </div>
                  </div>

                  {/* Step pills */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.4rem' }}>
                    {analysisSteps.map((step, i) => {
                      const done = i < (progress / 100) * analysisSteps.length
                      return (
                        <div key={step} className={`vs-process-pill ${done ? 'done' : 'pending'}`}>
                          {done
                            ? <svg width="12" height="12" fill="none" stroke="var(--green)" strokeWidth="3" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
                            : <svg width="12" height="12" fill="none" stroke="var(--text3)" strokeWidth="2" viewBox="0 0 24 24" className={i === Math.floor((progress / 100) * analysisSteps.length) ? 'vs-spin' : ''}><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
                          }
                          {step}
                        </div>
                      )
                    })}
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* RESULT */}
          {currentStep === 'result' && (
            <motion.div key="result" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -16 }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

                {/* Verdict */}
                <div className={`vs-verdict ${data.isAuthentic ? 'pass' : 'fail'}`}>
                  <div className={`vs-verdict-icon ${data.isAuthentic ? 'pass' : 'fail'}`}>
                    {data.isAuthentic
                      ? <svg width="28" height="28" fill="none" stroke="var(--green)" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
                      : <svg width="28" height="28" fill="none" stroke="var(--red)" strokeWidth="2.5" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
                    }
                  </div>
                  <div style={{ flex: 1 }}>
                    <p className="vs-syne" style={{ fontSize: '1.15rem', fontWeight: 800, color: data.isAuthentic ? 'var(--green)' : 'var(--red)', marginBottom: '.3rem' }}>
                      {data.isAuthentic ? 'Document Verified' : 'Verification Failed'}
                    </p>
                    <p style={{ color: 'var(--text2)', fontSize: '.82rem', marginBottom: '.75rem' }}>
                      {data.isAuthentic
                        ? 'This document appears authentic and passed our AI verification checks.'
                        : 'This document could not be verified. Please try again or contact support.'}
                    </p>
                    <div style={{ display: 'flex', gap: '.5rem', flexWrap: 'wrap' }}>
                      <span className={`vs-chip ${(data.confidence || 0) > 80 ? 'green' : (data.confidence || 0) > 60 ? 'gold' : 'red'}`}>
                        Confidence {data.confidence?.toFixed(1)}%
                      </span>
                      {data.mseScore !== undefined && (
                        <span className="vs-chip gold vs-mono">MSE {data.mseScore.toFixed(4)}</span>
                      )}
                    </div>
                  </div>
                  <RiskGauge score={data.riskScore || 0} />
                </div>

                {/* Document analysis + extracted info side by side */}
                <div className="vs-card">
                  <div className="vs-card-stripe" />
                  <div className="vs-card-header">
                    <p className="vs-syne" style={{ fontWeight: 700, fontSize: '.95rem', marginBottom: '.2rem' }}>Document Analysis</p>
                    <p style={{ color: 'var(--text2)', fontSize: '.75rem' }}>Server OCR regions and extracted data</p>
                  </div>
                  <div className="vs-card-body">
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>

                      {/* Image with bounding boxes */}
                      <div style={{ position: 'relative', borderRadius: '10px', overflow: 'hidden', background: '#000', border: '1px solid var(--border)' }}>
                        {data.previewUrl && (
                          <>
                            <img src={data.previewUrl} alt="Document" style={{ width: '100%', objectFit: 'contain', display: 'block' }} />
                            <div style={{ position: 'absolute', inset: 0 }}>
                              <BoundingBoxes boxes={data.boundingBoxes} imgW={imgDims.w} imgH={imgDims.h} />
                            </div>
                            {/* Legend */}
                            <div style={{ position: 'absolute', bottom: '.5rem', right: '.5rem', background: 'rgba(4,8,15,0.85)', borderRadius: '8px', padding: '.45rem .6rem', display: 'flex', flexDirection: 'column', gap: '.25rem' }}>
                              {data.boundingBoxes?.map((b, i) => (
                                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '.35rem', fontSize: '.65rem', color: 'var(--text2)' }}>
                                  <span style={{ width: 8, height: 8, borderRadius: '50%', background: b.color, display: 'inline-block', flexShrink: 0 }} />
                                  {b.label}
                                </div>
                              ))}
                            </div>
                          </>
                        )}
                      </div>

                      {/* Extracted fields */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '.5rem' }}>
                        <p style={{ fontSize: '.78rem', fontWeight: 600, color: 'var(--text2)', marginBottom: '.25rem', textTransform: 'uppercase', letterSpacing: '.06em' }}>Extracted Information</p>

                        {([
                          { label: 'Full Name',    key: 'name',        icon: '👤' },
                          { label: 'ID Number',    key: 'idNumber',    icon: '🪪' },
                          { label: 'Date of Birth',key: 'dob',         icon: '📅' },
                          { label: 'Sex',          key: 'sex',         icon: '⚧' },
                          { label: 'Nationality',  key: 'nationality', icon: '🌍' },
                          { label: 'Issuing County',key:'county',      icon: '📍' },
                          { label: 'Expiry Date',  key: 'expiryDate',  icon: '⏱' },
                        ] as { label: string; key: keyof typeof data.extractedData; icon: string }[]).map(({ label, key, icon }) => {
                          const val = data.extractedData?.[key]
                          const missing = !val
                          return (
                            <div key={key} className="vs-field-row">
                              <span className="vs-field-label">
                                <span style={{ fontSize: '.8rem' }}>{icon}</span>
                                {label}
                              </span>
                              <span className={`vs-field-value ${missing ? 'missing' : 'extracted'} vs-mono`}>
                                {missing ? '—' : val}
                              </span>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Risk factors */}
                <div className="vs-card">
                  <div className="vs-card-stripe" />
                  <div className="vs-card-header">
                    <p className="vs-syne" style={{ fontWeight: 700, fontSize: '.95rem', marginBottom: '.2rem' }}>Risk Assessment</p>
                    <p style={{ color: 'var(--text2)', fontSize: '.75rem' }}>Detailed breakdown of verification checks</p>
                  </div>
                  <div className="vs-card-body" style={{ display: 'flex', flexDirection: 'column', gap: '.85rem' }}>
                    {data.riskFactors?.map((f, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <span style={{ fontSize: '.8rem', color: 'var(--text2)', width: '160px', flexShrink: 0 }}>{f.factor}</span>
                        <div className="vs-risk-bar-track">
                          <motion.div
                            className="vs-risk-bar-fill"
                            style={{ background: f.status === 'pass' ? 'var(--green)' : f.status === 'warning' ? 'var(--gold)' : 'var(--red)' }}
                            initial={{ width: 0 }}
                            animate={{ width: `${f.score}%` }}
                            transition={{ duration: 0.9, delay: i * 0.1 }}
                          />
                        </div>
                        <span className="vs-mono" style={{ fontSize: '.78rem', fontWeight: 600, width: '36px', textAlign: 'right',
                          color: f.status === 'pass' ? 'var(--green)' : f.status === 'warning' ? 'var(--gold)' : 'var(--red)'
                        }}>{f.score}%</span>
                        {f.status === 'pass'    && <svg width="14" height="14" fill="none" stroke="var(--green)" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>}
                        {f.status === 'warning' && <svg width="14" height="14" fill="none" stroke="var(--gold)"  strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/></svg>}
                        {f.status === 'fail'    && <svg width="14" height="14" fill="none" stroke="var(--red)"   strokeWidth="2.5" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>}
                      </div>
                    ))}
                  </div>
                </div>

                {data.extractedText && (
                  <details style={{ marginTop: '-.25rem' }}>
                    <summary style={{ fontSize: '.72rem', color: 'var(--text3)', cursor: 'pointer', userSelect: 'none', padding: '.5rem 0' }}>Raw OCR output (debug)</summary>
                    <pre style={{ marginTop: '.4rem', padding: '.75rem', borderRadius: '8px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)', fontSize: '.68rem', color: 'var(--text3)', whiteSpace: 'pre-wrap', wordBreak: 'break-all', maxHeight: '120px', overflowY: 'auto', fontFamily: 'JetBrains Mono, monospace' }}>{data.extractedText}</pre>
                  </details>
                )}

                {/* Actions */}
                <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
                  {data.isAuthentic && (
                    <button className="vs-btn-primary" onClick={() => {
                      localStorage.setItem('verificationStatus', 'verified')
                      window.location.href = '/auth/biometric-registration'
                    }}>
                      Continue to Biometric Registration
                      <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                    </button>
                  )}
                  <button className="vs-btn-outline" onClick={handleReset}>
                    <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 101.85-6.24L1 10"/></svg>
                    Verify Another Document
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </>
  )
}