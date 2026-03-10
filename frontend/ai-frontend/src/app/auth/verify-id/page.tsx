"use client"

import { VerificationStepper } from '@/components/verification'

export default function VerifyIDPage() {
  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

        *{box-sizing:border-box;margin:0;padding:0;}
        :root{
          --bg:#04080F;--surface:#080E1A;
          --green:#00D46A;--green-dim:#007A3D;
          --border:rgba(255,255,255,0.07);--border2:rgba(255,255,255,0.12);
          --text:#F0F4FF;--text2:rgba(240,244,255,0.55);--text3:rgba(240,244,255,0.28);
        }
        body{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;min-height:100vh;}

        .vi-page{
          min-height:100vh;
          background:
            radial-gradient(ellipse 70% 40% at 60% 0%, rgba(0,212,106,0.05) 0%, transparent 70%),
            radial-gradient(ellipse 50% 30% at 10% 80%, rgba(96,165,250,0.04) 0%, transparent 60%),
            linear-gradient(180deg, #04080F 0%, #060C18 100%);
          background-attachment:fixed;
        }

        /* Grid overlay */
        .vi-grid{
          position:fixed;inset:0;pointer-events:none;z-index:0;
          background-image:
            linear-gradient(rgba(0,212,106,0.02) 1px,transparent 1px),
            linear-gradient(90deg,rgba(0,212,106,0.02) 1px,transparent 1px);
          background-size:48px 48px;
        }

        .vi-header{
          position:sticky;top:0;z-index:50;
          background:rgba(4,8,15,0.85);
          backdrop-filter:blur(16px);
          border-bottom:1px solid var(--border);
        }
        .vi-header-inner{
          max-width:900px;margin:0 auto;
          padding:.85rem 1.5rem;
          display:flex;align-items:center;justify-content:space-between;
        }
        .vi-logo{display:flex;align-items:center;gap:.65rem;}
        .vi-logo-icon{
          width:38px;height:38px;border-radius:10px;
          background:linear-gradient(135deg,var(--green),var(--green-dim));
          display:flex;align-items:center;justify-content:center;
          box-shadow:0 4px 16px rgba(0,212,106,0.25);
        }
        .vi-logo-text{font-family:'Syne',sans-serif;font-weight:800;font-size:.95rem;line-height:1.1;}
        .vi-logo-sub{color:var(--text3);font-size:.68rem;letter-spacing:.05em;}
        .vi-status-pill{
          display:flex;align-items:center;gap:.4rem;
          padding:.3rem .85rem;border-radius:100px;
          background:rgba(0,212,106,0.06);border:1px solid rgba(0,212,106,0.2);
          font-size:.72rem;font-weight:600;color:var(--green);
        }
        .vi-status-dot{width:6px;height:6px;border-radius:50%;background:var(--green);animation:vipulse 2s ease-in-out infinite;}
        @keyframes vipulse{0%,100%{opacity:1;}50%{opacity:.3;}}

        .vi-main{
          position:relative;z-index:1;
          max-width:900px;margin:0 auto;
          padding:3rem 1.5rem 5rem;
        }

        /* Hero section */
        .vi-hero{text-align:center;margin-bottom:3rem;}
        .vi-hero-badge{
          display:inline-flex;align-items:center;gap:.5rem;
          padding:.35rem 1rem;border-radius:100px;
          background:rgba(0,212,106,0.06);border:1px solid rgba(0,212,106,0.18);
          font-size:.72rem;font-weight:600;color:var(--green);letter-spacing:.06em;text-transform:uppercase;
          margin-bottom:1.25rem;
        }
        .vi-hero h1{
          font-family:'Syne',sans-serif;font-weight:800;
          font-size:clamp(1.75rem, 4vw, 2.5rem);
          line-height:1.15;margin-bottom:.85rem;
          background:linear-gradient(135deg,#F0F4FF 30%,rgba(0,212,106,0.8));
          -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
        }
        .vi-hero p{
          color:var(--text2);font-size:.95rem;line-height:1.6;
          max-width:500px;margin:0 auto;
        }

        /* Stats row */
        .vi-stats{
          display:grid;grid-template-columns:repeat(3,1fr);gap:.75rem;
          margin-bottom:2.5rem;
        }
        .vi-stat{
          background:rgba(255,255,255,0.02);border:1px solid var(--border);
          border-radius:12px;padding:.85rem 1rem;text-align:center;
        }
        .vi-stat-val{font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:800;color:var(--green);}
        .vi-stat-lbl{font-size:.7rem;color:var(--text3);margin-top:.15rem;}

        /* Footer */
        .vi-footer{
          position:relative;z-index:1;
          border-top:1px solid var(--border);
          background:rgba(4,8,15,0.6);
          padding:1.25rem 1.5rem;
        }
        .vi-footer-inner{
          max-width:900px;margin:0 auto;
          display:flex;align-items:center;justify-content:space-between;
          font-size:.75rem;color:var(--text3);
        }
        .vi-footer-links{display:flex;gap:1.25rem;}
        .vi-footer-links a{color:var(--text3);text-decoration:none;transition:color .2s;}
        .vi-footer-links a:hover{color:var(--text2);}

        @keyframes fadeUp{from{opacity:0;transform:translateY(20px);}to{opacity:1;transform:translateY(0);}}
        .vi-fade-up{animation:fadeUp .5s ease forwards;}
        .vi-fade-up-2{animation:fadeUp .5s .15s ease both;}
        .vi-fade-up-3{animation:fadeUp .5s .3s ease both;}
      `}</style>

      <div className="vi-page">
        <div className="vi-grid" />

        {/* Header */}
        <header className="vi-header">
          <div className="vi-header-inner">
            <div className="vi-logo">
              <div className="vi-logo-icon">
                <svg width="20" height="20" fill="none" stroke="#04080F" strokeWidth="2.5" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
                </svg>
              </div>
              <div>
                <p className="vi-logo-text">UhakikiAI</p>
                <p className="vi-logo-sub">Document Verification</p>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <span style={{ fontSize: '.78rem', color: 'var(--text3)' }}>Secure Verification Portal</span>
              <div className="vi-status-pill">
                <span className="vi-status-dot" />
                System Online
              </div>
            </div>
          </div>
        </header>

        {/* Main */}
        <main className="vi-main">

          {/* Hero */}
          <div className="vi-hero vi-fade-up">
            <div className="vi-hero-badge">
              <svg width="10" height="10" fill="var(--green)" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/></svg>
              AI-Powered Identity Verification
            </div>
            <h1>Identity Document<br/>Verification</h1>
            <p>Upload your official identity document for instant AI-powered authenticity checks, OCR extraction, and fraud detection.</p>
          </div>

          {/* Stats */}
          <div className="vi-stats vi-fade-up-2">
            {[
              { val: '96.8%', lbl: 'Detection Accuracy' },
              { val: '<2s',   lbl: 'Processing Time' },
              { val: '100%',  lbl: 'Encrypted' },
            ].map(s => (
              <div key={s.lbl} className="vi-stat">
                <div className="vi-stat-val">{s.val}</div>
                <div className="vi-stat-lbl">{s.lbl}</div>
              </div>
            ))}
          </div>

          {/* Stepper */}
          <div className="vi-fade-up-3">
            <VerificationStepper />
          </div>
        </main>

        {/* Footer */}
        <footer className="vi-footer">
          <div className="vi-footer-inner">
            <span>© 2024 UhakikiAI. All rights reserved.</span>
            <div className="vi-footer-links">
              <a href="#">Privacy Policy</a>
              <a href="#">Terms of Service</a>
              <a href="#">Support</a>
            </div>
          </div>
        </footer>
      </div>
    </>
  )
}