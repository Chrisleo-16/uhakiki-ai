"use client"

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

interface UserProfile {
  user_id: string; firstName: string; email: string; phone: string
  identificationNumber: string; institution: string; course: string; yearOfStudy: string
  verificationStatus: 'pending'|'active'|'incomplete'; biometricStatus: 'pending'|'complete'
  registrationDate: string; citizenship: string; identificationType: string
}

const STATUS_META = {
  active:     { color:'#00D46A', bg:'rgba(0,212,106,0.08)',  border:'rgba(0,212,106,0.2)',  label:'Active'     },
  pending:    { color:'#F5C842', bg:'rgba(245,200,66,0.08)', border:'rgba(245,200,66,0.2)', label:'Pending'    },
  incomplete: { color:'#FF4D4D', bg:'rgba(255,77,77,0.08)',  border:'rgba(255,77,77,0.2)',  label:'Incomplete' },
}

export default function UserDashboard() {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const token = localStorage.getItem('authToken')
        console.log('User Dashboard - Token exists:', !!token)
        console.log('User Dashboard - Token:', token ? token.substring(0, 20) + '...' : 'null')
        
        if (!token) {
          console.log('No token found, redirecting to signin')
          router.push('/auth/signin')
          return
        }

        console.log('Fetching user profile from backend...')
        const response = await fetch('http://localhost:8000/api/v1/user/profile', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })

        console.log('Profile response status:', response.status)

        if (response.ok) {
          const userData = await response.json()
          console.log('User data fetched successfully:', userData)
          setProfile(userData)
          localStorage.setItem('userRegistration', JSON.stringify(userData))
          localStorage.setItem('verificationStatus', userData.verificationStatus || 'pending')
          localStorage.setItem('biometricStatus', userData.biometricStatus || 'pending')
        } else if (response.status === 401) {
          console.log('Token invalid/expired, clearing and redirecting to signin')
          localStorage.removeItem('authToken')
          localStorage.removeItem('userRegistration')
          localStorage.removeItem('verificationStatus')
          localStorage.removeItem('biometricStatus')
          router.push('/auth/signin')
        } else if (response.status === 404) {
          console.log('User profile endpoint not found, using localStorage fallback')
          // Fallback to localStorage data
          const storedUserData = localStorage.getItem('userRegistration')
          if (storedUserData) {
            const userData = JSON.parse(storedUserData)
            setProfile(userData)
          } else {
            console.log('No stored user data found, redirecting to signup')
            router.push('/auth/signup')
          }
        } else {
          console.error('Failed to fetch user data, status:', response.status)
          // Try to use localStorage data as fallback
          const storedUserData = localStorage.getItem('userRegistration')
          if (storedUserData) {
            const userData = JSON.parse(storedUserData)
            setProfile(userData)
          } else {
            router.push('/auth/signup')
          }
        }
      } catch (error) {
        console.error('Error fetching user data:', error)
        // Try to use localStorage data as fallback
        const storedUserData = localStorage.getItem('userRegistration')
        if (storedUserData) {
          const userData = JSON.parse(storedUserData)
          setProfile(userData)
        } else {
          router.push('/auth/signup')
        }
      } finally {
        setLoading(false)
      }
    }

    fetchUserData()
  }, [router])

  const handleLogout = () => { localStorage.clear(); router.push('/') }

  if (loading) return (
    <div style={{minHeight:'100vh',background:'#04080F',display:'flex',alignItems:'center',justifyContent:'center'}}>
      <div style={{textAlign:'center'}}>
        <div style={{width:48,height:48,border:'2px solid rgba(0,212,106,0.2)',borderTopColor:'#00D46A',borderRadius:'50%',animation:'spin .7s linear infinite',margin:'0 auto 1rem'}}/>
        <p style={{color:'rgba(240,244,255,0.4)',fontFamily:'DM Sans,sans-serif',fontSize:'.88rem'}}>Loading dashboard...</p>
      </div>
      <style>{`@keyframes spin{to{transform:rotate(360deg);}}`}</style>
    </div>
  )

  if (!profile) return null

  const vs = STATUS_META[profile.verificationStatus] || STATUS_META.pending
  const bs = profile.biometricStatus === 'complete' ? STATUS_META.active : STATUS_META.pending
  const secLevel = profile.verificationStatus === 'active' && profile.biometricStatus === 'complete' ? 'High' : 'Standard'

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');
        *{box-sizing:border-box;margin:0;padding:0;}
        :root{
          --bg:#04080F;--surface:#080E1A;--surface2:#0C1524;
          --green:#00D46A;--green-glow:rgba(0,212,106,0.12);
          --border:rgba(255,255,255,0.07);--border2:rgba(255,255,255,0.12);
          --text:#F0F4FF;--text2:rgba(240,244,255,0.55);--text3:rgba(240,244,255,0.28);
        }
        body{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;min-height:100vh;}
        .syne{font-family:'Syne',sans-serif;}
        nav{
          display:flex;align-items:center;justify-content:space-between;
          padding:.9rem 2.5rem;background:rgba(4,8,15,0.9);backdrop-filter:blur(16px);
          border-bottom:1px solid var(--border);position:sticky;top:0;z-index:100;
        }
        .nav-logo{display:flex;align-items:center;gap:10px;}
        .logo-icon{width:34px;height:34px;border-radius:9px;background:linear-gradient(135deg,#00D46A,#007A3D);display:flex;align-items:center;justify-content:center;}
        .nav-links a{color:var(--text2);text-decoration:none;font-size:.88rem;font-weight:500;transition:color .2s;margin-left:1.75rem;}
        .nav-links a:hover,.nav-links a.active{color:var(--text);}
        .icon-btn{background:none;border:none;cursor:pointer;color:var(--text2);padding:.45rem;border-radius:8px;transition:background .2s,color .2s;}
        .icon-btn:hover{background:rgba(255,255,255,0.06);color:var(--text);}
        main{max-width:1100px;margin:0 auto;padding:2.5rem 2rem;}
        .stat-card{
          background:var(--surface);border:1px solid var(--border);
          border-radius:16px;padding:1.5rem;transition:border-color .2s,transform .2s;position:relative;overflow:hidden;
        }
        .stat-card:hover{border-color:var(--border2);transform:translateY(-2px);}
        .action-card{
          background:var(--surface);border:1px solid var(--border);
          border-radius:16px;padding:1.5rem;transition:border-color .2s,transform .2s;
        }
        .action-card:hover{transform:translateY(-2px);}
        .btn{
          display:inline-flex;align-items:center;gap:6px;
          padding:.6rem 1.25rem;border-radius:9px;font-size:.84rem;font-weight:600;
          cursor:pointer;text-decoration:none;border:none;transition:opacity .2s,transform .2s;
        }
        .btn:hover{opacity:.85;transform:translateY(-1px);}
        .profile-grid{display:grid;grid-template-columns:1fr 1fr;gap:2.5rem;}
        .dl dt{color:var(--text3);font-size:.78rem;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.2rem;}
        .dl dd{color:var(--text);font-size:.9rem;font-weight:500;margin-bottom:1rem;}
        .status-badge{
          display:inline-flex;align-items:center;gap:6px;
          padding:.3rem .85rem;border-radius:100px;font-size:.75rem;font-weight:600;letter-spacing:.04em;text-transform:uppercase;
        }
        .status-dot{width:6px;height:6px;border-radius:50%;}
        @keyframes fadeIn{from{opacity:0;transform:translateY(12px);}to{opacity:1;transform:translateY(0);}}
        .fade-in{animation:fadeIn .4s ease forwards;}
        @keyframes spin{to{transform:rotate(360deg);}}
        .grid-2{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1.25rem;}
        .grid-3{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:1.25rem;}
        .section-title{font-family:'Syne',sans-serif;font-weight:700;font-size:1rem;margin-bottom:1.25rem;color:var(--text);}
      `}</style>

      {/* NAV */}
      <nav>
        <div className="nav-logo">
          <div className="logo-icon">
            <svg width="18" height="18" fill="none" stroke="#04080F" strokeWidth="2.5" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
            </svg>
          </div>
          <span className="syne" style={{fontWeight:700,fontSize:'1rem'}}>UhakikiAI</span>
        </div>
        <div className="nav-links">
          <a href="/user-dashboard" className="active">Dashboard</a>
          <a href="/user-profile">Profile</a>
          <a href="/guide">AI Guide</a>
        </div>
        <div style={{display:'flex',alignItems:'center',gap:'.5rem'}}>
          <button className="icon-btn" title="Settings">
            <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
          </button>
          <button className="icon-btn" onClick={handleLogout} title="Logout">
            <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>
          </button>
        </div>
      </nav>

      <main>
        {/* Welcome banner */}
        <div className="fade-in" style={{
          background:'linear-gradient(135deg,rgba(0,212,106,0.06),rgba(0,122,61,0.03))',
          border:'1px solid rgba(0,212,106,0.15)',borderRadius:16,
          padding:'1.75rem 2rem',marginBottom:'2rem',
          display:'flex',alignItems:'center',justifyContent:'space-between',flexWrap:'wrap',gap:'1rem',
        }}>
          <div>
            <h2 className="syne" style={{fontSize:'1.4rem',fontWeight:800,marginBottom:'.25rem'}}>
              Welcome back, {profile.firstName}
            </h2>
            <p style={{color:'var(--text2)',fontSize:'.88rem'}}>Manage your identity verification and biometric settings</p>
          </div>
          <div className="status-badge" style={{background:vs.bg,border:`1px solid ${vs.border}`,color:vs.color}}>
            <span className="status-dot" style={{background:vs.color}}/>
            Account {vs.label}
          </div>
        </div>

        {/* Stats grid */}
        <div className="grid-2" style={{marginBottom:'2rem'}}>
          {[
            {
              label:'Verification',value:vs.label,sub: vs.label==='Active' ? 'Identity confirmed' : 'Completion required',
              icon:<svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>,
              color:vs.color, bg:vs.bg,
            },
            {
              label:'Biometrics',value: profile.biometricStatus === 'complete' ? 'Complete' : 'Pending',
              sub: profile.biometricStatus === 'complete' ? 'Face & voice registered' : 'Registration needed',
              icon:<svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z"/><path d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z"/></svg>,
              color:bs.color, bg:bs.bg,
            },
            {
              label:'Security Level',value:secLevel,sub: secLevel === 'High' ? 'Multi-factor active' : 'Complete setup to upgrade',
              icon:<svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>,
              color:'#3B82F6', bg:'rgba(59,130,246,0.08)',
            },
            {
              label:'Institution',value: profile.institution ? profile.institution.split('-').map((w:string)=>w[0].toUpperCase()+w.slice(1)).join(' ').slice(0,22) : '—',
              sub:profile.course || 'Course not set',
              icon:<svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>,
              color:'#F5C842', bg:'rgba(245,200,66,0.08)',
            },
          ].map(s => (
            <div key={s.label} className="stat-card fade-in">
              <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:'1rem'}}>
                <div style={{width:40,height:40,borderRadius:10,background:s.bg,display:'flex',alignItems:'center',justifyContent:'center',color:s.color}}>
                  {s.icon}
                </div>
                <span style={{width:8,height:8,borderRadius:'50%',background:s.color,display:'block',marginTop:4}}/>
              </div>
              <p style={{fontSize:'.78rem',color:'var(--text3)',textTransform:'uppercase',letterSpacing:'.05em',marginBottom:'.3rem'}}>{s.label}</p>
              <p className="syne" style={{fontSize:'1.15rem',fontWeight:700,color:s.color,marginBottom:'.2rem'}}>{s.value}</p>
              <p style={{fontSize:'.78rem',color:'var(--text3)'}}>{s.sub}</p>
            </div>
          ))}
        </div>

        {/* Action cards */}
        <p className="section-title">Pending Actions</p>
        <div className="grid-3" style={{marginBottom:'2.5rem'}}>
          {profile.verificationStatus !== 'active' && (
            <div className="action-card" style={{borderColor:'rgba(245,200,66,0.2)'}}>
              <div style={{display:'flex',alignItems:'center',gap:10,marginBottom:'.75rem'}}>
                <div style={{width:36,height:36,borderRadius:9,background:'rgba(245,200,66,0.1)',display:'flex',alignItems:'center',justifyContent:'center'}}>
                  <svg width="18" height="18" fill="none" stroke="#F5C842" strokeWidth="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                </div>
                <span className="syne" style={{fontWeight:700,fontSize:'.95rem'}}>Complete Verification</span>
              </div>
              <p style={{color:'var(--text2)',fontSize:'.84rem',lineHeight:1.6,marginBottom:'1rem'}}>Your account verification is incomplete. Finish to unlock all features.</p>
              <Link href="/auth/verify-id" className="btn" style={{background:'rgba(245,200,66,0.12)',color:'#F5C842',border:'1px solid rgba(245,200,66,0.25)'}}>
                Complete Now →
              </Link>
            </div>
          )}
          {profile.biometricStatus !== 'complete' && (
            <div className="action-card" style={{borderColor:'rgba(59,130,246,0.2)'}}>
              <div style={{display:'flex',alignItems:'center',gap:10,marginBottom:'.75rem'}}>
                <div style={{width:36,height:36,borderRadius:9,background:'rgba(59,130,246,0.1)',display:'flex',alignItems:'center',justifyContent:'center'}}>
                  <svg width="18" height="18" fill="none" stroke="#3B82F6" strokeWidth="2" viewBox="0 0 24 24"><path d="M23 7l-7 5 7 5V7z"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
                </div>
                <span className="syne" style={{fontWeight:700,fontSize:'.95rem'}}>Register Biometrics</span>
              </div>
              <p style={{color:'var(--text2)',fontSize:'.84rem',lineHeight:1.6,marginBottom:'1rem'}}>Add facial recognition and voice for enhanced security and instant login.</p>
              <Link href="/auth/biometric-registration" className="btn" style={{background:'rgba(59,130,246,0.1)',color:'#3B82F6',border:'1px solid rgba(59,130,246,0.25)'}}>
                Register Now →
              </Link>
            </div>
          )}
          <div className="action-card" style={{borderColor:'rgba(0,212,106,0.15)'}}>
            <div style={{display:'flex',alignItems:'center',gap:10,marginBottom:'.75rem'}}>
              <div style={{width:36,height:36,borderRadius:9,background:'rgba(0,212,106,0.1)',display:'flex',alignItems:'center',justifyContent:'center'}}>
                <svg width="18" height="18" fill="none" stroke="var(--green)" strokeWidth="2" viewBox="0 0 24 24"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
              </div>
              <span className="syne" style={{fontWeight:700,fontSize:'.95rem'}}>AI Assistant</span>
            </div>
            <p style={{color:'var(--text2)',fontSize:'.84rem',lineHeight:1.6,marginBottom:'1rem'}}>Get help and guidance from our AI assistant about the platform.</p>
            <Link href="/guide" className="btn" style={{background:'rgba(0,212,106,0.08)',color:'var(--green)',border:'1px solid rgba(0,212,106,0.2)'}}>
              Ask AI Guide →
            </Link>
          </div>
        </div>

        {/* Profile summary */}
        <div style={{background:'var(--surface)',border:'1px solid var(--border)',borderRadius:16,padding:'2rem'}}>
          <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:'1.75rem'}}>
            <p className="section-title" style={{margin:0}}>Profile Summary</p>
            <Link href="/user-profile" className="btn" style={{background:'rgba(255,255,255,0.04)',color:'var(--text2)',border:'1px solid var(--border2)',fontSize:'.8rem',padding:'.45rem 1rem'}}>
              Edit Profile
            </Link>
          </div>
          <div className="profile-grid">
            <div className="dl">
              <p style={{color:'var(--text3)',fontSize:'.78rem',fontWeight:600,textTransform:'uppercase',letterSpacing:'.08em',marginBottom:'1rem'}}>Personal</p>
              <dt>Full Name</dt><dd>{profile.firstName}</dd>
              <dt>Email</dt><dd>{profile.email}</dd>
              <dt>Phone</dt><dd>{profile.phone || '—'}</dd>
              <dt>ID Number</dt><dd>••••••{(profile.identificationNumber || '').slice(-2)}</dd>
            </div>
            <div className="dl">
              <p style={{color:'var(--text3)',fontSize:'.78rem',fontWeight:600,textTransform:'uppercase',letterSpacing:'.08em',marginBottom:'1rem'}}>Academic</p>
              <dt>Institution</dt><dd>{profile.institution ? profile.institution.split('-').map((w:string)=>w[0].toUpperCase()+w.slice(1)).join(' ') : '—'}</dd>
              <dt>Course</dt><dd>{profile.course || '—'}</dd>
              <dt>Year of Study</dt><dd>{profile.yearOfStudy ? `Year ${profile.yearOfStudy}` : '—'}</dd>
              <dt>Member Since</dt><dd>{profile.registrationDate}</dd>
            </div>
          </div>
        </div>
      </main>
    </>
  )
}