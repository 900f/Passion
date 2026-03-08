// app/purchase/page.tsx

'use client'
import { useState, useEffect } from 'react'

type Price = {
  id: string
  amount: number | null
  currency: string
  productName: string
  productDesc: string | null
}

function fmt(amount: number | null, currency: string) {
  if (!amount) return 'Free'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency.toUpperCase(),
    minimumFractionDigits: 2,
  }).format(amount / 100)
}

function getPlanMeta(name: string): { tier: string; days: string; order: number; accent: string } {
  const n = name.toLowerCase()
  if (n.includes('daily')   || n.includes('day'))   return { tier: 'Daily',    days: '1 day',   order: 0, accent: '#e87c3e' }
  if (n.includes('weekly')  || n.includes('week'))  return { tier: 'Weekly',   days: '7 days',  order: 1, accent: '#9b6dff' }
  if (n.includes('monthly') || n.includes('month')) return { tier: 'Monthly',  days: '30 days', order: 2, accent: '#3b9eff' }
  if (n.includes('lifetime'))                       return { tier: 'Lifetime', days: '∞',       order: 3, accent: '#dc2625' }
  return { tier: name, days: '', order: 4, accent: '#dc2625' }
}

export default function PurchasePage() {
  const [prices, setPrices]       = useState<Price[]>([])
  const [loading, setLoading]     = useState(true)
  const [buying, setBuying]       = useState(false)
  const [email, setEmail]         = useState('')
  const [selectedId, setSelected] = useState('')
  const [error, setError]         = useState('')
  const [mounted, setMounted]     = useState(false)

  useEffect(() => {
    setMounted(true)
    fetch('/api/stripe/prices')
      .then(r => r.json())
      .then(d => {
        const sorted = (Array.isArray(d) ? d : []).sort(
          (a: Price, b: Price) => getPlanMeta(a.productName).order - getPlanMeta(b.productName).order
        )
        setPrices(sorted)
        if (sorted.length > 0) setSelected(sorted[0].id)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  const selected = prices.find(p => p.id === selectedId)
  const meta     = selected ? getPlanMeta(selected.productName) : null

  async function buy() {
    if (!selectedId) return
    if (!email.trim()) { setError("Please enter your email address."); return }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) { setError("Please enter a valid email address."); return }
    setError("")
    setBuying(true)
    try {
      const res = await fetch("/api/stripe/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ priceId: selectedId, customerEmail: email.trim() }),
      })
      const data = await res.json()
      if (!res.ok || !data.url) { setError(data.error || "Checkout failed."); return }
      window.location.href = data.url
    } catch {
      setError("Network error. Please try again.")
    } finally {
      setBuying(false)
    }
  }

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500&display=swap');
        * { box-sizing: border-box; }

        .pur-root {
          min-height: 100vh;
          background: #0a0809;
          font-family: 'DM Sans', sans-serif;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 32px 20px;
          position: relative;
          overflow: hidden;
        }
        .pur-grid {
          position: fixed; inset: 0;
          background-image:
            linear-gradient(rgba(255,255,255,0.018) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.018) 1px, transparent 1px);
          background-size: 52px 52px;
          pointer-events: none;
        }
        .pur-glow {
          position: fixed;
          width: 700px; height: 700px;
          top: 50%; left: 50%;
          transform: translate(-50%, -50%);
          background: radial-gradient(circle, rgba(220,38,37,0.055) 0%, transparent 65%);
          pointer-events: none;
        }
        .pur-card {
          position: relative; z-index: 1;
          display: grid;
          grid-template-columns: 1fr 1fr;
          width: 100%;
          max-width: 920px;
          border-radius: 24px;
          overflow: hidden;
          border: 1px solid rgba(255,255,255,0.06);
          box-shadow: 0 32px 80px rgba(0,0,0,0.7), 0 0 0 1px rgba(220,38,37,0.06);
          opacity: 0;
          transform: translateY(20px);
          animation: fadeUp 0.55s cubic-bezier(0.16,1,0.3,1) 0.05s forwards;
        }
        @keyframes fadeUp {
          to { opacity: 1; transform: translateY(0); }
        }

        /* LEFT panel */
        .pur-visual {
          background: linear-gradient(145deg, #130e10 0%, #0d090a 100%);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 48px 36px;
          position: relative;
          overflow: hidden;
          gap: 32px;
        }

        /* subtle red vignette in corners */
        .pur-visual::before {
          content: '';
          position: absolute; inset: 0;
          background: radial-gradient(ellipse at 50% 110%, rgba(220,38,37,0.1) 0%, transparent 60%);
          pointer-events: none;
        }

        .corner {
          position: absolute;
          width: 36px; height: 36px;
          border-color: rgba(220,38,37,0.18);
          border-style: solid;
        }
        .corner-tl { top: 18px; left: 18px; border-width: 1px 0 0 1px; border-radius: 3px 0 0 0; }
        .corner-tr { top: 18px; right: 18px; border-width: 1px 1px 0 0; border-radius: 0 3px 0 0; }
        .corner-bl { bottom: 18px; left: 18px; border-width: 0 0 1px 1px; border-radius: 0 0 0 3px; }
        .corner-br { bottom: 18px; right: 18px; border-width: 0 1px 1px 0; border-radius: 0 0 3px 0; }

        .pur-visual-text { text-align: center; position: relative; z-index: 1; }

        .pur-badge {
          display: inline-flex; align-items: center; gap: 7px;
          padding: 5px 13px; border-radius: 100px;
          background: rgba(220,38,37,0.08);
          border: 1px solid rgba(220,38,37,0.2);
          margin-bottom: 16px;
        }
        .pur-badge-dot {
          width: 6px; height: 6px; border-radius: 50%;
          background: #dc2625;
          box-shadow: 0 0 8px rgba(220,38,37,0.8);
          animation: blink 2s ease infinite;
        }
        @keyframes blink {
          0%,100% { opacity: 1; } 50% { opacity: 0.25; }
        }
        .pur-badge span {
          font-size: 10px; font-weight: 700; letter-spacing: 2px;
          color: #dc2625; text-transform: uppercase; font-family: 'Syne', sans-serif;
        }
        .pur-visual-title {
          font-family: 'Syne', sans-serif;
          font-weight: 800; font-size: 30px;
          color: #f2eef0; margin: 0 0 10px;
          letter-spacing: -0.8px; line-height: 1.15;
        }
        .pur-visual-sub {
          font-size: 13px; color: #3a3537;
          margin: 0; line-height: 1.6;
        }

        /* screenshot mockup */
        .pur-mockup-wrap {
          position: relative; z-index: 1;
          width: 100%;
          max-width: 320px;
        }

        /* outer chrome frame */
        .pur-mockup-frame {
          background: #1a1318;
          border-radius: 14px;
          border: 1px solid rgba(255,255,255,0.08);
          overflow: hidden;
          box-shadow:
            0 0 0 1px rgba(220,38,37,0.1),
            0 20px 60px rgba(0,0,0,0.8),
            0 4px 16px rgba(220,38,37,0.08);
        }

        /* fake window bar */
        .pur-mockup-bar {
          height: 32px;
          background: #110d0f;
          border-bottom: 1px solid rgba(255,255,255,0.05);
          display: flex;
          align-items: center;
          padding: 0 12px;
          gap: 6px;
        }
        .mockup-dot {
          width: 8px; height: 8px; border-radius: 50%;
        }

        /* the actual screenshot */
        .pur-mockup-img {
          display: block;
          width: 100%;
          height: auto;
          max-height: 280px;
          object-fit: cover;
          object-position: top;
        }

        /* reflection under frame */
        .pur-mockup-reflection {
          height: 40px;
          background: linear-gradient(to bottom, rgba(220,38,37,0.04), transparent);
          margin: 0 10px;
          border-radius: 0 0 10px 10px;
          filter: blur(8px);
        }

        /* RIGHT — form */
        .pur-form {
          background: linear-gradient(160deg, #161012 0%, #0f0c0d 100%);
          padding: 44px 40px;
          display: flex;
          flex-direction: column;
          justify-content: center;
        }
        .pur-form-title {
          font-family: 'Syne', sans-serif;
          font-weight: 700; font-size: 22px;
          color: #f0ecee; margin: 0 0 6px;
        }
        .pur-form-sub {
          font-size: 13px; color: #3a3537;
          margin: 0 0 32px; line-height: 1.5;
        }
        .pur-label {
          display: block;
          font-size: 10px; font-weight: 700; letter-spacing: 1.5px;
          color: #3a3537; text-transform: uppercase;
          font-family: 'Syne', sans-serif; margin-bottom: 8px;
        }
        .pur-input {
          height: 48px; width: 100%;
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.07);
          border-radius: 10px;
          padding: 0 14px;
          font-size: 14px; font-family: 'DM Sans', sans-serif;
          color: #c5c0c2; outline: none;
          transition: border-color 0.15s, background 0.15s;
          margin-bottom: 20px;
        }
        .pur-input:focus {
          border-color: rgba(220,38,37,0.35);
          background: rgba(255,255,255,0.05);
        }
        .pur-input::placeholder { color: #2e292c; }

        .pur-select-wrap { position: relative; margin-bottom: 20px; }
        .pur-select {
          height: 48px; width: 100%;
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.07);
          border-radius: 10px;
          padding: 0 40px 0 14px;
          font-size: 14px; font-family: 'DM Sans', sans-serif;
          color: #c5c0c2; outline: none;
          appearance: none; cursor: pointer;
          transition: border-color 0.15s, background 0.15s;
          color-scheme: dark;
        }
        .pur-select:focus {
          border-color: rgba(220,38,37,0.35);
          background: rgba(255,255,255,0.05);
        }
        .pur-select-arrow {
          position: absolute; right: 14px; top: 50%;
          transform: translateY(-50%);
          pointer-events: none; color: #3a3537;
        }

        /* plan preview strip */
        .pur-preview {
          display: flex; align-items: center; justify-content: space-between;
          padding: 13px 16px;
          background: rgba(255,255,255,0.02);
          border-radius: 10px;
          margin-bottom: 24px;
          transition: border-color 0.2s;
          border: 1px solid rgba(255,255,255,0.04);
        }
        .pur-preview-left { display: flex; align-items: center; gap: 10px; }
        .pur-preview-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
        .pur-preview-name {
          font-family: 'Syne', sans-serif;
          font-weight: 700; font-size: 14px; color: #e5e3e4;
        }
        .pur-preview-days { font-size: 11px; color: #3a3537; margin-top: 1px; }
        .pur-preview-price {
          font-family: 'Syne', sans-serif;
          font-weight: 800; font-size: 20px; color: #f0ecee;
        }

        .pur-btn {
          height: 50px; width: 100%;
          background: linear-gradient(135deg, #dc2625, #b91c1b);
          border: none; border-radius: 12px;
          font-family: 'Syne', sans-serif;
          font-weight: 700; font-size: 15px;
          color: white; cursor: pointer;
          position: relative; overflow: hidden;
          transition: opacity 0.15s, transform 0.15s;
          box-shadow: 0 0 24px rgba(220,38,37,0.28);
        }
        .pur-btn::after {
          content: ''; position: absolute; inset: 0;
          background: linear-gradient(180deg, rgba(255,255,255,0.1) 0%, transparent 60%);
          pointer-events: none;
        }
        .pur-btn:hover:not(:disabled) { opacity: 0.88; transform: scale(0.99); }
        .pur-btn:disabled { opacity: 0.4; cursor: not-allowed; }

        .pur-divider {
          height: 1px;
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.05), transparent);
          margin: 22px 0;
        }
        .pur-trust {
          display: flex; align-items: center; justify-content: center;
          gap: 18px; flex-wrap: wrap;
        }
        .pur-trust-item {
          display: flex; align-items: center; gap: 5px;
          font-size: 11px; color: #2a2527;
        }
        .pur-error { font-size: 12px; color: #dc2625; margin-bottom: 12px; text-align: center; }

        @media (max-width: 680px) {
          .pur-card { grid-template-columns: 1fr; }
          .pur-visual { padding: 36px 28px; }
          .pur-form { padding: 32px 28px; }
        }
      `}</style>

      <div className="pur-root">
        <div className="pur-grid" />
        <div className="pur-glow" />

        <div className="pur-card">

          {/* LEFT — visual with mockup */}
          <div className="pur-visual">
            <div className="corner corner-tl" />
            <div className="corner corner-tr" />
            <div className="corner corner-bl" />
            <div className="corner corner-br" />

            {/* Text */}
            <div className="pur-visual-text">
              <div className="pur-badge">
                <div className="pur-badge-dot" />
                <span>Instant delivery</span>
              </div>
              <h1 className="pur-visual-title">Passion</h1>
              <p className="pur-visual-sub">
                Timer starts the moment<br />you first activate your key.
              </p>
            </div>

            {/* Mockup screenshot */}
            <div className="pur-mockup-wrap">
              <div className="pur-mockup-frame">
                {/* fake window chrome */}
                <div className="pur-mockup-bar">
                  <div className="mockup-dot" style={{ background: '#ff5f57' }} />
                  <div className="mockup-dot" style={{ background: '#febc2e' }} />
                  <div className="mockup-dot" style={{ background: '#28c840' }} />
                </div>
                {/*
                  Replace /preview.png with a screenshot of your menu/UI.
                  Drop the image into your /public folder.
                */}
                <img
                  src="/preview.png"
                  alt="Passion preview"
                  className="pur-mockup-img"
                  onError={e => {
                    // fallback placeholder if image not found
                    const t = e.currentTarget
                    t.style.display = 'none'
                    const placeholder = t.nextElementSibling as HTMLElement
                    if (placeholder) placeholder.style.display = 'flex'
                  }}
                />
                {/* placeholder shown if no image */}
                <div style={{
                  display: 'none', height: 220,
                  alignItems: 'center', justifyContent: 'center',
                  flexDirection: 'column', gap: 8,
                  background: '#0f0b0c',
                }}>
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#2a2527" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>
                  </svg>
                  <span style={{ fontSize: 11, color: '#2a2527', fontFamily: 'Syne, sans-serif', letterSpacing: 1 }}>
                    Add /preview.png to /public
                  </span>
                </div>
              </div>
              <div className="pur-mockup-reflection" />
            </div>
          </div>

          {/* RIGHT — form */}
          <div className="pur-form">
            <p className="pur-form-title">Get your license</p>
            <p className="pur-form-sub">One-time payment · No subscription</p>

            <label className="pur-label">Email address <span style={{color:"#dc2625"}}>*</span></label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com  (required)"
              className="pur-input"
            />

            <label className="pur-label">Plan</label>
            {loading ? (
              <div className="pur-input" style={{ display: 'flex', alignItems: 'center', color: '#2e292c', fontSize: 13, marginBottom: 20 }}>
                Loading plans…
              </div>
            ) : (
              <div className="pur-select-wrap">
                <select
                  value={selectedId}
                  onChange={e => setSelected(e.target.value)}
                  className="pur-select">
                  {prices.map(p => {
                    const m = getPlanMeta(p.productName)
                    return (
                      <option key={p.id} value={p.id}>
                        {m.tier}  ·  {m.days}  ·  {fmt(p.amount, p.currency)}
                      </option>
                    )
                  })}
                </select>
                <svg className="pur-select-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </div>
            )}

            {/* Selected plan preview */}
            {selected && meta && (
              <div className="pur-preview" style={{ borderColor: meta.accent + '22' }}>
                <div className="pur-preview-left">
                  <div className="pur-preview-dot" style={{ background: meta.accent, boxShadow: `0 0 8px ${meta.accent}66` }} />
                  <div>
                    <div className="pur-preview-name">{meta.tier}</div>
                    <div className="pur-preview-days">{meta.days} · timer starts on first use</div>
                  </div>
                </div>
                <div className="pur-preview-price">{fmt(selected.amount, selected.currency)}</div>
              </div>
            )}

            {error && <p className="pur-error">{error}</p>}

            <button className="pur-btn" onClick={buy} disabled={buying || !selectedId || loading || !email.trim()}>
              {buying ? 'Redirecting to Stripe…' : 'Buy Now →'}
            </button>

            <div className="pur-divider" />

            <div className="pur-trust">
              <div className="pur-trust-item">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                Secured by Stripe
              </div>
              <div className="pur-trust-item">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                Instant key delivery
              </div>
              <div className="pur-trust-item">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                Timer on activation
              </div>
            </div>

            <div style={{ textAlign: 'center', marginTop: 18 }}>
              <a href="/download"
                 style={{ fontSize: 11, color: '#2a2527', textDecoration: 'none' }}
                 onMouseEnter={e => (e.currentTarget.style.color = '#5d585c')}
                 onMouseLeave={e => (e.currentTarget.style.color = '#2a2527')}>
                Already have a key? Download →
              </a>
            </div>
          </div>

        </div>
      </div>
    </>
  )
}