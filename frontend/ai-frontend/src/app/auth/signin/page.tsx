"use client"

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function SignIn() {
  const [formData, setFormData] = useState({ email: '', password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()

  const validate = () => {
    const e: Record<string, string> = {}
    if (!formData.email) e.email = 'Email is required'
    else if (!/\S+@\S+\.\S+/.test(formData.email)) e.email = 'Invalid email address'
    if (!formData.password) e.password = 'Password is required'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async (ev: React.FormEvent) => {
    ev.preventDefault()
    if (!validate()) return
    setIsLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/signin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: formData.email, password: formData.password }),
      })
      if (res.ok) {
        const result = await res.json()
        localStorage.setItem('authToken', result.access_token)
        localStorage.setItem('userEmail', formData.email)
        const profileRes = await fetch(`${API_BASE}/api/v1/user/profile`, {
          headers: { Authorization: `Bearer ${result.access_token}` },
        })
        if (profileRes.ok) {
          const userData = await profileRes.json()
          localStorage.setItem('userRegistration', JSON.stringify(userData))
          localStorage.setItem('verificationStatus', userData.verification_status || 'pending')
          localStorage.setItem('biometricStatus', userData.biometric_status || 'pending')
        }
        router.push('/user-dashboard')
      } else {
        const err = await res.json()
        setErrors({ submit: err.detail || 'Invalid email or password' })
      }
    } catch {
      setErrors({ submit: 'Connection failed. Please try again.' })
    } finally {
      setIsLoading(false)
    }
  }

  const set = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    setErrors(prev => ({ ...prev, [field]: '' }))
  }

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');
        *{box-sizing:border-box;margin:0;padding:0;}
        :root{
          --bg:#04080F;--surface:#080E1A;--surface2:#0C1524;
          --green:#00D46A;--green-dim:#007A3D;--green-glow:rgba(0,212,106,0.12);
          --red:#FF4D4D;--red-dim:rgba(255,77,77,0.08);
          --border:rgba(255,255,255,0.07);--border2:rgba(255,255,255,0.12);
          --text:#F0F4FF;--text2:rgba(240,244,255,0.55);--text3:rgba(240,244,255,0.28);
        }
        body{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;min-height:100vh;}
        .syne{font-family:'Syne',sans-serif;}
        .grid-bg{
          background-image:linear-gradient(rgba(0,212,106,0.025) 1px,transparent 1px),linear-gradient(90deg,rgba(0,212,106,0.025) 1px,transparent 1px);
          background-size:60px 60px;
        }
        .orb{position:absolute;border-radius:50%;filter:blur(120px);pointer-events:none;}
        input{
          width:100%;padding:.75rem 1rem .75rem 2.75rem;
          background:rgba(255,255,255,0.04);
          border:1px solid var(--border2);border-radius:10px;
          color:var(--text);font-family:'DM Sans',sans-serif;font-size:.9rem;outline:none;
          transition:border-color .2s,box-shadow .2s;
        }
        input:focus{border-color:var(--green);box-shadow:0 0 0 3px rgba(0,212,106,0.1);}
        input.err{border-color:var(--red);}
        input::placeholder{color:var(--text3);}
        input:-webkit-autofill{-webkit-box-shadow:0 0 0 1000px #080E1A inset!important;-webkit-text-fill-color:var(--text)!important;}
        label{display:block;font-size:.82rem;font-weight:500;color:var(--text2);margin-bottom:.45rem;}
        .field{position:relative;margin-bottom:1.25rem;}
        .field-icon{position:absolute;left:.85rem;top:50%;transform:translateY(-50%);color:var(--text3);}
        .error-msg{color:var(--red);font-size:.78rem;margin-top:.4rem;display:flex;align-items:center;gap:4px;}
        .btn-green{
          width:100%;padding:.85rem;border-radius:10px;
          background:var(--green);color:#04080F;
          font-family:'Syne',sans-serif;font-weight:700;font-size:.92rem;letter-spacing:.03em;
          border:none;cursor:pointer;transition:opacity .2s,transform .2s,box-shadow .2s;
          display:flex;align-items:center;justify-content:center;gap:8px;
        }
        .btn-green:hover:not(:disabled){opacity:.9;transform:translateY(-1px);box-shadow:0 8px 30px rgba(0,212,106,0.25);}
        .btn-green:disabled{opacity:.5;cursor:not-allowed;}
        .card{
          background:var(--surface);border:1px solid var(--border);
          border-radius:20px;padding:2.5rem;width:100%;max-width:440px;
          position:relative;overflow:hidden;
        }
        .divider{display:flex;align-items:center;gap:.75rem;margin:1.5rem 0;}
        .divider-line{flex:1;height:1px;background:var(--border);}
        .btn-bio{
          width:100%;padding:.75rem;border-radius:10px;
          background:transparent;border:1px solid var(--border2);
          color:var(--text2);font-family:'DM Sans',sans-serif;font-size:.88rem;
          cursor:pointer;transition:background .2s,border-color .2s;
          display:flex;align-items:center;justify-content:center;gap:8px;
        }
        .btn-bio:hover{background:rgba(255,255,255,0.04);border-color:rgba(255,255,255,0.2);}
        .submit-error{
          background:rgba(255,77,77,0.06);border:1px solid rgba(255,77,77,0.2);
          border-radius:10px;padding:.75rem 1rem;margin-bottom:1rem;
          color:var(--red);font-size:.84rem;display:flex;align-items:center;gap:8px;
        }
        @keyframes spin{to{transform:rotate(360deg);}}
        .spinner{width:16px;height:16px;border:2px solid rgba(4,8,15,0.3);border-top-color:#04080F;border-radius:50%;animation:spin .7s linear infinite;}
        .show-pass{position:absolute;right:.85rem;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;color:var(--text3);padding:2px;}
        .show-pass:hover{color:var(--text2);}
        @keyframes fadeIn{from{opacity:0;transform:translateY(16px);}to{opacity:1;transform:translateY(0);}}
        .fade-in{animation:fadeIn .5s ease forwards;}
      `}</style>

      <div className="grid-bg" style={{minHeight:'100vh',display:'flex',alignItems:'center',justifyContent:'center',padding:'2rem',position:'relative'}}>
        <div className="orb" style={{width:500,height:500,background:'rgba(0,212,106,0.05)',top:'0%',right:'10%'}}/>
        <div className="orb" style={{width:300,height:300,background:'rgba(245,200,66,0.03)',bottom:'10%',left:'5%'}}/>

        <div className="fade-in" style={{width:'100%',maxWidth:440}}>
          {/* Logo */}
          <div style={{textAlign:'center',marginBottom:'2rem'}}>
            <div style={{
              width:52,height:52,borderRadius:14,margin:'0 auto 1rem',
              background:'linear-gradient(135deg,#00D46A,#007A3D)',
              display:'flex',alignItems:'center',justifyContent:'center',
            }}>
              <svg width="26" height="26" fill="none" stroke="#04080F" strokeWidth="2.5" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
              </svg>
            </div>
            <h1 className="syne" style={{fontSize:'1.6rem',fontWeight:800,marginBottom:'.35rem'}}>Welcome Back</h1>
            <p style={{color:'var(--text2)',fontSize:'.88rem'}}>Sign in to your UhakikiAI account</p>
          </div>

          <div className="card">
            <div style={{
              position:'absolute',top:0,left:0,right:0,height:2,
              background:'linear-gradient(90deg,transparent,var(--green),transparent)',
            }}/>

            <form onSubmit={handleSubmit}>
              {/* Email */}
              <div style={{marginBottom:'1.25rem'}}>
                <label>Email Address</label>
                <div className="field" style={{margin:0}}>
                  <span className="field-icon">
                    <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>
                  </span>
                  <input
                    type="email" value={formData.email}
                    onChange={e => set('email', e.target.value)}
                    className={errors.email ? 'err' : ''}
                    placeholder="your.email@example.com"
                  />
                </div>
                {errors.email && <p className="error-msg">⚠ {errors.email}</p>}
              </div>

              {/* Password */}
              <div style={{marginBottom:'1.5rem'}}>
                <label>Password</label>
                <div className="field" style={{margin:0}}>
                  <span className="field-icon">
                    <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
                  </span>
                  <input
                    type={showPassword ? 'text' : 'password'} value={formData.password}
                    onChange={e => set('password', e.target.value)}
                    className={errors.password ? 'err' : ''}
                    placeholder="Enter your password"
                    style={{paddingRight:'2.75rem'}}
                  />
                  <button type="button" className="show-pass" onClick={() => setShowPassword(!showPassword)}>
                    {showPassword
                      ? <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                      : <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    }
                  </button>
                </div>
                {errors.password && <p className="error-msg">⚠ {errors.password}</p>}
              </div>

              {/* Remember / Forgot */}
              <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'1.5rem'}}>
                <label style={{display:'flex',alignItems:'center',gap:8,cursor:'pointer',margin:0}}>
                  <input type="checkbox" style={{width:'auto',padding:0,background:'none',border:'1px solid var(--border2)'}}/>
                  <span style={{fontSize:'.83rem',color:'var(--text2)'}}>Remember me</span>
                </label>
                <a href="#" style={{color:'var(--green)',fontSize:'.83rem',textDecoration:'none',fontWeight:500}}>Forgot password?</a>
              </div>

              {errors.submit && (
                <div className="submit-error">
                  <svg width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                  {errors.submit}
                </div>
              )}

              <button type="submit" className="btn-green" disabled={isLoading}>
                {isLoading ? <><div className="spinner"/> Signing in...</> : 'Sign In'}
              </button>
            </form>

            <div className="divider">
              <div className="divider-line"/>
              <span style={{color:'var(--text3)',fontSize:'.78rem',whiteSpace:'nowrap'}}>or continue with</span>
              <div className="divider-line"/>
            </div>

            <button className="btn-bio">
              <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/><path d="M12 6v6l4 2"/></svg>
              Biometric Sign In
            </button>
            <p style={{textAlign:'center',color:'var(--text3)',fontSize:'.75rem',marginTop:'.5rem'}}>Use face recognition or voice biometrics</p>
          </div>

          <p style={{textAlign:'center',marginTop:'1.5rem',color:'var(--text2)',fontSize:'.88rem'}}>
            Don&apos;t have an account?{' '}
            <Link href="/auth/signup" style={{color:'var(--green)',textDecoration:'none',fontWeight:600}}>Register here</Link>
          </p>

          {/* Trust */}
          <div style={{display:'flex',justifyContent:'center',gap:'1.5rem',marginTop:'1.5rem'}}>
            {['Encrypted','Privacy Protected','GDPR'].map(t => (
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