// app/purchase/page.tsx

'use client'
import { useState, useEffect } from 'react'

type Price = {
  id: string
  amount: number | null
  currency: string
  productName: string
  productDesc: string | null
  recurring: { interval: string } | null
}

function fmt(amount: number | null, currency: string) {
  if (!amount) return 'Free'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency.toUpperCase(),
    minimumFractionDigits: 2,
  }).format(amount / 100)
}

function getPlanMeta(name: string): {
  tier: string; period: string; days: string; order: number; accent: string; glow: string
} {
  const n = name.toLowerCase()
  if (n.includes('daily')   || n.includes('day'))   return { tier: 'Daily',    period: 'per day',    days: '1 day',   order: 0, accent: '#e87c3e', glow: 'rgba(232,124,62,0.15)'  }
  if (n.includes('weekly')  || n.includes('week'))  return { tier: 'Weekly',   period: 'per week',   days: '7 days',  order: 1, accent: '#9b6dff', glow: 'rgba(155,109,255,0.15)' }
  if (n.includes('monthly') || n.includes('month')) return { tier: 'Monthly',  period: 'per month',  days: '30 days', order: 2, accent: '#3b9eff', glow: 'rgba(59,158,255,0.15)'  }
  if (n.includes('lifetime'))                       return { tier: 'Lifetime', period: 'one time',   days: '∞',       order: 3, accent: '#dc2625', glow: 'rgba(220,38,37,0.2)'    }
  return { tier: name, period: '', days: '', order: 4, accent: '#dc2625', glow: 'rgba(220,38,37,0.15)' }
}

const FEATURES: Record<string, string[]> = {
  Daily:    ['Full access for 24 hours', 'HWID device lock', 'Instant key delivery'],
  Weekly:   ['Full access for 7 days',   'HWID device lock', 'Instant key delivery'],
  Monthly:  ['Full access for 30 days',  'HWID device lock', 'Instant key delivery', 'Priority support'],
  Lifetime: ['Full access forever',       'HWID device lock', 'Instant key delivery', 'All future updates', 'Priority support'],
}

export default function PurchasePage() {
  const [prices, setPrices]   = useState<Price[]>([])
  const [loading, setLoading] = useState(true)
  const [buying, setBuying]   = useState<string | null>(null)
  const [email, setEmail]     = useState('')
  const [error, setError]     = useState('')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    fetch('/api/stripe/prices')
      .then(r => r.json())
      .then(d => {
        const sorted = (Array.isArray(d) ? d : []).sort(
          (a: Price, b: Price) => getPlanMeta(a.productName).order - getPlanMeta(b.productName).order
        )
        setPrices(sorted)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  async function buy(priceId: string) {
    setError('')
    setBuying(priceId)
    try {
      const res = await fetch('/api/stripe/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ priceId, customerEmail: email || undefined }),
      })
      const data = await res.json()
      if (!res.ok || !data.url) { setError(data.error || 'Checkout failed.'); return }
      window.location.href = data.url
    } catch {
      setError('Network error. Please try again.')
    } finally {
      setBuying(null)
    }
  }

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&display=swap');

        .purchase-root {
          min-height: 100vh;
          background: #0a0809;
          font-family: 'DM Sans', sans-serif;
          position: relative;
          overflow: hidden;
        }

        .bg-grid {
          position: fixed;
          inset: 0;
          background-image:
            linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
          background-size: 48px 48px;
          pointer-events: none;
        }

        .bg-noise {
          position: fixed;
          inset: 0;
          opacity: 0.03;
          background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
          pointer-events: none;
        }

        .card-enter {
          opacity: 0;
          transform: translateY(24px);
          animation: cardIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }

        @keyframes cardIn {
          to { opacity: 1; transform: translateY(0); }
        }

        .plan-card {
          position: relative;
          border-radius: 20px;
          padding: 28px;
          display: flex;
          flex-direction: column;
          cursor: default;
          transition: transform 0.25s cubic-bezier(0.16,1,0.3,1), box-shadow 0.25s ease;
        }

        .plan-card:hover {
          transform: translateY(-4px);
        }

        .shimmer-line {
          height: 1px;
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
          margin: 20px 0;
        }

        .buy-btn {
          height: 46px;
          border-radius: 10px;
          font-family: 'Syne', sans-serif;
          font-weight: 700;
          font-size: 14px;
          letter-spacing: 0.5px;
          border: none;
          cursor: pointer;
          width: 100%;
          transition: opacity 0.15s, transform 0.15s;
          position: relative;
          overflow: hidden;
          color: white;
        }

        .buy-btn:hover:not(:disabled) {
          opacity: 0.88;
          transform: scale(0.98);
        }

        .buy-btn:disabled { opacity: 0.4; cursor: not-allowed; }

        .buy-btn::after {
          content: '';
          position: absolute;
          inset: 0;
          background: linear-gradient(180deg, rgba(255,255,255,0.12) 0%, transparent 100%);
          pointer-events: none;
        }

        .feature-item {
          display: flex;
          align-items: center;
          gap: 10px;
          font-size: 13px;
          color: #7a7578;
          padding: 4px 0;
        }

        .feature-dot {
          width: 5px;
          height: 5px;
          border-radius: 50%;
          flex-shrink: 0;
        }

        .email-input {
          height: 46px;
          width: 100%;
          background: rgba(255,255,255,0.04);
          border: 1px solid rgba(255,255,255,0.08);
          border-radius: 10px;
          padding: 0 14px;
          font-size: 14px;
          font-family: 'DM Sans', sans-serif;
          color: #c5c0c2;
          outline: none;
          transition: border-color 0.15s, background 0.15s;
        }

        .email-input:focus {
          border-color: rgba(220,38,37,0.4);
          background: rgba(255,255,255,0.06);
        }

        .email-input::placeholder { color: #3a3537; }

        .popular-ring {
          position: absolute;
          inset: -1px;
          border-radius: 21px;
          background: linear-gradient(135deg, #dc2625, #ff6b6b, #dc2625);
          background-size: 200% 200%;
          animation: ringPulse 3s ease infinite;
          z-index: -1;
        }

        @keyframes ringPulse {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }

        .price-num {
          font-family: 'Syne', sans-serif;
          font-weight: 800;
          line-height: 1;
        }

        .header-title {
          font-family: 'Syne', sans-serif;
          font-weight: 800;
        }
      `}</style>

      <div className="purchase-root">
        <div className="bg-grid" />
        <div className="bg-noise" />

        {/* Ambient glow blobs */}
        <div style={{
          position: 'fixed', top: '-20%', left: '50%', transform: 'translateX(-50%)',
          width: 600, height: 600,
          background: 'radial-gradient(circle, rgba(220,38,37,0.06) 0%, transparent 70%)',
          pointerEvents: 'none',
        }} />

        <div style={{ position: 'relative', zIndex: 1, padding: '72px 24px 80px', maxWidth: 1100, margin: '0 auto' }}>

          {/* Header */}
          <div style={{ textAlign: 'center', marginBottom: 64 }}
               className={mounted ? 'card-enter' : ''}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              padding: '6px 16px', borderRadius: 100,
              background: 'rgba(220,38,37,0.08)',
              border: '1px solid rgba(220,38,37,0.2)',
              marginBottom: 24,
            }}>
              <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#dc2625' }} />
              <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: 2, color: '#dc2625', textTransform: 'uppercase', fontFamily: 'Syne, sans-serif' }}>
                Choose your plan
              </span>
            </div>

            <h1 className="header-title" style={{ fontSize: 52, color: '#f0ecee', margin: '0 0 16px', letterSpacing: -1.5 }}>
              Get Access to<br />
              <span style={{ color: '#dc2625' }}>Passion</span>
            </h1>
            <p style={{ fontSize: 16, color: '#4a4648', maxWidth: 420, margin: '0 auto', lineHeight: 1.6 }}>
              Your key activates the moment you first use it —<br />not when you buy it.
            </p>
          </div>

          {/* Email field */}
          <div style={{ maxWidth: 360, margin: '0 auto 52px' }}
               className={mounted ? 'card-enter' : ''}
               style2={{ animationDelay: '0.1s' }}>
            <label style={{ display: 'block', fontSize: 11, fontWeight: 600, letterSpacing: 1.5, color: '#3a3537', textTransform: 'uppercase', marginBottom: 8, fontFamily: 'Syne, sans-serif' }}>
              Email for key delivery
            </label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com  (optional)"
              className="email-input"
            />
          </div>

          {error && (
            <p style={{ textAlign: 'center', color: '#dc2625', fontSize: 13, marginBottom: 24 }}>{error}</p>
          )}

          {/* Plans */}
          {loading ? (
            <div style={{ textAlign: 'center', padding: '64px 0', color: '#3a3537', fontFamily: 'Syne, sans-serif', letterSpacing: 2, fontSize: 12, textTransform: 'uppercase' }}>
              Loading plans…
            </div>
          ) : prices.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '64px 0', color: '#3a3537' }}>
              No plans configured. <a href="/login" style={{ color: '#dc2625' }}>Admin →</a>
            </div>
          ) : (
            <div style={{
              display: 'grid',
              gridTemplateColumns: `repeat(${Math.min(prices.length, 4)}, 1fr)`,
              gap: 16,
              alignItems: 'start',
            }}>
              {prices.map((p, idx) => {
                const meta     = getPlanMeta(p.productName)
                const isLifetime = meta.tier === 'Lifetime'
                const features  = FEATURES[meta.tier] ?? FEATURES.Monthly
                const delay     = `${idx * 0.08 + 0.15}s`

                return (
                  <div key={p.id}
                       className={`card-enter`}
                       style={{ animationDelay: delay }}>
                    <div
                      className="plan-card"
                      style={{
                        background: isLifetime
                          ? 'linear-gradient(145deg, #1e0f10 0%, #160c0d 100%)'
                          : 'linear-gradient(145deg, #161012 0%, #110d0f 100%)',
                        border: isLifetime ? 'none' : '1px solid rgba(255,255,255,0.05)',
                        boxShadow: isLifetime
                          ? `0 0 0 1px rgba(220,38,37,0.3), 0 24px 64px rgba(0,0,0,0.6), 0 0 40px ${meta.glow}`
                          : '0 8px 32px rgba(0,0,0,0.4)',
                      }}>

                      {isLifetime && <div className="popular-ring" />}

                      {isLifetime && (
                        <div style={{
                          position: 'absolute', top: -12, left: '50%', transform: 'translateX(-50%)',
                          background: '#dc2625',
                          padding: '4px 14px', borderRadius: 100,
                          fontSize: 10, fontWeight: 800, letterSpacing: 2,
                          color: '#fff', textTransform: 'uppercase',
                          fontFamily: 'Syne, sans-serif',
                          whiteSpace: 'nowrap',
                        }}>
                          Best Value
                        </div>
                      )}

                      {/* Plan label */}
                      <div style={{ marginBottom: 20 }}>
                        <div style={{
                          display: 'inline-flex', alignItems: 'center', gap: 6,
                          padding: '4px 10px', borderRadius: 6,
                          background: meta.accent + '18',
                          border: `1px solid ${meta.accent}30`,
                          marginBottom: 12,
                        }}>
                          <div style={{ width: 5, height: 5, borderRadius: '50%', background: meta.accent }} />
                          <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: 1.5, color: meta.accent, textTransform: 'uppercase', fontFamily: 'Syne, sans-serif' }}>
                            {meta.days}
                          </span>
                        </div>

                        <h2 style={{ fontFamily: 'Syne, sans-serif', fontWeight: 700, fontSize: 22, color: '#f0ecee', margin: 0 }}>
                          {meta.tier}
                        </h2>
                      </div>

                      {/* Price */}
                      <div style={{ marginBottom: 4 }}>
                        <span className="price-num" style={{ fontSize: 42, color: '#f0ecee' }}>
                          {fmt(p.amount, p.currency)}
                        </span>
                      </div>
                      <p style={{ fontSize: 12, color: '#3a3537', marginBottom: 0, fontWeight: 500, letterSpacing: 0.5 }}>
                        {meta.period}
                      </p>

                      <div className="shimmer-line" />

                      {/* Features */}
                      <div style={{ flex: 1, marginBottom: 24 }}>
                        {features.map(f => (
                          <div key={f} className="feature-item">
                            <div className="feature-dot" style={{ background: meta.accent }} />
                            {f}
                          </div>
                        ))}
                      </div>

                      {/* CTA */}
                      <button
                        className="buy-btn"
                        onClick={() => buy(p.id)}
                        disabled={buying === p.id}
                        style={{ background: isLifetime ? `linear-gradient(135deg, #dc2625, #b91c1b)` : `linear-gradient(135deg, ${meta.accent}cc, ${meta.accent}99)` }}>
                        {buying === p.id ? 'Redirecting…' : `Get ${meta.tier}`}
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {/* Footer */}
          <div style={{ textAlign: 'center', marginTop: 52 }}>
            <p style={{ fontSize: 12, color: '#2a2527', marginBottom: 8 }}>
              Secured by Stripe · No subscription · Cancel anytime
            </p>
            <a href="/download"
               style={{ fontSize: 12, color: '#2a2527', textDecoration: 'none', transition: 'color 0.15s' }}
               onMouseEnter={e => (e.currentTarget.style.color = '#5d585c')}
               onMouseLeave={e => (e.currentTarget.style.color = '#2a2527')}>
              Already have a key? Download →
            </a>
          </div>

        </div>
      </div>
    </>
  )
}