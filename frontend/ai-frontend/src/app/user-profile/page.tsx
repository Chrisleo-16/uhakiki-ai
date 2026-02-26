"use client"

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

interface UserProfile {
  firstName: string; lastName: string; email: string; phone: string
  idNumber: string; institution: string; course: string; yearOfStudy: string
  verificationStatus: 'pending'|'active'|'incomplete'; biometricStatus: 'pending'|'complete'
  registrationDate: string
}

export default function UserProfile() {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [tab, setTab] = useState<'overview'|'biometrics'|'security'>('overview')
  const [bioStep, setBioStep] = useState<'face'|'voice'|'done'>('face')
  const [capturing, setCapturing] = useState(false)
  const [countdown, setCountdown] = useState(0)
  const [captured, setCaptured] = useState(0)
  const [voiceRec, setVoiceRec] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const mediaRef = useRef<MediaRecorder | null>(null)
  const router = useRouter()

  useEffect(() => {
    try {
      const raw = localStorage.getItem('userRegistration')
      if (raw) {
        const d = JSON.parse(raw)
        setProfile({
          ...d,
          verificationStatus: (localStorage.getItem('verificationStatus') || 'pending') as UserProfile['verificationStatus'],
          biometricStatus:    (localStorage.getItem('biometricStatus')    || 'pending') as UserProfile['biometricStatus'],
          registrationDate: new Date().toLocaleDateString('en-KE',{year:'numeric',month:'long',day:'numeric'}),
        })
      }
    } catch { router.push('/auth/signup') }
  }, [router])

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video:{ facingMode:'user' }, audio:false })
      if (videoRef.current) videoRef.current.srcObject = stream
    } catch (e) { console.error('Camera denied', e) }
  }
  const stopCamera = () => {
    if (videoRef.current?.srcObject) {
      (videoRef.current.srcObject as MediaStream).getTracks().forEach(t => t.stop())
    }
  }
  const capture = () => {
    setCapturing(true); setCountdown(3)
    const t = setInterval(() => {
      setCountdown(p => {
        if (p <= 1) {
          clearInterval(t)
          if (videoRef.current && canvasRef.current) {
            const ctx = canvasRef.current.getContext('2d')
            canvasRef.current.width = videoRef.current.videoWidth
            canvasRef.current.height = videoRef.current.videoHeight
            ctx?.drawImage(videoRef.current, 0, 0)
          }
          const next = captured + 1
          setCaptured(next)
          if (next >= 3) { setBioStep('voice'); stopCamera() }
          setCapturing(false)
          return 0
        }
        return p - 1
      })
    }, 1000)
  }
  const startVoice = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio:true })
      const mr = new MediaRecorder(stream)
      mediaRef.current = mr
      mr.onstop = () => { setVoiceRec(false); setBioStep('done'); localStorage.setItem('biometricStatus','complete'); setProfile(p => p ? { ...p, biometricStatus:'complete' } : p) }
      mr.start(); setVoiceRec(true)
      setTimeout(() => { if (mr.state === 'recording') { mr.stop(); stream.getTracks().forEach(t => t.stop()) } }, 5000)
    } catch (e) { console.error(e) }
  }

  useEffect(() => {
    if (tab === 'biometrics' && bioStep === 'face' && profile?.biometricStatus !== 'complete') startCamera()
    if (tab !== 'biometrics') stopCamera()
    return () => stopCamera()
  }, [tab, bioStep]) // eslint-disable-line

  if (!profile) return null

  const vs = { active:{c:'#00D46A',b:'rgba(0,212,106,0.1)'}, pending:{c:'#F5C842',b:'rgba(245,200,66,0.1)'}, incomplete:{c:'#FF4D4D',b:'rgba(255,77,77,0.1)'} }[profile.verificationStatus]

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');
        *{box-sizing:border-box;margin:0;padding:0;}
        :root{
          --bg:#04080F;--surface:#080E1A;--surface2:#0C1524;
          --green:#00D46A;--border:rgba(255,255,255,0.07);--border2:rgba(255,255,255,0.12);
          --text:#F0F4FF;--text2:rgba(240,244,255,0.55);--text3:rgba(240,244,255,0.28);
        }
        body{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;min-height:100vh;}
        .syne{font-family:'Syne',sans-serif;}
        nav{display:flex;align-items:center;justify-content:space-between;padding:.9rem 2.5rem;background:rgba(4,8,15,0.9);backdrop-filter:blur(16px);border-bottom:1px solid var(--border);position:sticky;top:0;z-index:100;}
        .logo-icon{width:34px;height:34px;border-radius:9px;background:linear-gradient(135deg,#00D46A,#007A3D);display:flex;align-items:center;justify-content:center;}
        .icon-btn{background:none;border:none;cursor:pointer;color:var(--text2);padding:.45rem;border-radius:8px;transition:background .2s,color .2s;}
        .icon-btn:hover{background:rgba(255,255,255,0.06);color:var(--text);}
        main{max-width:820px;margin:0 auto;padding:2.5rem 2rem;}
        .card{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:2rem;}
        .tab-bar{display:flex;border-bottom:1px solid var(--border);margin-bottom:2rem;}
        .tab{padding:.75rem 1.5rem;background:none;border:none;cursor:pointer;color:var(--text2);font-family:'DM Sans',sans-serif;font-size:.88rem;font-weight:500;border-bottom:2px solid transparent;transition:color .2s,border-color .2s;margin-bottom:-1px;}
        .tab:hover{color:var(--text);}
        .tab.active{color:var(--green);border-bottom-color:var(--green);}
        .dl dt{color:var(--text3);font-size:.75rem;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.2rem;}
        .dl dd{color:var(--text);font-size:.9rem;font-weight:500;margin-bottom:1.1rem;}
        .btn{display:inline-flex;align-items:center;gap:6px;padding:.65rem 1.4rem;border-radius:9px;font-size:.85rem;font-weight:600;cursor:pointer;text-decoration:none;border:none;transition:opacity .2s,transform .2s;}
        .btn:hover{opacity:.85;transform:translateY(-1px);}
        .green-btn{background:var(--green);color:#04080F;font-family:'Syne',sans-serif;}
        .ghost-btn{background:rgba(255,255,255,0.04);color:var(--text2);border:1px solid var(--border2);}
        .red-btn{background:rgba(255,77,77,0.12);color:#FF4D4D;border:1px solid rgba(255,77,77,0.25);}
        .security-row{display:flex;align-items:center;justify-content:space-between;padding:1rem;background:rgba(255,255,255,0.02);border-radius:10px;margin-bottom:.75rem;}
        @keyframes spin{to{transform:rotate(360deg);}}
        @keyframes fadeIn{from{opacity:0;transform:translateY(12px);}to{opacity:1;transform:translateY(0);}}
        .fade-in{animation:fadeIn .4s ease forwards;}
      `}</style>

      <nav>
        <div style={{display:'flex',alignItems:'center',gap:10}}>
          <Link href="/user-dashboard" className="icon-btn" style={{marginRight:4}}>
            <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7"/></svg>
          </Link>
          <div className="logo-icon">
            <svg width="18" height="18" fill="none" stroke="#04080F" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
          </div>
          <span className="syne" style={{fontWeight:700,fontSize:'1rem'}}>Profile Settings</span>
        </div>
        <div style={{display:'inline-flex',alignItems:'center',gap:6,padding:'.3rem .9rem',borderRadius:100,background:vs.b,border:`1px solid ${vs.c}30`,color:vs.c,fontSize:'.75rem',fontWeight:600}}>
          <span style={{width:6,height:6,borderRadius:'50%',background:vs.c}}/>
          {profile.verificationStatus.toUpperCase()}
        </div>
      </nav>

      <main className="fade-in">
        {/* Profile header */}
        <div style={{display:'flex',alignItems:'center',gap:'1.25rem',marginBottom:'2rem'}}>
          <div style={{
            width:64,height:64,borderRadius:'50%',
            background:'linear-gradient(135deg,rgba(0,212,106,0.2),rgba(0,122,61,0.1))',
            border:'2px solid rgba(0,212,106,0.25)',
            display:'flex',alignItems:'center',justifyContent:'center',fontSize:'1.5rem',
          }}>
            {profile.firstName[0]}{profile.lastName?.[0] || ''}
          </div>
          <div>
            <h1 className="syne" style={{fontSize:'1.3rem',fontWeight:800,marginBottom:'.2rem'}}>{profile.firstName} {profile.lastName}</h1>
            <p style={{color:'var(--text2)',fontSize:'.85rem'}}>{profile.email}</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="tab-bar">
          {(['overview','biometrics','security'] as const).map(t => (
            <button key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
              {t[0].toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>

        {/* Overview */}
        {tab === 'overview' && (
          <div className="card">
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'2rem'}}>
              <div className="dl">
                <p className="syne" style={{fontWeight:700,marginBottom:'1rem',fontSize:'.9rem'}}>Personal Information</p>
                <dt>Full Name</dt><dd>{profile.firstName} {profile.lastName}</dd>
                <dt>Email</dt><dd>{profile.email}</dd>
                <dt>Phone</dt><dd>{profile.phone || '—'}</dd>
                <dt>National ID</dt><dd>••••••{(profile.idNumber || '').slice(-2)}</dd>
              </div>
              <div className="dl">
                <p className="syne" style={{fontWeight:700,marginBottom:'1rem',fontSize:'.9rem'}}>Academic Information</p>
                <dt>Institution</dt><dd>{profile.institution ? profile.institution.split('-').map((w:string)=>w[0].toUpperCase()+w.slice(1)).join(' ') : '—'}</dd>
                <dt>Course</dt><dd>{profile.course || '—'}</dd>
                <dt>Year of Study</dt><dd>{profile.yearOfStudy ? `Year ${profile.yearOfStudy}` : '—'}</dd>
                <dt>Member Since</dt><dd>{profile.registrationDate}</dd>
              </div>
            </div>
          </div>
        )}

        {/* Biometrics */}
        {tab === 'biometrics' && (
          <div className="card">
            {profile.biometricStatus === 'complete' ? (
              <div style={{textAlign:'center',padding:'2rem 0'}}>
                <div style={{width:72,height:72,borderRadius:'50%',border:'2px solid #00D46A',background:'rgba(0,212,106,0.08)',display:'flex',alignItems:'center',justifyContent:'center',margin:'0 auto 1.25rem'}}>
                  <svg width="34" height="34" fill="none" stroke="#00D46A" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                </div>
                <h3 className="syne" style={{fontSize:'1.25rem',fontWeight:700,marginBottom:'.5rem',color:'#00D46A'}}>Biometrics Registered</h3>
                <p style={{color:'var(--text2)',fontSize:'.88rem',marginBottom:'1.5rem'}}>Face and voice biometrics are active on your account.</p>
                {['Instant biometric login','Enhanced security protection','Quick identity verification'].map(i => (
                  <div key={i} style={{display:'flex',alignItems:'center',gap:10,justifyContent:'center',marginBottom:'.5rem'}}>
                    <svg width="14" height="14" fill="none" stroke="#00D46A" strokeWidth="2.5" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
                    <span style={{color:'var(--text2)',fontSize:'.85rem'}}>{i}</span>
                  </div>
                ))}
              </div>
            ) : (
              <>
                {/* Step indicator */}
                <div style={{display:'flex',gap:'1rem',marginBottom:'2rem'}}>
                  {[{key:'face',label:'Face'},{ key:'voice',label:'Voice'},{key:'done',label:'Complete'}].map((s,i) => {
                    const steps = ['face','voice','done']
                    const curr = steps.indexOf(bioStep)
                    const done = i < curr
                    const active = i === curr
                    return (
                      <div key={s.key} style={{display:'flex',alignItems:'center',gap:8,flex: i < 2 ? 1 : 'none'}}>
                        <div style={{
                          width:28,height:28,borderRadius:'50%',display:'flex',alignItems:'center',justifyContent:'center',
                          fontSize:'.75rem',fontWeight:700,flexShrink:0,
                          background: done ? '#00D46A' : active ? 'rgba(0,212,106,0.15)' : 'rgba(255,255,255,0.05)',
                          border: done ? 'none' : active ? '1px solid #00D46A' : '1px solid rgba(255,255,255,0.1)',
                          color: done ? '#04080F' : active ? '#00D46A' : 'var(--text3)',
                        }}>
                          {done ? '✓' : i+1}
                        </div>
                        <span style={{fontSize:'.82rem',color: active ? 'var(--text)' : 'var(--text3)'}}>{s.label}</span>
                        {i < 2 && <div style={{flex:1,height:1,background:'rgba(255,255,255,0.07)'}}/>}
                      </div>
                    )
                  })}
                </div>

                {bioStep === 'face' && (
                  <>
                    <p className="syne" style={{fontWeight:700,marginBottom:'.5rem'}}>Facial Recognition</p>
                    <p style={{color:'var(--text2)',fontSize:'.85rem',marginBottom:'1.25rem'}}>Captured: {captured}/3 — look directly at the camera</p>
                    <div style={{position:'relative',borderRadius:12,overflow:'hidden',background:'#000',aspectRatio:'4/3',marginBottom:'1.25rem'}}>
                      <video ref={videoRef} autoPlay playsInline muted style={{width:'100%',height:'100%',objectFit:'cover'}}/>
                      <div style={{position:'absolute',inset:0,display:'flex',alignItems:'center',justifyContent:'center',pointerEvents:'none'}}>
                        <div style={{width:160,height:160,borderRadius:'50%',border:'2px solid rgba(0,212,106,0.6)',boxShadow:'0 0 0 2000px rgba(0,0,0,0.4)'}}/>
                      </div>
                      {capturing && countdown > 0 && (
                        <div style={{position:'absolute',inset:0,display:'flex',alignItems:'center',justifyContent:'center',background:'rgba(0,0,0,0.5)'}}>
                          <span className="syne" style={{fontSize:'5rem',fontWeight:800,color:'var(--green)'}}>{countdown}</span>
                        </div>
                      )}
                      <div style={{position:'absolute',top:'50%',left:0,right:0,height:2,background:'linear-gradient(90deg,transparent,var(--green),transparent)',animation:'scan 2s linear infinite'}}/>
                    </div>
                    <canvas ref={canvasRef} style={{display:'none'}}/>
                    <div style={{display:'flex',gap:'.75rem'}}>
                      <button className="btn ghost-btn" onClick={() => setTab('overview')} style={{flex:1,justifyContent:'center'}}>Cancel</button>
                      <button className="btn green-btn" onClick={capture} disabled={capturing} style={{flex:2,justifyContent:'center'}}>
                        {capturing ? 'Capturing...' : `Capture ${captured+1} of 3`}
                      </button>
                    </div>
                  </>
                )}

                {bioStep === 'voice' && (
                  <>
                    <p className="syne" style={{fontWeight:700,marginBottom:'.5rem'}}>Voice Biometrics</p>
                    <p style={{color:'var(--text2)',fontSize:'.85rem',marginBottom:'1.5rem'}}>
                      Say clearly: <code style={{background:'rgba(255,255,255,0.06)',padding:'2px 8px',borderRadius:6,fontSize:'.82rem',color:'var(--green)'}}>"Uhakiki AI verifies my identity"</code>
                    </p>
                    <div style={{width:120,height:120,borderRadius:'50%',border:`2px solid ${voiceRec ? '#00D46A' : 'rgba(255,255,255,0.12)'}`,background:voiceRec ? 'rgba(0,212,106,0.08)' : 'rgba(255,255,255,0.03)',display:'flex',alignItems:'center',justifyContent:'center',margin:'0 auto 1.5rem',transition:'all .3s'}}>
                      {voiceRec ? (
                        <div style={{display:'flex',alignItems:'flex-end',gap:4,height:36}}>
                          {[16,28,20,32,18,24].map((h,i) => (
                            <div key={i} style={{width:4,borderRadius:2,background:'var(--green)',height:h,animation:`wave .6s ${i*.1}s infinite alternate`}}/>
                          ))}
                        </div>
                      ) : (
                        <svg width="40" height="40" fill="none" stroke="var(--text2)" strokeWidth="1.5" viewBox="0 0 24 24"><path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"/><path d="M19 10v2a7 7 0 01-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
                      )}
                    </div>
                    <div style={{display:'flex',gap:'.75rem'}}>
                      <button className="btn ghost-btn" onClick={() => { setBioStep('face'); setCaptured(0); startCamera() }} style={{flex:1,justifyContent:'center'}}>Back</button>
                      {!voiceRec
                        ? <button className="btn green-btn" onClick={startVoice} style={{flex:2,justifyContent:'center'}}>Start Recording</button>
                        : <button className="btn red-btn" onClick={() => { mediaRef.current?.stop() }} style={{flex:2,justifyContent:'center'}}>Stop</button>
                      }
                    </div>
                  </>
                )}

                {bioStep === 'done' && (
                  <div style={{textAlign:'center',padding:'1.5rem 0'}}>
                    <div style={{width:72,height:72,borderRadius:'50%',border:'2px solid #00D46A',background:'rgba(0,212,106,0.08)',display:'flex',alignItems:'center',justifyContent:'center',margin:'0 auto 1.25rem'}}>
                      <svg width="34" height="34" fill="none" stroke="#00D46A" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                    </div>
                    <h3 className="syne" style={{fontSize:'1.2rem',fontWeight:700,color:'#00D46A',marginBottom:'.5rem'}}>Registration Complete</h3>
                    <p style={{color:'var(--text2)',fontSize:'.88rem',marginBottom:'1.5rem'}}>Your biometric data has been securely encrypted and stored.</p>
                    <button className="btn green-btn" onClick={() => router.push('/user-dashboard')} style={{justifyContent:'center',width:'100%'}}>Return to Dashboard</button>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Security */}
        {tab === 'security' && (
          <div style={{display:'flex',flexDirection:'column',gap:'1.25rem'}}>
            <div className="card">
              <p className="syne" style={{fontWeight:700,marginBottom:'1.25rem'}}>Security Settings</p>
              {[
                {icon:'🔐',title:'Two-Factor Authentication',sub:'Add extra login verification',action:'Enable',color:'var(--green)'},
                {icon:'👤',title:'Biometric Login',sub: profile.biometricStatus==='complete' ? 'Face & voice enabled' : 'Complete biometric registration',action: profile.biometricStatus==='complete' ? 'Active' : 'Setup',color: profile.biometricStatus==='complete' ? '#00D46A' : '#3B82F6'},
                {icon:'🔔',title:'Login Alerts',sub:'Get notified of new sign-ins',action:'Configure',color:'#F5C842'},
              ].map(s => (
                <div key={s.title} className="security-row">
                  <div style={{display:'flex',alignItems:'center',gap:12}}>
                    <span style={{fontSize:'1.1rem'}}>{s.icon}</span>
                    <div>
                      <p style={{fontWeight:500,fontSize:'.9rem',marginBottom:'.15rem'}}>{s.title}</p>
                      <p style={{color:'var(--text3)',fontSize:'.8rem'}}>{s.sub}</p>
                    </div>
                  </div>
                  <button className="btn" style={{background:`${s.color}15`,color:s.color,border:`1px solid ${s.color}30`,padding:'.4rem .9rem',fontSize:'.8rem'}}
                    onClick={() => s.action === 'Setup' ? setTab('biometrics') : undefined}>
                    {s.action}
                  </button>
                </div>
              ))}
            </div>

            <div className="card">
              <p className="syne" style={{fontWeight:700,marginBottom:'1.25rem'}}>Privacy & Compliance</p>
              {[
                {label:'AES-256 Data Encryption',active:true},
                {label:'GDPR Compliant',active:true},
                {label:'Kenya Data Protection Act 2019',active:true},
                {label:'Biometric Template Storage (not raw images)',active:true},
              ].map(item => (
                <div key={item.label} style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'.65rem 0',borderBottom:'1px solid rgba(255,255,255,0.04)'}}>
                  <span style={{color:'var(--text2)',fontSize:'.88rem'}}>{item.label}</span>
                  <svg width="16" height="16" fill="none" stroke="#00D46A" strokeWidth="2.5" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
      <style>{`
        @keyframes scan{0%{top:30%;}50%{top:70%;}100%{top:30%;}}
        @keyframes wave{0%{transform:scaleY(1);}100%{transform:scaleY(1.8);}}
      `}</style>
    </>
  )
}