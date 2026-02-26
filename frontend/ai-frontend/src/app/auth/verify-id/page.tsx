"use client"

import { useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

export default function VerifyID() {
  const [isScanning, setIsScanning] = useState(false)
  const [scanComplete, setScanComplete] = useState(false)
  const [verificationResult, setVerificationResult] = useState<'success' | 'failed' | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [step, setStep] = useState(0)
  const [verificationData, setVerificationData] = useState<any>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const router = useRouter()

  const scanSteps = [
    'Analyzing document features...',
    'Checking security elements...',
    'Running ELA detection...',
    'Verifying authenticity...',
    'Generating confidence score...',
  ]

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    
    setIsProcessing(true)
    setIsScanning(true)
    setProgress(0)
    setStep(0)

    const stepInterval = setInterval(() => {
      setStep(prev => Math.min(prev + 1, scanSteps.length - 1))
    }, 550)

    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) { clearInterval(progressInterval); return 100 }
        return prev + 3.5
      })
    }, 100)

    try {
      // Call backend document verification API
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('http://localhost:8000/api/v1/document/verify', {
        method: 'POST',
        body: formData
      })

      const result = await response.json()
      
      // Clear intervals
      clearInterval(stepInterval)
      clearInterval(progressInterval)
      setProgress(100)
      setStep(scanSteps.length - 1)

      if (response.ok && result.authentic) {
        setVerificationResult('success')
        setVerificationData(result)
        // Store verification status
        localStorage.setItem('verificationStatus', 'verified')
        localStorage.setItem('documentVerification', JSON.stringify({
          authentic: result.authentic,
          confidence: result.confidence,
          mse_score: result.mse_score,
          timestamp: new Date().toISOString()
        }))
      } else {
        setVerificationResult('failed')
        localStorage.setItem('verificationStatus', 'pending')
      }
    } catch (error) {
      console.error('Document verification failed:', error)
      // Clear intervals
      clearInterval(stepInterval)
      clearInterval(progressInterval)
      setProgress(100)
      setStep(scanSteps.length - 1)
      
      // Default to failed on network error
      setVerificationResult('failed')
      localStorage.setItem('verificationStatus', 'pending')
    } finally {
      setScanComplete(true)
      setIsScanning(false)
      setIsProcessing(false)
    }
  }

  const handleRetake = () => {
    setScanComplete(false)
    setVerificationResult(null)
    setProgress(0)
    setStep(0)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleContinue = () => {
    if (verificationResult === 'success') router.push('/auth/biometric-registration')
    else {
      localStorage.setItem('verificationStatus', 'pending')
      router.push('/user-dashboard')
    }
  }

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');
        *{box-sizing:border-box;margin:0;padding:0;}
        :root{
          --bg:#04080F;--surface:#080E1A;--surface2:#0C1524;
          --green:#00D46A;--green-dim:#007A3D;--green-glow:rgba(0,212,106,0.12);
          --red:#FF4D4D;--gold:#F5C842;
          --border:rgba(255,255,255,0.07);--border2:rgba(255,255,255,0.12);
          --text:#F0F4FF;--text2:rgba(240,244,255,0.55);--text3:rgba(240,244,255,0.28);
        }
        body{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;min-height:100vh;}
        .syne{font-family:'Syne',sans-serif;}
        .grid-bg{background-image:linear-gradient(rgba(0,212,106,0.025) 1px,transparent 1px),linear-gradient(90deg,rgba(0,212,106,0.025) 1px,transparent 1px);background-size:60px 60px;}
        .orb{position:absolute;border-radius:50%;filter:blur(100px);pointer-events:none;}
        .card{background:var(--surface);border:1px solid var(--border);border-radius:20px;padding:2.5rem;position:relative;overflow:hidden;}
        .upload-zone{
          border:1.5px dashed rgba(255,255,255,0.12);border-radius:16px;
          padding:3rem 2rem;text-align:center;cursor:pointer;
          transition:border-color .2s,background .2s;position:relative;overflow:hidden;
        }
        .upload-zone:hover{border-color:rgba(0,212,106,0.35);background:rgba(0,212,106,0.02);}
        .progress-bar{height:3px;background:rgba(255,255,255,0.06);border-radius:100px;overflow:hidden;margin:1rem 0;}
        .progress-fill{height:100%;border-radius:100px;background:linear-gradient(90deg,var(--green-dim),var(--green));transition:width .1s linear;}
        .btn-primary{
          padding:.8rem 2rem;border-radius:10px;background:var(--green);color:#04080F;
          font-family:'Syne',sans-serif;font-weight:700;font-size:.9rem;border:none;cursor:pointer;
          transition:opacity .2s,transform .2s,box-shadow .2s;display:inline-flex;align-items:center;gap:8px;
        }
        .btn-primary:hover{opacity:.9;transform:translateY(-1px);box-shadow:0 8px 30px rgba(0,212,106,0.25);}
        .btn-ghost{
          padding:.8rem 2rem;border-radius:10px;background:transparent;color:var(--text2);
          font-family:'DM Sans',sans-serif;font-size:.9rem;border:1px solid var(--border2);cursor:pointer;
          transition:background .2s,border-color .2s;display:inline-flex;align-items:center;gap:8px;
        }
        .btn-ghost:hover{background:rgba(255,255,255,0.04);border-color:rgba(255,255,255,0.2);}
        .scan-step{display:flex;align-items:center;gap:10px;padding:.6rem 0;color:var(--text2);font-size:.85rem;}
        .step-dot{width:8px;height:8px;border-radius:50%;background:var(--green);flex-shrink:0;}
        @keyframes scanPulse{0%,100%{opacity:.3;}50%{opacity:1;}}
        .scanning .step-dot{animation:scanPulse 1s infinite;}
        @keyframes scanBeam{0%{top:-10%;}100%{top:110%;}}
        .scan-beam{position:absolute;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--green),transparent);animation:scanBeam 2s linear infinite;pointer-events:none;}
        @keyframes fadeIn{from{opacity:0;transform:translateY(16px);}to{opacity:1;transform:translateY(0);}}
        .fade-in{animation:fadeIn .5s ease forwards;}
        .success-ring{
          width:80px;height:80px;border-radius:50%;border:2px solid var(--green);
          display:flex;align-items:center;justify-content:center;margin:0 auto 1.5rem;
          background:rgba(0,212,106,0.08);
        }
        .fail-ring{
          width:80px;height:80px;border-radius:50%;border:2px solid var(--red);
          display:flex;align-items:center;justify-content:center;margin:0 auto 1.5rem;
          background:rgba(255,77,77,0.08);
        }
        .tip-item{display:flex;align-items:flex-start;gap:10px;color:var(--text2);font-size:.85rem;line-height:1.6;margin-bottom:.6rem;}
      `}</style>

      <div className="grid-bg" style={{minHeight:'100vh',display:'flex',alignItems:'center',justifyContent:'center',padding:'2rem',position:'relative'}}>
        <div className="orb" style={{width:500,height:500,background:'rgba(59,130,246,0.05)',top:'-5%',right:'0%'}}/>
        <div className="orb" style={{width:400,height:400,background:'rgba(0,212,106,0.04)',bottom:'0%',left:'0%'}}/>

        <div className="fade-in" style={{width:'100%',maxWidth:560}}>
          {/* Header */}
          <div style={{textAlign:'center',marginBottom:'2rem'}}>
            <div style={{
              width:52,height:52,borderRadius:14,margin:'0 auto 1rem',
              background:'linear-gradient(135deg,#3B82F6,#1D4ED8)',
              display:'flex',alignItems:'center',justifyContent:'center',
            }}>
              <svg width="26" height="26" fill="none" stroke="#fff" strokeWidth="2.5" viewBox="0 0 24 24">
                <rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/>
              </svg>
            </div>
            <h1 className="syne" style={{fontSize:'1.6rem',fontWeight:800,marginBottom:'.35rem'}}>Verify Your Identity</h1>
            <p style={{color:'var(--text2)',fontSize:'.88rem',maxWidth:400,margin:'0 auto'}}>
              Upload a clear photo of your national ID for AI-powered forgery detection
            </p>
          </div>

          <div className="card">
            <div style={{position:'absolute',top:0,left:0,right:0,height:2,background:'linear-gradient(90deg,transparent,#3B82F6,transparent)'}}/>

            {!scanComplete ? (
              <div>
                {/* Upload zone */}
                <div className="upload-zone">
                  <input ref={fileInputRef} type="file" accept="image/*" onChange={handleFileUpload}
                    style={{position:'absolute',inset:0,opacity:0,cursor:'pointer'}} disabled={isProcessing}/>
                  {isScanning && <div className="scan-beam"/>}

                  {!isScanning ? (
                    <>
                      <div style={{
                        width:64,height:64,borderRadius:'50%',background:'rgba(59,130,246,0.1)',
                        border:'1px solid rgba(59,130,246,0.25)',
                        display:'flex',alignItems:'center',justifyContent:'center',margin:'0 auto 1.25rem',
                      }}>
                        <svg width="28" height="28" fill="none" stroke="#3B82F6" strokeWidth="1.5" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                        </svg>
                      </div>
                      <p style={{fontWeight:500,marginBottom:'.35rem'}}>Drop your ID card here</p>
                      <p style={{color:'var(--text3)',fontSize:'.82rem'}}>PNG, JPG up to 10MB — or <span style={{color:'#3B82F6'}}>click to browse</span></p>
                    </>
                  ) : (
                    <div>
                      <div style={{
                        width:64,height:64,borderRadius:'50%',background:'rgba(0,212,106,0.1)',
                        border:'1px solid rgba(0,212,106,0.3)',
                        display:'flex',alignItems:'center',justifyContent:'center',margin:'0 auto 1.25rem',
                      }}>
                        <svg width="28" height="28" fill="none" stroke="var(--green)" strokeWidth="2" viewBox="0 0 24 24" style={{animation:'spin .8s linear infinite'}}>
                          <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" strokeOpacity=".2"/>
                          <path d="M21 12a9 9 0 00-9-9"/>
                        </svg>
                      </div>
                      <p style={{fontWeight:500,color:'var(--green)',marginBottom:'.75rem'}}>Scanning document...</p>
                      <div className="progress-bar">
                        <div className="progress-fill" style={{width:`${progress}%`}}/>
                      </div>
                      <div style={{marginTop:'.75rem'}}>
                        {scanSteps.map((s, i) => (
                          <div key={s} className={`scan-step ${i <= step ? 'scanning' : ''}`} style={{opacity: i > step ? 0.3 : 1}}>
                            <span className="step-dot" style={{background: i < step ? 'var(--green)' : i === step ? 'var(--green)' : 'rgba(255,255,255,0.1)'}}/>
                            {s}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Tips */}
                <div style={{
                  marginTop:'1.5rem',background:'rgba(59,130,246,0.05)',
                  border:'1px solid rgba(59,130,246,0.15)',borderRadius:12,padding:'1rem 1.25rem',
                }}>
                  <p style={{fontSize:'.82rem',fontWeight:600,color:'#3B82F6',marginBottom:'.75rem'}}>For best results</p>
                  {['Good lighting, no glare or reflections','Place ID on flat, contrasting surface','Capture all four corners clearly','Text must be fully readable'].map(t => (
                    <div key={t} className="tip-item">
                      <svg width="14" height="14" fill="none" stroke="var(--green)" strokeWidth="2.5" viewBox="0 0 24 24" style={{flexShrink:0,marginTop:2}}>
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                      {t}
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div style={{textAlign:'center'}}>
                {verificationResult === 'success' ? (
                  <>
                    <div className="success-ring">
                      <svg width="36" height="36" fill="none" stroke="var(--green)" strokeWidth="2" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                      </svg>
                    </div>
                    <h3 className="syne" style={{fontSize:'1.35rem',fontWeight:700,color:'var(--green)',marginBottom:'.5rem'}}>Verification Successful</h3>
                    <p style={{color:'var(--text2)',fontSize:'.9rem',marginBottom:'2rem'}}>
                      Your ID has been authenticated. Proceed to biometric registration.
                    </p>
                    <div style={{
                      background:'rgba(0,212,106,0.05)',border:'1px solid rgba(0,212,106,0.2)',
                      borderRadius:12,padding:'1rem',marginBottom:'2rem',
                      display:'grid',gridTemplateColumns:'1fr 1fr',gap:'1rem',
                    }}>
                      {verificationData ? [
                        ['Authenticity', verificationData.authentic ? 'Verified' : 'Failed'],
                        ['Confidence', `${verificationData.confidence?.toFixed(1) || 'N/A'}%`],
                        ['MSE Score', verificationData.mse_score?.toFixed(4) || 'N/A'],
                        ['Risk Level', verificationData.authentic ? 'Low' : 'High']
                      ] : [
                        ['Authenticity','Verified'],
                        ['Confidence','97.3%'],
                        ['ELA Score','0.012'],
                        ['Risk Level','Low']
                      ].map(([k,v]) => (
                        <div key={k}>
                          <p style={{color:'var(--text3)',fontSize:'.75rem',marginBottom:'.2rem'}}>{k}</p>
                          <p style={{fontWeight:600,fontSize:'.9rem',color:'var(--green)'}}>{v}</p>
                        </div>
                      ))}
                    </div>
                    <button className="btn-primary" onClick={handleContinue} style={{width:'100%',justifyContent:'center'}}>
                      Continue to Biometrics →
                    </button>
                  </>
                ) : (
                  <>
                    <div className="fail-ring">
                      <svg width="36" height="36" fill="none" stroke="var(--red)" strokeWidth="2" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                      </svg>
                    </div>
                    <h3 className="syne" style={{fontSize:'1.35rem',fontWeight:700,color:'var(--red)',marginBottom:'.5rem'}}>Verification Failed</h3>
                    <p style={{color:'var(--text2)',fontSize:'.9rem',marginBottom:'2rem'}}>
                      We couldn&apos;t verify this document. Try again with a clearer image, or continue with pending status.
                    </p>
                    <div style={{display:'flex',gap:'.75rem'}}>
                      <button className="btn-ghost" onClick={handleRetake} style={{flex:1,justifyContent:'center'}}>Try Again</button>
                      <button className="btn-primary" onClick={handleContinue} style={{flex:1,justifyContent:'center',background:'rgba(255,255,255,0.08)',color:'var(--text2)',border:'1px solid var(--border2)'}}>Continue Pending</button>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>

          <div style={{textAlign:'center',marginTop:'1.5rem'}}>
            <Link href="/auth/signup" style={{color:'var(--text3)',textDecoration:'none',fontSize:'.84rem'}}>
              ← Back to Registration
            </Link>
          </div>
        </div>
      </div>
      <style>{`@keyframes spin{to{transform:rotate(360deg);}}`}</style>
    </>
  )
}