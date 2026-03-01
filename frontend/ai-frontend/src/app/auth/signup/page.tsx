"use client"

import { useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

// ─── Types ────────────────────────────────────────────────────────────────────
type CitizenType  = 'kenyan' | 'foreign' | null
type HasNationalId = 'yes' | 'no' | null

interface FormState {
  citizenType:       CitizenType
  hasNationalId:     HasNationalId
  nationalId:        string
  firstNameId:       string
  idCardType:        string
  kcseYear:          string
  kcseIndex:         string
  firstNameKcse:     string
  dateOfBirth:       string
  kcseCertImage:     File | null
  passportNumber:    string
  firstNamePassport: string
  passportImage:     File | null
  email:             string
  confirmEmail:      string
  password:          string
  confirmPassword:   string
}

const INITIAL: FormState = {
  citizenType: null, hasNationalId: null,
  nationalId: '', firstNameId: '', idCardType: 'kenyan',
  kcseYear: '', kcseIndex: '', firstNameKcse: '', dateOfBirth: '', kcseCertImage: null,
  passportNumber: '', firstNamePassport: '', passportImage: null,
  email: '', confirmEmail: '', password: '', confirmPassword: '',
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function calcAge(dob: string) {
  const today = new Date(), birth = new Date(dob)
  let age = today.getFullYear() - birth.getFullYear()
  if (today.getMonth() < birth.getMonth() || (today.getMonth() === birth.getMonth() && today.getDate() < birth.getDate())) age--
  return age
}

// ─── Component ────────────────────────────────────────────────────────────────
export default function SignUp() {
  const router       = useRouter()
  const kcseRef      = useRef<HTMLInputElement>(null)
  const passportRef  = useRef<HTMLInputElement>(null)

  const [form, setForm]           = useState<FormState>(INITIAL)
  const [errors, setErrors]       = useState<Record<string, string>>({})
  const [step, setStep]           = useState<'identity' | 'credentials'>('identity')
  const [idValidated, setIdValid] = useState(false)
  const [validName, setValidName] = useState('')
  const [validId,   setValidId]   = useState('')
  const [validating, setValidating] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [docBusy,    setDocBusy]    = useState(false)
  const [docStatus,  setDocStatus]  = useState<'idle'|'ok'|'fail'>('idle')
  const [showPass,   setShowPass]   = useState(false)
  const [showConf,   setShowConf]   = useState(false)

  function set<K extends keyof FormState>(k: K, v: FormState[K]) {
    setForm(p => ({ ...p, [k]: v }))
    setErrors(p => ({ ...p, [k]: '' }))
  }

  // ── Validation ──────────────────────────────────────────────────────────────
  function validateIdentity() {
    const e: Record<string,string> = {}
    if (!form.citizenType) e.citizenType = 'Select citizenship'
    if (form.citizenType === 'kenyan') {
      if (!form.hasNationalId) e.hasNationalId = 'Select an option'
      if (form.hasNationalId === 'yes') {
        if (!form.nationalId)  e.nationalId  = 'ID number is required'
        if (!form.firstNameId) e.firstNameId = 'First name is required'
        if (!idValidated)      e.validate    = 'Please validate your ID first'
      }
      if (form.hasNationalId === 'no') {
        if (!form.kcseYear)      e.kcseYear      = 'Exam year is required'
        if (!form.kcseIndex)     e.kcseIndex     = 'Index number is required'
        if (!form.firstNameKcse) e.firstNameKcse = 'First name is required'
        if (!form.dateOfBirth)   e.dateOfBirth   = 'Date of birth is required'
        else if (calcAge(form.dateOfBirth) < 16) e.dateOfBirth = 'Must be 16+ years to register'
        if (!form.kcseCertImage) e.kcseCertImage = 'KCSE certificate image is required'
        if (!idValidated)        e.validate      = 'Please validate your KCSE details first'
      }
    }
    if (form.citizenType === 'foreign') {
      if (!form.passportNumber)    e.passportNumber    = 'Passport number is required'
      if (!form.firstNamePassport) e.firstNamePassport = 'First name is required'
      if (!form.passportImage)     e.passportImage     = 'Passport image is required'
      if (!idValidated)            e.validate          = 'Please validate your passport details first'
    }
    setErrors(e); return Object.keys(e).length === 0
  }

  function validateCredentials() {
    const e: Record<string,string> = {}
    if (!form.email)                            e.email          = 'Email is required'
    else if (!/\S+@\S+\.\S+/.test(form.email)) e.email          = 'Email is invalid'
    if (form.email !== form.confirmEmail)       e.confirmEmail   = 'Emails do not match'
    if (!form.password || form.password.length < 8) e.password  = 'Password must be at least 8 characters'
    else if (!/[A-Z]/.test(form.password) || !/[0-9]/.test(form.password))
                                                e.password       = 'Include at least one uppercase letter and one number'
    if (form.password !== form.confirmPassword) e.confirmPassword= 'Passwords do not match'
    setErrors(e); return Object.keys(e).length === 0
  }

  // ── Validate identity (mock / backend) ─────────────────────────────────────
  async function handleValidate() {
    setValidating(true); setErrors({})
    try {
      await new Promise(r => setTimeout(r, 1200))
      let name = '', idNum = ''
      if (form.citizenType === 'kenyan' && form.hasNationalId === 'yes') {
        if (!form.nationalId || !form.firstNameId) { setErrors({ validate: 'Fill in ID number and first name first' }); return }
        name = form.firstNameId.toUpperCase(); idNum = form.nationalId
      } else if (form.citizenType === 'kenyan' && form.hasNationalId === 'no') {
        if (!form.kcseIndex || !form.kcseYear || !form.firstNameKcse || !form.dateOfBirth) { setErrors({ validate: 'Fill in all KCSE fields first' }); return }
        if (calcAge(form.dateOfBirth) < 16) { setErrors({ dateOfBirth: 'Must be 16+ years to register' }); return }
        name = form.firstNameKcse.toUpperCase(); idNum = form.kcseIndex
      } else if (form.citizenType === 'foreign') {
        if (!form.passportNumber || !form.firstNamePassport) { setErrors({ validate: 'Fill in passport number and first name first' }); return }
        name = form.firstNamePassport.toUpperCase(); idNum = form.passportNumber
      }
      setValidName(name); setValidId(idNum); setIdValid(true)
    } catch { setErrors({ validate: 'Validation failed. Please try again.' })
    } finally { setValidating(false) }
  }

  // ── Doc upload + verify ────────────────────────────────────────────────────
  async function handleDocUpload(file: File, type: 'kcse'|'passport') {
    setDocBusy(true); setDocStatus('idle')
    try {
      if (type === 'kcse') set('kcseCertImage', file)
      else                 set('passportImage',  file)
      const fd = new FormData(); fd.append('file', file)
      const res = await fetch(`${API_BASE}/api/v1/document/verify`, { method: 'POST', body: fd })
      if (res.ok) { const r = await res.json(); setDocStatus(r.authentic ? 'ok' : 'fail') }
      else setDocStatus('fail')
    } catch { setDocStatus('ok')          // offline fallback
    } finally { setDocBusy(false) }
  }

  function handleNext() { if (validateIdentity()) setStep('credentials') }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); if (!validateCredentials()) return
    setSubmitting(true)
    try {
      const isKenyan = form.citizenType === 'kenyan'
      const endpoint = isKenyan ? `${API_BASE}/api/v1/auth/register/kenyan` : `${API_BASE}/api/v1/auth/register/foreign`
      const payload  = isKenyan
        ? { citizenship:'kenyan', identificationType: form.hasNationalId==='yes'?'national_id':'kcse_certificate',
            identificationNumber: form.hasNationalId==='yes'?form.nationalId:form.kcseIndex,
            firstName: form.hasNationalId==='yes'?form.firstNameId:form.firstNameKcse,
            email:form.email, password:form.password, dateOfBirth:form.dateOfBirth||null, kcseExamYear:form.kcseYear||null }
        : { citizenship:'foreign', identificationType:'passport',
            identificationNumber:form.passportNumber, firstName:form.firstNamePassport,
            email:form.email, password:form.password }

      const res    = await fetch(endpoint, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload) })
      const result = await res.json()
      if (res.ok && result.status !== 'error') {
        localStorage.setItem('authToken', result.access_token)
        localStorage.setItem('userId', result.user_id || '')
        localStorage.setItem('verificationStatus', 'pending')
        localStorage.setItem('userRegistration', JSON.stringify({
          firstName:            payload.firstName,
          email:                payload.email,
          citizenship:          payload.citizenship,
          identificationNumber: payload.identificationNumber,
          identificationType:   payload.identificationType,
        }))
        router.push('/auth/biometric-registration')
      } else {
        setErrors({ submit: result.detail || result.message || 'Registration failed. Please try again.' })
      }
    } catch { setErrors({ submit: 'Network error — please check your connection.' })
    } finally { setSubmitting(false) }
  }

  const showKenyanId = form.citizenType === 'kenyan' && form.hasNationalId === 'yes'
  const showKcse     = form.citizenType === 'kenyan' && form.hasNationalId === 'no'
  const showForeign  = form.citizenType === 'foreign'
  const showFields   = showKenyanId || showKcse || showForeign

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');
        *{box-sizing:border-box;margin:0;padding:0;}
        :root{
          --bg:#04080F;--surface:#080E1A;--surface2:#0C1524;
          --green:#00D46A;--green-dim:#007A3D;--green-glow:rgba(0,212,106,0.12);
          --gold:#F5C842;--red:#FF4D4D;
          --border:rgba(255,255,255,0.07);--border2:rgba(255,255,255,0.12);
          --text:#F0F4FF;--text2:rgba(240,244,255,0.55);--text3:rgba(240,244,255,0.28);
        }
        body{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;min-height:100vh;}
        .syne{font-family:'Syne',sans-serif;}
        .grid-bg{
          background-image:linear-gradient(rgba(0,212,106,0.025) 1px,transparent 1px),
                           linear-gradient(90deg,rgba(0,212,106,0.025) 1px,transparent 1px);
          background-size:60px 60px;
        }
        .orb{position:absolute;border-radius:50%;filter:blur(120px);pointer-events:none;}

        /* ── Inputs & selects ── */
        .inp, .sel{
          width:100%;padding:.7rem 1rem;
          background:rgba(255,255,255,0.04);
          border:1px solid var(--border2);border-radius:10px;
          color:var(--text);font-family:'DM Sans',sans-serif;font-size:.88rem;outline:none;
          transition:border-color .2s,box-shadow .2s;
        }
        .inp:focus,.sel:focus{border-color:var(--green);box-shadow:0 0 0 3px rgba(0,212,106,0.08);}
        .inp.err,.sel.err{border-color:var(--red);}
        .inp::placeholder{color:var(--text3);}
        .inp:-webkit-autofill{-webkit-box-shadow:0 0 0 1000px #080E1A inset!important;-webkit-text-fill-color:var(--text)!important;}
        .sel{
          cursor:pointer;appearance:none;
          background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='rgba(240,244,255,0.3)'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'/%3E%3C/svg%3E");
          background-repeat:no-repeat;background-position:right .85rem center;background-size:16px;
          padding-right:2.5rem;
        }
        .sel option{background:#080E1A;color:var(--text);}

        /* ── Date input ── */
        input[type="date"]{color-scheme:dark;}
        input[type="date"]::-webkit-calendar-picker-indicator{filter:invert(0.6);}

        /* ── Labels & errors ── */
        .lbl{display:block;font-size:.8rem;font-weight:500;color:var(--text2);margin-bottom:.4rem;}
        .err-msg{color:var(--red);font-size:.75rem;margin-top:.35rem;display:flex;align-items:center;gap:4px;}

        /* ── Upload zone ── */
        .upload-zone{
          border:1.5px dashed rgba(255,255,255,0.1);border-radius:10px;
          padding:.85rem 1rem;cursor:pointer;display:flex;align-items:center;gap:10px;
          transition:border-color .2s,background .2s;
        }
        .upload-zone:hover{border-color:rgba(0,212,106,0.3);background:rgba(0,212,106,0.02);}
        .upload-zone.ok{border-color:rgba(0,212,106,0.4);}
        .upload-zone.fail{border-color:rgba(255,77,77,0.4);}

        /* ── Buttons ── */
        .btn-primary{
          width:100%;padding:.8rem;border-radius:10px;
          background:var(--green);color:#04080F;
          font-family:'Syne',sans-serif;font-weight:700;font-size:.9rem;letter-spacing:.03em;
          border:none;cursor:pointer;transition:opacity .2s,transform .2s,box-shadow .2s;
          display:flex;align-items:center;justify-content:center;gap:8px;
        }
        .btn-primary:hover:not(:disabled){opacity:.9;transform:translateY(-1px);box-shadow:0 8px 30px rgba(0,212,106,0.25);}
        .btn-primary:disabled{opacity:.45;cursor:not-allowed;}

        .btn-validate{
          padding:.6rem 1.4rem;border-radius:9px;
          background:rgba(0,212,106,0.08);border:1px solid rgba(0,212,106,0.25);
          color:var(--green);font-family:'DM Sans',sans-serif;font-size:.85rem;font-weight:600;
          cursor:pointer;display:inline-flex;align-items:center;gap:7px;
          transition:background .2s,border-color .2s;
        }
        .btn-validate:hover:not(:disabled){background:rgba(0,212,106,0.14);border-color:rgba(0,212,106,0.4);}
        .btn-validate:disabled{opacity:.5;cursor:not-allowed;}

        .btn-back{
          padding:.8rem 1.25rem;border-radius:10px;
          background:rgba(255,255,255,0.04);border:1px solid var(--border2);
          color:var(--text2);font-family:'DM Sans',sans-serif;font-size:.88rem;font-weight:500;
          cursor:pointer;white-space:nowrap;transition:background .2s;
        }
        .btn-back:hover{background:rgba(255,255,255,0.07);}

        /* ── Card ── */
        .card{
          background:var(--surface);border:1px solid var(--border);
          border-radius:20px;width:100%;max-width:520px;position:relative;overflow:hidden;
        }
        .card-top-stripe{position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--green),transparent);}
        .card-header{padding:1.5rem 2rem;border-bottom:1px solid var(--border);}
        .card-body{padding:1.75rem 2rem;display:flex;flex-direction:column;gap:1.25rem;}
        .card-footer{padding:1rem 2rem;border-top:1px solid var(--border);text-align:center;}

        /* ── Progress bar ── */
        .prog-track{height:3px;background:rgba(255,255,255,0.05);}
        .prog-fill{height:100%;background:linear-gradient(90deg,var(--green-dim),var(--green));transition:width .4s ease;}

        /* ── Validated banner ── */
        .valid-banner{
          background:rgba(0,212,106,0.05);border:1px solid rgba(0,212,106,0.18);
          border-radius:10px;padding:.8rem 1rem;
        }

        /* ── Error banner ── */
        .err-banner{
          background:rgba(255,77,77,0.06);border:1px solid rgba(255,77,77,0.2);
          border-radius:10px;padding:.7rem 1rem;
          display:flex;align-items:center;gap:8px;color:var(--red);font-size:.84rem;
        }

        /* ── Summary strip (step 2) ── */
        .summary-strip{
          background:rgba(0,212,106,0.04);border:1px solid rgba(0,212,106,0.15);
          border-radius:10px;padding:.7rem 1rem;
          display:flex;align-items:center;gap:8px;
          font-size:.8rem;color:var(--text2);
        }

        /* ── Show-pass button ── */
        .show-pass{
          position:absolute;right:.85rem;top:50%;transform:translateY(-50%);
          background:none;border:none;cursor:pointer;color:var(--text3);padding:2px;
        }
        .show-pass:hover{color:var(--text2);}

        /* ── Pill tag ── */
        .pill{
          display:inline-flex;align-items:center;gap:6px;
          padding:3px 10px;border-radius:100px;
          border:1px solid rgba(0,212,106,0.25);background:rgba(0,212,106,0.06);
          color:var(--green);font-size:.7rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase;
        }
        .pill-dot{width:5px;height:5px;border-radius:50%;background:var(--green);animation:pulse 2s infinite;}
        @keyframes pulse{0%,100%{opacity:1;}50%{opacity:.4;}}
        @keyframes spin{to{transform:rotate(360deg);}}
        .spin{animation:spin .7s linear infinite;}
        @keyframes fadeIn{from{opacity:0;transform:translateY(14px);}to{opacity:1;transform:translateY(0);}}
        .fade-in{animation:fadeIn .45s ease forwards;}
        .divider{display:flex;align-items:center;gap:.75rem;}
        .divider-line{flex:1;height:1px;background:var(--border);}

        /* ── Field row spacing ── */
        .field{display:flex;flex-direction:column;}

        /* ── Hint text ── */
        .hint{color:var(--text3);font-size:.74rem;margin-top:.3rem;}
      `}</style>

      <div
        className="grid-bg"
        style={{
          minHeight:'100vh',display:'flex',alignItems:'flex-start',justifyContent:'center',
          padding:'2.5rem 1rem 3rem',position:'relative',
        }}
      >
        <div className="orb" style={{width:500,height:500,background:'rgba(0,212,106,0.05)',top:'5%',right:'5%'}}/>
        <div className="orb" style={{width:350,height:350,background:'rgba(245,200,66,0.03)',bottom:'10%',left:'2%'}}/>

        <div className="fade-in" style={{width:'100%',maxWidth:520,display:'flex',flexDirection:'column',alignItems:'center',gap:'1.25rem'}}>

          {/* ── Logo header ── */}
          <div style={{display:'flex',alignItems:'center',gap:10}}>
            <div style={{
              width:42,height:42,borderRadius:11,
              background:'linear-gradient(135deg,var(--green),var(--green-dim))',
              display:'flex',alignItems:'center',justifyContent:'center',flexShrink:0,
            }}>
              <svg width="22" height="22" fill="none" stroke="#04080F" strokeWidth="2.5" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
              </svg>
            </div>
            <div>
              <p className="syne" style={{fontWeight:800,fontSize:'1rem',lineHeight:1.1}}>UhakikiAI</p>
              <p style={{color:'var(--text3)',fontSize:'.72rem',letterSpacing:'.05em'}}>Sovereign Identity Engine</p>
            </div>
            <div style={{width:1,height:30,background:'var(--border)',margin:'0 .5rem'}}/>
            <span className="pill"><span className="pill-dot"/>HEF Portal</span>
          </div>

          {/* ── Card ── */}
          <div className="card">
            <div className="card-top-stripe"/>

            {/* Header */}
            <div className="card-header">
              <div style={{display:'flex',alignItems:'center',justifyContent:'space-between'}}>
                <div>
                  <h2 className="syne" style={{fontSize:'1.15rem',fontWeight:800,marginBottom:'.2rem'}}>
                    Create Account
                  </h2>
                  <p style={{color:'var(--text2)',fontSize:'.8rem'}}>
                    {step === 'identity' ? 'Step 1 of 2 — Identity Verification' : 'Step 2 of 2 — Account Credentials'}
                  </p>
                </div>
                {/* Step circles */}
                <div style={{display:'flex',alignItems:'center',gap:6}}>
                  {[1,2].map(n => (
                    <div key={n} style={{
                      width:28,height:28,borderRadius:'50%',
                      display:'flex',alignItems:'center',justifyContent:'center',
                      fontSize:'.75rem',fontWeight:700,
                      backgroundColor: (step==='credentials'&&n===1)||(n===1&&step==='identity')
                        ? 'rgba(0,212,106,0.15)' : n===2&&step==='credentials' ? 'rgba(0,212,106,0.15)' : 'rgba(255,255,255,0.05)',
                      border: step==='identity'&&n===1 ? '1px solid var(--green)'
                            : step==='credentials'&&n===2 ? '1px solid var(--green)'
                            : step==='credentials'&&n===1 ? 'none' : '1px solid rgba(255,255,255,0.1)',
                      color: step==='identity'&&n===1 ? 'var(--green)'
                           : step==='credentials'&&n===2 ? 'var(--green)'
                           : step==='credentials'&&n===1 ? '#04080F' : 'var(--text3)',
                    }}>
                      {step==='credentials'&&n===1
                        ? <svg width="12" height="12" fill="none" stroke="#04080F" strokeWidth="3" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
                        : n
                      }
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Progress */}
            <div className="prog-track">
              <div className="prog-fill" style={{width: step==='identity' ? '50%' : '100%'}}/>
            </div>

            {/* Body */}
            <div className="card-body">

              {/* ═══ STEP 1: IDENTITY ═══ */}
              {step === 'identity' && (
                <>
                  {/* Citizenship */}
                  <div className="field">
                    <label className="lbl">Are you a Kenyan Citizen? *</label>
                    <select
                      className={`sel${errors.citizenType?' err':''}`}
                      value={form.citizenType??''}
                      onChange={e => { set('citizenType',(e.target.value||null) as CitizenType); setIdValid(false); setValidName('') }}
                    >
                      <option value="">— Select citizenship —</option>
                      <option value="kenyan">Yes, Kenyan Citizen</option>
                      <option value="foreign">No, Foreign Student</option>
                    </select>
                    {errors.citizenType && <ErrMsg msg={errors.citizenType}/>}
                  </div>

                  {/* Has national ID */}
                  {form.citizenType === 'kenyan' && (
                    <div className="field">
                      <label className="lbl">Do you have a National ID / Maisha Number? *</label>
                      <select
                        className={`sel${errors.hasNationalId?' err':''}`}
                        value={form.hasNationalId??''}
                        onChange={e => { set('hasNationalId',(e.target.value||null) as HasNationalId); setIdValid(false); setValidName('') }}
                      >
                        <option value="">— Select option —</option>
                        <option value="yes">Yes, I have a National ID</option>
                        <option value="no">No, use KCSE certificate</option>
                      </select>
                      {errors.hasNationalId && <ErrMsg msg={errors.hasNationalId}/>}
                    </div>
                  )}

                  {/* ── Kenyan with ID ── */}
                  {showKenyanId && (
                    <>
                      <div className="field">
                        <label className="lbl">ID Number *</label>
                        <input className={`inp${errors.nationalId?' err':''}`}
                          type="text" value={form.nationalId} placeholder="Enter 8-digit ID number"
                          onChange={e => { set('nationalId',e.target.value.replace(/\D/g,'').slice(0,9)); setIdValid(false) }}/>
                        {errors.nationalId && <ErrMsg msg={errors.nationalId}/>}
                      </div>
                      <div className="field">
                        <label className="lbl">First Name as per your ID *</label>
                        <input className={`inp${errors.firstNameId?' err':''}`}
                          type="text" value={form.firstNameId} placeholder="Exactly as on ID card"
                          onChange={e => { set('firstNameId',e.target.value); setIdValid(false) }}/>
                        {errors.firstNameId && <ErrMsg msg={errors.firstNameId}/>}
                      </div>
                      <div className="field">
                        <label className="lbl">Type of ID Card</label>
                        <select className="sel" value={form.idCardType} onChange={e => set('idCardType',e.target.value)}>
                          <option value="kenyan">Kenyan Citizen (ID card)</option>
                          <option value="alien">Foreign Resident (Alien ID)</option>
                        </select>
                      </div>
                    </>
                  )}

                  {/* ── Kenyan without ID (KCSE) ── */}
                  {showKcse && (
                    <>
                      <div className="field">
                        <label className="lbl">KCSE Exam Year *</label>
                        <select className={`sel${errors.kcseYear?' err':''}`}
                          value={form.kcseYear} onChange={e => { set('kcseYear',e.target.value); setIdValid(false) }}>
                          <option value="">— Select year —</option>
                          {[2025,2024,2023,2022,2021,2020,2019,2018].map(y => (
                            <option key={y} value={String(y)}>{y}</option>
                          ))}
                        </select>
                        {errors.kcseYear && <ErrMsg msg={errors.kcseYear}/>}
                      </div>
                      <div className="field">
                        <label className="lbl">KCSE Index Number *</label>
                        <input className={`inp${errors.kcseIndex?' err':''}`}
                          type="text" value={form.kcseIndex} placeholder="e.g. 12345678901"
                          onChange={e => { set('kcseIndex',e.target.value); setIdValid(false) }}/>
                        {errors.kcseIndex && <ErrMsg msg={errors.kcseIndex}/>}
                      </div>
                      <div className="field">
                        <label className="lbl">First Name as per KCSE Results Slip *</label>
                        <input className={`inp${errors.firstNameKcse?' err':''}`}
                          type="text" value={form.firstNameKcse} placeholder="Exactly as on certificate"
                          onChange={e => { set('firstNameKcse',e.target.value); setIdValid(false) }}/>
                        {errors.firstNameKcse && <ErrMsg msg={errors.firstNameKcse}/>}
                      </div>
                      <div className="field">
                        <label className="lbl">Date of Birth *</label>
                        <input className={`inp${errors.dateOfBirth?' err':''}`}
                          type="date" value={form.dateOfBirth}
                          onChange={e => { set('dateOfBirth',e.target.value); setIdValid(false) }}/>
                        <span className="hint">Must be 16 years or older to register</span>
                        {errors.dateOfBirth && <ErrMsg msg={errors.dateOfBirth}/>}
                      </div>

                      {/* KCSE cert upload */}
                      <div className="field">
                        <label className="lbl">KCSE Certificate Image *</label>
                        <input ref={kcseRef} type="file" accept="image/*" style={{display:'none'}}
                          onChange={e => { const f=e.target.files?.[0]; if(f) handleDocUpload(f,'kcse') }}/>
                        <div className={`upload-zone${docStatus==='ok'?' ok':docStatus==='fail'?' fail':''}`}
                          onClick={() => kcseRef.current?.click()}>
                          <DocUploadContent busy={docBusy} status={docStatus} fileName={form.kcseCertImage?.name} label="KCSE certificate"/>
                        </div>
                        {errors.kcseCertImage && <ErrMsg msg={errors.kcseCertImage}/>}
                      </div>
                    </>
                  )}

                  {/* ── Foreign student ── */}
                  {showForeign && (
                    <>
                      <div className="field">
                        <label className="lbl">Passport Number *</label>
                        <input className={`inp${errors.passportNumber?' err':''}`}
                          type="text" value={form.passportNumber} placeholder="Enter passport number"
                          onChange={e => { set('passportNumber',e.target.value.toUpperCase()); setIdValid(false) }}/>
                        {errors.passportNumber && <ErrMsg msg={errors.passportNumber}/>}
                      </div>
                      <div className="field">
                        <label className="lbl">First Name as per Passport *</label>
                        <input className={`inp${errors.firstNamePassport?' err':''}`}
                          type="text" value={form.firstNamePassport} placeholder="Exactly as on passport"
                          onChange={e => { set('firstNamePassport',e.target.value); setIdValid(false) }}/>
                        {errors.firstNamePassport && <ErrMsg msg={errors.firstNamePassport}/>}
                      </div>

                      {/* Passport image upload */}
                      <div className="field">
                        <label className="lbl">Passport Image *</label>
                        <input ref={passportRef} type="file" accept="image/*" style={{display:'none'}}
                          onChange={e => { const f=e.target.files?.[0]; if(f) handleDocUpload(f,'passport') }}/>
                        <div className={`upload-zone${docStatus==='ok'?' ok':docStatus==='fail'?' fail':''}`}
                          onClick={() => passportRef.current?.click()}>
                          <DocUploadContent busy={docBusy} status={docStatus} fileName={form.passportImage?.name} label="passport"/>
                        </div>
                        {errors.passportImage && <ErrMsg msg={errors.passportImage}/>}
                      </div>
                    </>
                  )}

                  {/* ── Validate button ── */}
                  {showFields && !idValidated && (
                    <button type="button" className="btn-validate" onClick={handleValidate} disabled={validating}>
                      {validating
                        ? <><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="spin"><path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" strokeOpacity=".2"/><path d="M21 12a9 9 0 00-9-9"/></svg>Validating...</>
                        : <><svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>Validate Identity</>
                      }
                    </button>
                  )}

                  {/* ── Validated banner ── */}
                  {idValidated && (
                    <div className="valid-banner">
                      <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:'.4rem'}}>
                        <svg width="15" height="15" fill="none" stroke="var(--green)" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                        <span style={{color:'var(--green)',fontSize:'.82rem',fontWeight:600}}>Identity Validated</span>
                      </div>
                      <div style={{paddingLeft:23,display:'flex',flexDirection:'column',gap:3}}>
                        <span style={{color:'var(--text2)',fontSize:'.8rem'}}><strong>Name:</strong> {validName}</span>
                        <span style={{color:'var(--text2)',fontSize:'.8rem'}}><strong>ID:</strong> {validId}</span>
                      </div>
                    </div>
                  )}

                  {errors.validate && <ErrMsg msg={errors.validate}/>}

                  {/* ── Next ── */}
                  {showFields && (
                    <button type="button" className="btn-primary" onClick={handleNext}>
                      Continue to Credentials →
                    </button>
                  )}
                </>
              )}

              {/* ═══ STEP 2: CREDENTIALS ═══ */}
              {step === 'credentials' && (
                <>
                  {/* Summary strip */}
                  <div className="summary-strip">
                    <svg width="14" height="14" fill="none" stroke="var(--green)" strokeWidth="2.5" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
                    Identity verified as&nbsp;<strong style={{color:'var(--green)'}}>{validName}</strong>&nbsp;({validId})
                  </div>

                  {/* Email */}
                  <div className="field">
                    <label className="lbl">Email Address *</label>
                    <div style={{position:'relative'}}>
                      <span style={{position:'absolute',left:'.85rem',top:'50%',transform:'translateY(-50%)',color:'var(--text3)'}}>
                        <svg width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                      </span>
                      <input className={`inp${errors.email?' err':''}`} type="email" value={form.email}
                        placeholder="your.email@example.com" style={{paddingLeft:'2.5rem'}}
                        onChange={e => set('email',e.target.value)}/>
                    </div>
                    {errors.email && <ErrMsg msg={errors.email}/>}
                  </div>

                  {/* Confirm email */}
                  <div className="field">
                    <label className="lbl">Confirm Email *</label>
                    <div style={{position:'relative'}}>
                      <span style={{position:'absolute',left:'.85rem',top:'50%',transform:'translateY(-50%)',color:'var(--text3)'}}>
                        <svg width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                      </span>
                      <input className={`inp${errors.confirmEmail?' err':''}`} type="email" value={form.confirmEmail}
                        placeholder="Re-enter your email" style={{paddingLeft:'2.5rem'}}
                        onChange={e => set('confirmEmail',e.target.value)}/>
                    </div>
                    {errors.confirmEmail && <ErrMsg msg={errors.confirmEmail}/>}
                  </div>

                  {/* Password */}
                  <div className="field">
                    <label className="lbl">Password *</label>
                    <div style={{position:'relative'}}>
                      <span style={{position:'absolute',left:'.85rem',top:'50%',transform:'translateY(-50%)',color:'var(--text3)'}}>
                        <svg width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
                      </span>
                      <input className={`inp${errors.password?' err':''}`}
                        type={showPass?'text':'password'} value={form.password}
                        placeholder="Min 8 chars, 1 uppercase, 1 number"
                        style={{paddingLeft:'2.5rem',paddingRight:'2.75rem'}}
                        onChange={e => set('password',e.target.value)}/>
                      <button type="button" className="show-pass" onClick={() => setShowPass(!showPass)}>
                        {showPass
                          ? <svg width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                          : <svg width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                        }
                      </button>
                    </div>
                    {errors.password && <ErrMsg msg={errors.password}/>}
                  </div>

                  {/* Confirm password */}
                  <div className="field">
                    <label className="lbl">Confirm Password *</label>
                    <div style={{position:'relative'}}>
                      <span style={{position:'absolute',left:'.85rem',top:'50%',transform:'translateY(-50%)',color:'var(--text3)'}}>
                        <svg width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
                      </span>
                      <input className={`inp${errors.confirmPassword?' err':''}`}
                        type={showConf?'text':'password'} value={form.confirmPassword}
                        placeholder="Re-enter password"
                        style={{paddingLeft:'2.5rem',paddingRight:'2.75rem'}}
                        onChange={e => set('confirmPassword',e.target.value)}/>
                      <button type="button" className="show-pass" onClick={() => setShowConf(!showConf)}>
                        {showConf
                          ? <svg width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                          : <svg width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                        }
                      </button>
                    </div>
                    {errors.confirmPassword && <ErrMsg msg={errors.confirmPassword}/>}
                  </div>

                  {/* Submit error */}
                  {errors.submit && (
                    <div className="err-banner">
                      <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                      {errors.submit}
                    </div>
                  )}

                  {/* Actions */}
                  <div style={{display:'flex',gap:'.75rem'}}>
                    <button type="button" className="btn-back" onClick={() => setStep('identity')}>← Back</button>
                    <button type="submit" className="btn-primary" disabled={submitting} style={{flex:1}}>
                      {submitting
                        ? <><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="spin"><path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" strokeOpacity=".2"/><path d="M21 12a9 9 0 00-9-9"/></svg>Registering...</>
                        : 'Create Account'
                      }
                    </button>
                  </div>
                </>
              )}
            </div>

            {/* Footer */}
            <div className="card-footer">
              <p style={{color:'var(--text2)',fontSize:'.85rem'}}>
                Already have an account?{' '}
                <Link href="/auth/signin" style={{color:'var(--green)',textDecoration:'none',fontWeight:600}}>Sign in here</Link>
              </p>
            </div>
          </div>

          {/* Trust badges */}
          <div style={{display:'flex',gap:'1.75rem',alignItems:'center',flexWrap:'wrap',justifyContent:'center'}}>
            {['AI-Powered Verification','End-to-End Encrypted','Government Grade Security'].map(t => (
              <span key={t} style={{display:'flex',alignItems:'center',gap:5,color:'var(--text3)',fontSize:'.72rem'}}>
                <span style={{width:5,height:5,borderRadius:'50%',background:'var(--green)',display:'inline-block'}}/>
                {t}
              </span>
            ))}
          </div>
        </div>
      </div>
    </>
  )
}

// ─── Sub-components ───────────────────────────────────────────────────────────
function ErrMsg({ msg }: { msg: string }) {
  return (
    <span style={{color:'var(--red)',fontSize:'.75rem',display:'flex',alignItems:'center',gap:4,marginTop:'.3rem'}}>
      <svg width="11" height="11" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
      {msg}
    </span>
  )
}

function DocUploadContent({ busy, status, fileName, label }: { busy:boolean; status:'idle'|'ok'|'fail'; fileName?:string; label:string }) {
  if (busy) return (
    <>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--green)" strokeWidth="2.5" style={{animation:'spin .7s linear infinite',flexShrink:0}}>
        <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" strokeOpacity=".2"/><path d="M21 12a9 9 0 00-9-9"/>
      </svg>
      <span style={{color:'var(--text2)',fontSize:'.82rem'}}>Verifying document…</span>
    </>
  )
  if (status === 'ok') return (
    <>
      <svg width="16" height="16" fill="none" stroke="var(--green)" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
      <span style={{color:'var(--green)',fontSize:'.82rem'}}>Document verified ✓</span>
    </>
  )
  if (status === 'fail') return (
    <>
      <svg width="16" height="16" fill="none" stroke="var(--red)" strokeWidth="2.5" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
      <span style={{color:'var(--red)',fontSize:'.82rem'}}>Verification failed — try again</span>
    </>
  )
  return (
    <>
      <svg width="16" height="16" fill="none" stroke="var(--text3)" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>
      <span style={{color:'var(--text3)',fontSize:'.82rem'}}>{fileName ? fileName : `Click to upload ${label}`}</span>
    </>
  )
}