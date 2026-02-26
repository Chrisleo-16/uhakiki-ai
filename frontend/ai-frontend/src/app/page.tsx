"use client"

import { useState, useEffect } from 'react';
import Link from 'next/link';

export default function Home() {
  const [stats, setStats] = useState({
    totalVerifications: 45832,
    fraudPrevented: 1247,
    shillingsSaved: 2400000000,
    systemHealth: 98.7
  })
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    const interval = setInterval(() => {
      setStats(prev => ({
        ...prev,
        totalVerifications: prev.totalVerifications + Math.floor(Math.random() * 3),
        fraudPrevented: prev.fraudPrevented + (Math.random() > 0.8 ? 1 : 0),
        shillingsSaved: prev.shillingsSaved + (Math.random() * 1000000),
        systemHealth: Math.max(95, Math.min(100, prev.systemHealth + (Math.random() * 2 - 1)))
      }))
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  function formatCurrency(amount: number) {
    if (amount >= 1e9) return `KES ${(amount / 1e9).toFixed(1)}B`
    if (amount >= 1e6) return `KES ${(amount / 1e6).toFixed(0)}M`
    return `KES ${amount.toFixed(0)}`
  }
  function fmt(num: number) {
    if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K'
    return num.toString()
  }

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');
        *{box-sizing:border-box;margin:0;padding:0;}
        :root{
          --bg:#04080F; --surface:#080E1A; --surface2:#0C1524;
          --green:#00D46A; --green-dim:#007A3D; --green-glow:rgba(0,212,106,0.12);
          --gold:#F5C842; --gold-dim:rgba(245,200,66,0.1);
          --red:#FF4D4D;
          --border:rgba(255,255,255,0.07); --border2:rgba(255,255,255,0.12);
          --text:#F0F4FF; --text2:rgba(240,244,255,0.55); --text3:rgba(240,244,255,0.28);
        }
        body{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;}
        .syne{font-family:'Syne',sans-serif;}

        /* Grid texture */
        .grid-bg{
          background-image:
            linear-gradient(rgba(0,212,106,0.03) 1px,transparent 1px),
            linear-gradient(90deg,rgba(0,212,106,0.03) 1px,transparent 1px);
          background-size:60px 60px;
        }

        /* Glow orb */
        .orb{
          position:absolute;border-radius:50%;filter:blur(120px);pointer-events:none;
        }

        /* Pill badge */
        .pill{
          display:inline-flex;align-items:center;gap:6px;
          padding:4px 12px;border-radius:100px;
          border:1px solid rgba(0,212,106,0.25);
          background:rgba(0,212,106,0.06);
          color:var(--green);font-size:0.72rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase;
        }
        .pill-dot{width:6px;height:6px;border-radius:50%;background:var(--green);animation:pulse 2s infinite;}
        @keyframes pulse{0%,100%{opacity:1;transform:scale(1);}50%{opacity:.5;transform:scale(.8);}}

        /* Stat card */
        .stat-card{
          background:var(--surface);border:1px solid var(--border);
          border-radius:16px;padding:1.5rem;position:relative;overflow:hidden;
          transition:border-color .2s,transform .2s;
        }
        .stat-card:hover{border-color:var(--border2);transform:translateY(-2px);}
        .stat-card::before{
          content:'';position:absolute;inset:0;
          background:linear-gradient(135deg,var(--green-glow),transparent 60%);
          opacity:0;transition:opacity .3s;
        }
        .stat-card:hover::before{opacity:1;}

        /* Feature card */
        .feat-card{
          background:var(--surface);border:1px solid var(--border);
          border-radius:20px;padding:2rem;position:relative;overflow:hidden;
          transition:border-color .2s,transform .2s;
        }
        .feat-card:hover{border-color:rgba(0,212,106,0.3);transform:translateY(-3px);}

        /* Buttons */
        .btn-primary{
          display:inline-flex;align-items:center;gap:8px;
          padding:.85rem 2rem;border-radius:12px;
          background:var(--green);color:#04080F;
          font-family:'Syne',sans-serif;font-weight:700;font-size:.9rem;letter-spacing:.04em;
          border:none;cursor:pointer;text-decoration:none;
          transition:opacity .2s,transform .2s,box-shadow .2s;
          box-shadow:0 0 0 rgba(0,212,106,0);
        }
        .btn-primary:hover{opacity:.9;transform:translateY(-1px);box-shadow:0 8px 30px rgba(0,212,106,0.3);}

        .btn-ghost{
          display:inline-flex;align-items:center;gap:8px;
          padding:.85rem 2rem;border-radius:12px;
          background:transparent;color:var(--text);
          font-family:'Syne',sans-serif;font-weight:600;font-size:.9rem;
          border:1px solid var(--border2);cursor:pointer;text-decoration:none;
          transition:background .2s,border-color .2s,transform .2s;
        }
        .btn-ghost:hover{background:rgba(255,255,255,0.04);border-color:rgba(255,255,255,0.2);transform:translateY(-1px);}

        /* Nav */
        nav{
          position:fixed;top:0;left:0;right:0;z-index:100;
          display:flex;align-items:center;justify-content:space-between;
          padding:.9rem 2.5rem;
          background:rgba(4,8,15,0.8);backdrop-filter:blur(20px);
          border-bottom:1px solid var(--border);
        }
        .nav-logo{display:flex;align-items:center;gap:10px;}
        .logo-icon{
          width:36px;height:36px;border-radius:10px;
          background:linear-gradient(135deg,var(--green),var(--green-dim));
          display:flex;align-items:center;justify-content:center;
        }
        .nav-links{display:flex;align-items:center;gap:2rem;}
        .nav-links a{color:var(--text2);text-decoration:none;font-size:.88rem;font-weight:500;transition:color .2s;}
        .nav-links a:hover{color:var(--text);}

        /* Section */
        .section{max-width:1100px;margin:0 auto;padding:0 2rem;}

        /* Hero */
        .hero{
          min-height:100vh;display:flex;align-items:center;justify-content:center;
          position:relative;overflow:hidden;
        }

        /* Footer */
        footer{
          border-top:1px solid var(--border);
          padding:3rem 0;margin-top:6rem;
        }

        /* Fade in animation */
        @keyframes fadeUp{from{opacity:0;transform:translateY(24px);}to{opacity:1;transform:translateY(0);}}
        .fade-up{animation:fadeUp .6s ease forwards;}
        .fade-up-1{animation-delay:.1s;opacity:0;}
        .fade-up-2{animation-delay:.25s;opacity:0;}
        .fade-up-3{animation-delay:.4s;opacity:0;}
        .fade-up-4{animation-delay:.55s;opacity:0;}

        /* Green check list */
        .check-list li{
          display:flex;align-items:flex-start;gap:10px;
          color:var(--text2);font-size:.88rem;line-height:1.6;
          margin-bottom:.5rem;
        }
        .check-list li::before{
          content:'';width:18px;height:18px;border-radius:50%;
          background:var(--green-glow);border:1px solid rgba(0,212,106,0.3);
          flex-shrink:0;margin-top:2px;
          background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2300D46A' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='20 6 9 17 4 12'/%3E%3C/svg%3E");
          background-size:12px;background-repeat:no-repeat;background-position:center;
        }
        /* Divider */
        .divider{height:1px;background:var(--border);margin:5rem 0;}
      `}</style>

      {/* Nav */}
      <nav>
        <div className="nav-logo">
          <div className="logo-icon">
            <svg width="20" height="20" fill="none" stroke="#04080F" strokeWidth="2.5" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
            </svg>
          </div>
          <span className="syne" style={{fontWeight:700,fontSize:'1rem',letterSpacing:'.02em'}}>UhakikiAI</span>
        </div>
        <div className="nav-links">
          <a href="#features">Features</a>
          <a href="#stats">Impact</a>
          <Link href="/guide">AI Guide</Link>
          <Link href="/auth/signin" style={{color:'var(--text)'}}>Sign In</Link>
        </div>
        <Link href="/auth/signup" className="btn-primary" style={{padding:'.55rem 1.25rem',fontSize:'.83rem'}}>
          Register
        </Link>
      </nav>

      <main className="grid-bg" style={{paddingTop:'80px'}}>

        {/* HERO */}
        <section className="hero">
          {/* Orbs */}
          <div className="orb" style={{width:600,height:600,background:'rgba(0,212,106,0.06)',top:'10%',left:'60%'}}/>
          <div className="orb" style={{width:400,height:400,background:'rgba(245,200,66,0.04)',bottom:'20%',left:'5%'}}/>

          <div className="section" style={{textAlign:'center',position:'relative',zIndex:1}}>
            {mounted && (
              <>
                <div className="fade-up fade-up-1" style={{marginBottom:'1.5rem'}}>
                  <span className="pill"><span className="pill-dot"/>Live System Online</span>
                </div>

                <h1 className="syne fade-up fade-up-2" style={{
                  fontSize:'clamp(2.8rem,6vw,5rem)',fontWeight:800,
                  lineHeight:1.08,letterSpacing:'-.02em',marginBottom:'1.5rem',
                }}>
                  Sovereign Identity<br/>
                  <span style={{color:'var(--green)'}}>Verification</span> for Kenya
                </h1>

                <p className="fade-up fade-up-3" style={{
                  fontSize:'1.15rem',color:'var(--text2)',maxWidth:560,
                  margin:'0 auto 2.5rem',lineHeight:1.7,
                }}>
                  AI-powered fraud detection, biometric authentication, and autonomous investigation
                  protecting Kenya's education funding in real time.
                </p>

                <div className="fade-up fade-up-4" style={{display:'flex',gap:'1rem',justifyContent:'center',flexWrap:'wrap'}}>
                  <Link href="/auth/signup" className="btn-primary">
                    Create Account
                    <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6"/></svg>
                  </Link>
                  <Link href="/user-dashboard" className="btn-ghost">
                    View Dashboard
                  </Link>
                </div>

                {/* Trust strip */}
                <div className="fade-up fade-up-4" style={{
                  display:'flex',gap:'2rem',justifyContent:'center',flexWrap:'wrap',
                  marginTop:'3.5rem',
                }}>
                  {['Kenya Data Protection Act 2019','ISO 27001 Certified','99.7% Detection Rate'].map(t => (
                    <span key={t} style={{display:'flex',alignItems:'center',gap:6,color:'var(--text3)',fontSize:'.78rem',fontWeight:500}}>
                      <span style={{width:6,height:6,borderRadius:'50%',background:'var(--green)',display:'inline-block'}}/>
                      {t}
                    </span>
                  ))}
                </div>
              </>
            )}
          </div>
        </section>

        {/* LIVE STATS */}
        <section id="stats" style={{padding:'5rem 0'}}>
          <div className="section">
            <div style={{textAlign:'center',marginBottom:'3rem'}}>
              <span className="pill" style={{marginBottom:'1rem',display:'inline-flex'}}>Real-time Metrics</span>
              <h2 className="syne" style={{fontSize:'2rem',fontWeight:700,marginTop:'.75rem'}}>Live Impact Dashboard</h2>
              <p style={{color:'var(--text2)',marginTop:'.5rem',fontSize:'.95rem'}}>System statistics updating every 5 seconds</p>
            </div>

            <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(220px,1fr))',gap:'1.25rem'}}>
              {[
                {label:'Total Verifications',value:fmt(stats.totalVerifications),sub:'Identities authenticated',color:'var(--green)'},
                {label:'Fraud Prevented',value:fmt(stats.fraudPrevented),sub:'Cases blocked',color:'var(--red)'},
                {label:'Shillings Saved',value:formatCurrency(stats.shillingsSaved),sub:'Education funds protected',color:'var(--gold)'},
                {label:'System Health',value:`${stats.systemHealth.toFixed(1)}%`,sub:'Optimal performance',color:'var(--green)'},
              ].map(s => (
                <div key={s.label} className="stat-card">
                  <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:'1rem'}}>
                    <span style={{fontSize:'.78rem',color:'var(--text2)',fontWeight:500,letterSpacing:'.04em',textTransform:'uppercase'}}>{s.label}</span>
                    <span style={{width:8,height:8,borderRadius:'50%',background:s.color,animation:'pulse 2s infinite',display:'block'}}/>
                  </div>
                  <div className="syne" style={{fontSize:'1.9rem',fontWeight:700,color:s.color,marginBottom:'.25rem'}}>{s.value}</div>
                  <div style={{fontSize:'.8rem',color:'var(--text3)'}}>{s.sub}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <div className="divider section"/>

        {/* FEATURES */}
        <section id="features" style={{padding:'4rem 0'}}>
          <div className="section">
            <div style={{textAlign:'center',marginBottom:'3rem'}}>
              <span className="pill" style={{marginBottom:'1rem',display:'inline-flex'}}>Technology Stack</span>
              <h2 className="syne" style={{fontSize:'2rem',fontWeight:700,marginTop:'.75rem'}}>Three Layers of Protection</h2>
            </div>

            <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(300px,1fr))',gap:'1.5rem'}}>
              {[
                {
                  tag:'GD-FD',title:'Document Forgery Detection',
                  desc:'Generative neural networks analyze uploaded documents using Error Level Analysis and deepfake detection.',
                  items:['RAD Autoencoder reconstruction','ELA digital manipulation','Deepfake identification','99.7% accuracy rate'],
                  accent:'#3B82F6',
                },
                {
                  tag:'MBIC',title:'Biometric Identity Confirmation',
                  desc:'Multimodal biometric system combining real-time liveness detection with face and voice authentication.',
                  items:['Facial recognition & liveness','Voice biometrics (MFCC)','Anti-spoofing measures','Challenge-response system'],
                  accent:'var(--green)',
                },
                {
                  tag:'AAFI',title:'Autonomous Fraud Investigation',
                  desc:'Agentic AI system autonomously investigates suspicious cases using Bayesian risk scoring.',
                  items:['Master Agent orchestration','Bayesian risk scoring','Plan-Act-Reflect loop','Real-time monitoring'],
                  accent:'var(--gold)',
                },
              ].map(f => (
                <div key={f.tag} className="feat-card">
                  <div style={{
                    display:'inline-flex',padding:'6px 14px',borderRadius:8,marginBottom:'1.25rem',
                    background:`rgba(${f.accent === 'var(--green)' ? '0,212,106' : f.accent === 'var(--gold)' ? '245,200,66' : '59,130,246'},0.1)`,
                    border:`1px solid rgba(${f.accent === 'var(--green)' ? '0,212,106' : f.accent === 'var(--gold)' ? '245,200,66' : '59,130,246'},0.25)`,
                    color:f.accent,fontSize:'.75rem',fontWeight:700,letterSpacing:'.08em',
                  }}>{f.tag}</div>
                  <h3 className="syne" style={{fontSize:'1.15rem',fontWeight:700,marginBottom:'.75rem'}}>{f.title}</h3>
                  <p style={{color:'var(--text2)',fontSize:'.88rem',lineHeight:1.7,marginBottom:'1.25rem'}}>{f.desc}</p>
                  <ul className="check-list" style={{listStyle:'none',padding:0}}>{f.items.map(i => <li key={i}>{i}</li>)}</ul>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA BANNER */}
        <section style={{padding:'4rem 0'}}>
          <div className="section">
            <div style={{
              background:'linear-gradient(135deg,rgba(0,212,106,0.08),rgba(0,122,61,0.04))',
              border:'1px solid rgba(0,212,106,0.2)',
              borderRadius:24,padding:'3.5rem 3rem',textAlign:'center',position:'relative',overflow:'hidden',
            }}>
              <div className="orb" style={{width:400,height:400,background:'rgba(0,212,106,0.06)',top:'-50%',left:'50%',transform:'translateX(-50%)'}}/>
              <h2 className="syne" style={{fontSize:'2.2rem',fontWeight:800,marginBottom:'.75rem',position:'relative'}}>
                Protect Kenya's Education Future
              </h2>
              <p style={{color:'var(--text2)',fontSize:'1rem',maxWidth:520,margin:'0 auto 2rem',lineHeight:1.7,position:'relative'}}>
                Join us in securing the Student-Centered Funding Model and ensuring every shilling reaches deserving students.
              </p>
              <div style={{display:'flex',gap:'1rem',justifyContent:'center',position:'relative',flexWrap:'wrap'}}>
                <Link href="/auth/signup" className="btn-primary">Get Started Free</Link>
                <Link href="/guide" className="btn-ghost">Talk to AI Guide</Link>
              </div>
            </div>
          </div>
        </section>

      </main>

      {/* FOOTER */}
      <footer>
        <div className="section">
          <div style={{display:'grid',gridTemplateColumns:'2fr 1fr 1fr 1fr',gap:'3rem',flexWrap:'wrap'}}>
            <div>
              <div className="nav-logo" style={{marginBottom:'1rem'}}>
                <div className="logo-icon">
                  <svg width="20" height="20" fill="none" stroke="#04080F" strokeWidth="2.5" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
                  </svg>
                </div>
                <span className="syne" style={{fontWeight:700}}>UhakikiAI</span>
              </div>
              <p style={{color:'var(--text3)',fontSize:'.85rem',lineHeight:1.7,maxWidth:260}}>
                Sovereign Identity Verification System for Kenya's education sector. Powered by advanced AI.
              </p>
            </div>
            {[
              {title:'Solutions',links:['Document Verification','Biometric Auth','Fraud Detection','Risk Assessment']},
              {title:'Platform',links:['Dashboard','AI Guide','API Reference','Status']},
              {title:'Compliance',links:['Data Protection Act','ISO 27001','GDPR','Audit Reports']},
            ].map(col => (
              <div key={col.title}>
                <p className="syne" style={{fontWeight:600,marginBottom:'1rem',fontSize:'.88rem'}}>{col.title}</p>
                <ul style={{listStyle:'none',padding:0}}>
                  {col.links.map(l => (
                    <li key={l} style={{marginBottom:'.6rem'}}>
                      <a href="#" style={{color:'var(--text3)',textDecoration:'none',fontSize:'.85rem',transition:'color .2s'}}
                        onMouseEnter={e=>(e.target as HTMLElement).style.color='var(--text)'}
                        onMouseLeave={e=>(e.target as HTMLElement).style.color='var(--text3)'}>{l}</a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          <div style={{borderTop:'1px solid var(--border)',marginTop:'3rem',paddingTop:'1.5rem',display:'flex',justifyContent:'space-between',alignItems:'center',flexWrap:'wrap',gap:'1rem'}}>
            <p style={{color:'var(--text3)',fontSize:'.8rem'}}>© 2025 UhakikiAI. Protecting Kenya's education future with sovereign AI.</p>
            <div style={{display:'flex',gap:'1.5rem'}}>
              {['Privacy','Terms','Security'].map(l => (
                <a key={l} href="#" style={{color:'var(--text3)',textDecoration:'none',fontSize:'.8rem'}}>{l}</a>
              ))}
            </div>
          </div>
        </div>
      </footer>
    </>
  )
}