"use client"

import { useState, useEffect, useRef } from 'react'

interface Message {
  id: string; type: 'user'|'bot'; content: string; timestamp: Date
  category?: 'general'|'verification'|'biometrics'|'security'|'technical'
}

const QUICK = [
  { id:'1', q:'How does ID verification work?', cat:'verification' as const },
  { id:'2', q:'Biometric registration guide', cat:'biometrics' as const },
  { id:'3', q:'Security features overview', cat:'security' as const },
  { id:'4', q:'Troubleshooting common issues', cat:'technical' as const },
  { id:'5', q:'What do account statuses mean?', cat:'general' as const },
  { id:'6', q:'How is my data protected?', cat:'security' as const },
]

const RESPONSES: Record<string, string> = {
  verification: `ID Verification runs 3 layers in under 3 seconds:

1. Error Level Analysis (ELA) — detects pixel-level tampering
2. RAD Autoencoder — reconstructs the document and measures deviation
3. Deepfake classifier — checks for AI-generated manipulations

Confidence scores above 95% are auto-approved. Below that threshold triggers manual review.`,

  biometrics: `Biometric Registration steps:

Face (3 captures, ~15 sec):
• Center your face in the oval guide
• Look straight, keep still per capture
• Tip: natural daylight gives the best results

Voice (5 sec recording):
• Say: "Uhakiki AI verifies my identity"
• Speak clearly at normal pace
• Quiet environment recommended

Data stored as encrypted mathematical templates — never as raw images or audio.`,

  security: `Security architecture has 3 modules:

GD-FD — Document Forgery Detection
• ELA + RAD autoencoder + deepfake nets
• 99.7% accuracy on CASIA dataset

MBIC — Biometric Identity Confirmation  
• Liveness detection + anti-spoofing
• Face + voice fusion scoring

AAFI — Autonomous Fraud Investigation
• Bayesian risk scorer
• Plan-Act-Reflect agentic loop
• Real-time pattern matching`,

  technical: `Common issues and fixes:

Camera won't start:
→ Grant permission in browser settings
→ Close other apps using the camera
→ Try a different browser (Chrome recommended)

Verification keeps failing:
→ Use bright, even lighting (avoid flash)
→ Place ID flat on a dark background
→ Capture all 4 corners in frame

Account stuck on Pending:
→ Complete biometric registration
→ Check email for any required action

Still stuck? Contact support@uhakiki.ai`,

  general: `Account status meanings:

ACTIVE ✓
All verification steps complete. Full access to all features and highest security level.

PENDING ⚡
ID verified but biometrics not yet registered. Limited feature access. Complete biometrics to upgrade.

INCOMPLETE ✗
Registration process not finished. Very limited access. Must complete verification steps.

Upgrade path: Sign up → Verify ID → Register biometrics → Status becomes ACTIVE`,

  privacy: `Data protection at UhakikiAI:

Collection: Only what's necessary for verification. No unnecessary data.

Storage: AES-256 encrypted. Biometric templates only — not raw images or recordings.

Retention: Auto-deleted after 2 years of inactivity.

Compliance: Kenya Data Protection Act 2019 + GDPR.

Your rights: Access, correct, export, or delete your data anytime via Profile Settings.`,
}

function getResponse(input: string): { text: string; cat: Message['category'] } {
  const t = input.toLowerCase()
  if (t.includes('verif') || t.includes('id') || t.includes('document')) return { text: RESPONSES.verification, cat: 'verification' }
  if (t.includes('biomet') || t.includes('face') || t.includes('voice')) return { text: RESPONSES.biometrics, cat: 'biometrics' }
  if (t.includes('secur') || t.includes('protect') || t.includes('safe')) return { text: RESPONSES.security, cat: 'security' }
  if (t.includes('trouble') || t.includes('problem') || t.includes('issue') || t.includes('error') || t.includes('camera')) return { text: RESPONSES.technical, cat: 'technical' }
  if (t.includes('status') || t.includes('pending') || t.includes('active')) return { text: RESPONSES.general, cat: 'general' }
  if (t.includes('privacy') || t.includes('data') || t.includes('gdpr')) return { text: RESPONSES.privacy, cat: 'security' }
  return {
    text: `I can help with:\n• ID verification process\n• Biometric registration\n• Security features\n• Troubleshooting\n• Account status\n• Privacy & data protection\n\nTry asking me a specific question or pick one of the quick actions below.`,
    cat: 'general'
  }
}

export default function AIGuide() {
  const [msgs, setMsgs] = useState<Message[]>([{
    id:'0', type:'bot', content:"Hello! I'm your UhakikiAI Guide. Ask me anything about identity verification, biometrics, security, or your account.\n\nHow can I help you today?",
    timestamp: new Date(), category:'general'
  }])
  const [input, setInput] = useState('')
  const [typing, setTyping] = useState(false)
  const [recording, setRecording] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)
  const mediaRef = useRef<MediaRecorder | null>(null)

  useEffect(() => { endRef.current?.scrollIntoView({ behavior:'smooth' }) }, [msgs])

  const send = (text: string) => {
    if (!text.trim()) return
    const user: Message = { id: Date.now().toString(), type:'user', content:text, timestamp:new Date() }
    setMsgs(p => [...p, user])
    setInput('')
    setTyping(true)
    setTimeout(() => {
      const { text: txt, cat } = getResponse(text)
      const bot: Message = { id:(Date.now()+1).toString(), type:'bot', content:txt, timestamp:new Date(), category:cat }
      setMsgs(p => [...p, bot])
      setTyping(false)
    }, 1200)
  }

  const startVoice = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio:true })
      const mr = new MediaRecorder(stream)
      mediaRef.current = mr
      mr.start(); setRecording(true)
      setTimeout(() => { if (mr.state==='recording') { mr.stop(); stream.getTracks().forEach(t=>t.stop()); setRecording(false) } }, 5000)
    } catch(e) { console.error(e) }
  }

  const CAT_COLOR: Record<string, string> = {
    verification:'#3B82F6', biometrics:'#00D46A', security:'#F5C842', technical:'#FF4D4D', general:'#A78BFA'
  }

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');
        *{box-sizing:border-box;margin:0;padding:0;}
        :root{
          --bg:#04080F;--surface:#080E1A;--surface2:#0C1524;
          --green:#00D46A;--border:rgba(255,255,255,0.07);--border2:rgba(255,255,255,0.12);
          --text:#F0F4FF;--text2:rgba(240,244,255,0.55);--text3:rgba(240,244,255,0.28);
        }
        body{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;height:100vh;display:flex;flex-direction:column;}
        .syne{font-family:'Syne',sans-serif;}
        .mono{font-family:'DM Mono',monospace;}
        nav{
          display:flex;align-items:center;justify-content:space-between;padding:.9rem 2rem;
          background:rgba(4,8,15,0.95);backdrop-filter:blur(16px);
          border-bottom:1px solid var(--border);flex-shrink:0;
        }
        .logo-icon{width:34px;height:34px;border-radius:9px;background:linear-gradient(135deg,#00D46A,#007A3D);display:flex;align-items:center;justify-content:center;}
        .layout{display:flex;flex:1;overflow:hidden;}
        aside{
          width:260px;flex-shrink:0;border-right:1px solid var(--border);
          background:var(--surface);padding:1.5rem 1.25rem;overflow-y:auto;display:flex;flex-direction:column;gap:1rem;
        }
        .quick-btn{
          width:100%;text-align:left;background:rgba(255,255,255,0.02);border:1px solid var(--border);
          border-radius:10px;padding:.75rem 1rem;cursor:pointer;
          color:var(--text2);font-family:'DM Sans',sans-serif;font-size:.83rem;line-height:1.4;
          transition:background .2s,border-color .2s,color .2s;
        }
        .quick-btn:hover{background:rgba(255,255,255,0.05);border-color:var(--border2);color:var(--text);}
        .chat-area{flex:1;display:flex;flex-direction:column;overflow:hidden;}
        .messages{flex:1;overflow-y:auto;padding:1.5rem;display:flex;flex-direction:column;gap:1rem;}
        .messages::-webkit-scrollbar{width:4px;}
        .messages::-webkit-scrollbar-track{background:transparent;}
        .messages::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.08);border-radius:4px;}
        .bot-msg{
          display:flex;gap:10px;max-width:680px;align-self:flex-start;
        }
        .bot-bubble{
          background:var(--surface2);border:1px solid var(--border);
          border-radius:0 12px 12px 12px;padding:1rem 1.25rem;
          color:var(--text);font-size:.88rem;line-height:1.7;white-space:pre-line;
          border-left:2px solid var(--green);
        }
        .user-msg{align-self:flex-end;display:flex;flex-direction:column;align-items:flex-end;max-width:540px;}
        .user-bubble{
          background:linear-gradient(135deg,rgba(0,212,106,0.15),rgba(0,122,61,0.1));
          border:1px solid rgba(0,212,106,0.2);
          border-radius:12px 12px 0 12px;padding:.8rem 1.1rem;
          color:var(--text);font-size:.88rem;line-height:1.6;
        }
        .ts{color:var(--text3);font-size:.7rem;margin-top:.3rem;}
        .bot-icon{width:32px;height:32px;border-radius:50%;background:rgba(0,212,106,0.1);border:1px solid rgba(0,212,106,0.2);display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:2px;}
        .typing{display:flex;gap:4px;align-items:center;padding:.75rem 1rem;}
        .dot{width:6px;height:6px;border-radius:50%;background:var(--green);opacity:.4;}
        .dot:nth-child(1){animation:blink 1.2s .0s infinite;}
        .dot:nth-child(2){animation:blink 1.2s .2s infinite;}
        .dot:nth-child(3){animation:blink 1.2s .4s infinite;}
        @keyframes blink{0%,100%{opacity:.2;}50%{opacity:1;}}
        .input-bar{
          border-top:1px solid var(--border);padding:1rem 1.5rem;
          display:flex;align-items:center;gap:.75rem;background:var(--surface);flex-shrink:0;
        }
        .msg-input{
          flex:1;background:rgba(255,255,255,0.04);border:1px solid var(--border2);
          border-radius:10px;padding:.7rem 1rem;color:var(--text);
          font-family:'DM Sans',sans-serif;font-size:.9rem;outline:none;
          transition:border-color .2s,box-shadow .2s;
        }
        .msg-input:focus{border-color:var(--green);box-shadow:0 0 0 3px rgba(0,212,106,0.08);}
        .msg-input::placeholder{color:var(--text3);}
        .icon-btn{background:none;border:none;cursor:pointer;color:var(--text2);padding:.5rem;border-radius:8px;transition:background .2s,color .2s;display:flex;align-items:center;}
        .icon-btn:hover{background:rgba(255,255,255,0.06);color:var(--text);}
        .send-btn{
          background:var(--green);border:none;border-radius:10px;padding:.6rem .9rem;cursor:pointer;
          display:flex;align-items:center;justify-content:center;
          transition:opacity .2s,transform .2s,box-shadow .2s;
        }
        .send-btn:hover:not(:disabled){opacity:.9;transform:translateY(-1px);box-shadow:0 4px 16px rgba(0,212,106,0.3);}
        .send-btn:disabled{opacity:.35;cursor:not-allowed;}
        @keyframes fadeIn{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:translateY(0);}}
        .fade-in{animation:fadeIn .3s ease forwards;}
      `}</style>

      <nav>
        <div style={{display:'flex',alignItems:'center',gap:10}}>
          <div className="logo-icon">
            <svg width="18" height="18" fill="none" stroke="#04080F" strokeWidth="2.5" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
            </svg>
          </div>
          <span className="syne" style={{fontWeight:700,fontSize:'1rem'}}>UhakikiAI Guide</span>
          <span style={{
            marginLeft:4,padding:'2px 10px',borderRadius:100,
            background:'rgba(0,212,106,0.1)',border:'1px solid rgba(0,212,106,0.2)',
            color:'var(--green)',fontSize:'.7rem',fontWeight:600,
          }}>ONLINE</span>
        </div>
        <span style={{color:'var(--text3)',fontSize:'.78rem'}}>AI-powered • Available 24/7 • Privacy protected</span>
      </nav>

      <div className="layout">
        {/* Sidebar quick actions */}
        <aside>
          <p className="syne" style={{fontWeight:700,fontSize:'.85rem',color:'var(--text2)',textTransform:'uppercase',letterSpacing:'.08em'}}>
            Quick Topics
          </p>
          {QUICK.map(q => (
            <button key={q.id} className="quick-btn" onClick={() => send(q.q)}>
              <span style={{
                display:'inline-block',width:6,height:6,borderRadius:'50%',
                background: CAT_COLOR[q.cat] || 'var(--green)',
                marginRight:8,verticalAlign:'middle',
              }}/>
              {q.q}
            </button>
          ))}

          <div style={{marginTop:'auto',paddingTop:'1rem',borderTop:'1px solid var(--border)'}}>
            <p style={{color:'var(--text3)',fontSize:'.75rem',lineHeight:1.6}}>
              Your conversations are private and encrypted. UhakikiAI does not store chat history.
            </p>
          </div>
        </aside>

        {/* Chat */}
        <div className="chat-area">
          <div className="messages">
            {msgs.map(m => (
              <div key={m.id} className={`fade-in ${m.type === 'bot' ? 'bot-msg' : 'user-msg'}`}>
                {m.type === 'bot' && (
                  <div className="bot-icon">
                    <svg width="14" height="14" fill="none" stroke="var(--green)" strokeWidth="2" viewBox="0 0 24 24">
                      <path d="M12 2a2 2 0 012 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 017 7H3a7 7 0 017-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 012-2z"/>
                      <path d="M3 13h18M3 17h18"/>
                      <circle cx="8" cy="13" r="1" fill="var(--green)"/>
                      <circle cx="16" cy="13" r="1" fill="var(--green)"/>
                    </svg>
                  </div>
                )}
                <div>
                  {m.category && m.type === 'bot' && (
                    <span style={{
                      display:'inline-block',fontSize:'.68rem',fontWeight:600,
                      padding:'1px 8px',borderRadius:100,marginBottom:'.4rem',
                      background:`${CAT_COLOR[m.category] || 'var(--green)'}15`,
                      color:CAT_COLOR[m.category] || 'var(--green)',
                      border:`1px solid ${CAT_COLOR[m.category] || 'var(--green)'}30`,
                      textTransform:'uppercase',letterSpacing:'.06em',
                    }}>{m.category}</span>
                  )}
                  <div className={m.type === 'bot' ? 'bot-bubble' : 'user-bubble'}>
                    {m.content}
                  </div>
                  <p className="ts">{m.timestamp.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}</p>
                </div>
              </div>
            ))}

            {typing && (
              <div className="bot-msg fade-in">
                <div className="bot-icon">
                  <svg width="14" height="14" fill="none" stroke="var(--green)" strokeWidth="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>
                </div>
                <div className="bot-bubble">
                  <div className="typing">
                    <div className="dot"/><div className="dot"/><div className="dot"/>
                  </div>
                </div>
              </div>
            )}
            <div ref={endRef}/>
          </div>

          {/* Input */}
          <div className="input-bar">
            <button className={`icon-btn ${recording ? 'recording' : ''}`} onClick={startVoice}
              style={recording ? {color:'#FF4D4D',animation:'blink 1s infinite'} : {}}>
              <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"/>
                <path d="M19 10v2a7 7 0 01-14 0v-2"/>
                <line x1="12" y1="19" x2="12" y2="23"/>
                <line x1="8" y1="23" x2="16" y2="23"/>
              </svg>
            </button>
            <input
              className="msg-input"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input) } }}
              placeholder="Ask me anything about UhakikiAI..."
            />
            <button className="send-btn" onClick={() => send(input)} disabled={!input.trim()}>
              <svg width="16" height="16" fill="none" stroke="#04080F" strokeWidth="2.5" viewBox="0 0 24 24">
                <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </>
  )
}