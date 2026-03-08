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
    minimumFractionDigits: 0,
  }).format(amount / 100)
}

function getDurationLabel(name: string): { label: string; sublabel: string; days: string } {
  const n = name.toLowerCase()
  if (n.includes('daily')   || n.includes('day'))   return { label: 'Daily',    sublabel: 'Renews every day',    days: '1 day'   }
  if (n.includes('weekly')  || n.includes('week'))  return { label: 'Weekly',   sublabel: 'Renews every week',   days: '7 days'  }
  if (n.includes('monthly') || n.includes('month')) return { label: 'Monthly',  sublabel: 'Renews every month',  days: '30 days' }
  if (n.includes('lifetime'))                       return { label: 'Lifetime', sublabel: 'Never expires',       days: '∞'       }
  return { label: name, sublabel: '', days: '' }
}

const PLAN_FEATURES: Record<string, string[]> = {
  daily:    ['License key delivered instantly', 'HWID-lock support', 'Access while active'],
  weekly:   ['License key delivered instantly', 'HWID-lock support', 'Access while active'],
  monthly:  ['License key delivered instantly', 'HWID-lock support', 'Access while active'],
  lifetime: ['License key delivered instantly', 'HWID-lock support', 'All future updates', 'Never expires'],
}

function getFeatures(name: string): string[] {
  const n = name.toLowerCase()
  if (n.includes('daily')   || n.includes('day'))   return PLAN_FEATURES.daily
  if (n.includes('weekly')  || n.includes('week'))  return PLAN_FEATURES.weekly
  if (n.includes('monthly') || n.includes('month')) return PLAN_FEATURES.monthly
  if (n.includes('lifetime'))                       return PLAN_FEATURES.lifetime
  return PLAN_FEATURES.monthly
}

// Sort order: daily → weekly → monthly → lifetime
function planOrder(name: string): number {
  const n = name.toLowerCase()
  if (n.includes('daily')   || n.includes('day'))   return 0
  if (n.includes('weekly')  || n.includes('week'))  return 1
  if (n.includes('monthly') || n.includes('month')) return 2
  if (n.includes('lifetime'))                       return 3
  return 4
}

export default function PurchasePage() {
  const [prices, setPrices]   = useState<Price[]>([])
  const [loading, setLoading] = useState(true)
  const [buying, setBuying]   = useState<string | null>(null)
  const [email, setEmail]     = useState('')
  const [error, setError]     = useState('')

  useEffect(() => {
    fetch('/api/stripe/prices')
      .then(r => r.json())
      .then(d => {
        const sorted = (Array.isArray(d) ? d : []).sort(
          (a: Price, b: Price) => planOrder(a.productName) - planOrder(b.productName)
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
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ priceId, customerEmail: email || undefined }),
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
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-16"
         style={{ background: '#0f0b0c' }}>

      <div className="absolute pointer-events-none"
           style={{
             width: 800, height: 800,
             background: 'radial-gradient(circle, rgba(220,38,37,0.05) 0%, transparent 65%)',
             top: '50%', left: '50%',
             transform: 'translate(-50%, -50%)',
           }} />

      <div className="relative w-full max-w-4xl">
        <div className="text-center mb-10">
          <h1 className="text-[32px] font-bold tracking-tight mb-3"
              style={{ color: '#e5e3e4', textShadow: '0 0 30px rgba(220,38,37,0.3)' }}>
            Passion
          </h1>
          <p className="text-[15px]" style={{ color: '#5d585c' }}>
            Choose a plan. Your key activates the moment you first use it.
          </p>
        </div>

        {/* Email */}
        <div className="mb-8 max-w-sm mx-auto">
          <label className="text-[12px] uppercase tracking-widest block mb-2" style={{ color: '#5d585c' }}>
            Your email (optional — for key delivery)
          </label>
          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="h-[42px] w-full rounded-[8px] px-3 text-[13px] outline-none"
            style={{ background: '#2a2024', border: '1px solid #352c2f', color: '#c5c0c2' }}
            onFocus={e => { e.target.style.borderColor = '#5a4f52' }}
            onBlur={e  => { e.target.style.borderColor = '#352c2f' }}
          />
        </div>

        {error && (
          <p className="text-center text-[13px] mb-6" style={{ color: '#dc2625' }}>{error}</p>
        )}

        {loading ? (
          <div className="text-center py-16" style={{ color: '#5d585c' }}>Loading plans…</div>
        ) : prices.length === 0 ? (
          <div className="text-center py-16" style={{ color: '#5d585c' }}>
            No plans configured yet.{' '}
            <a href="/login" style={{ color: '#dc2625' }}>Admin →</a>
          </div>
        ) : (
          <div className={`grid gap-4 ${
            prices.length <= 2 ? 'max-w-2xl mx-auto grid-cols-' + prices.length :
            prices.length === 3 ? 'grid-cols-3' : 'grid-cols-2 lg:grid-cols-4'
          }`}>
            {prices.map(p => {
              const { label, sublabel, days } = getDurationLabel(p.productName)
              const features  = getFeatures(p.productName)
              const isLifetime = label === 'Lifetime'

              return (
                <div key={p.id}
                     className="rounded-[16px] p-6 relative flex flex-col"
                     style={{
                       background: isLifetime
                         ? 'linear-gradient(180deg,#2a1518 0%,#1f1013 100%)'
                         : 'linear-gradient(180deg,#21161a 0%,#161014 100%)',
                       border: `1px solid ${isLifetime ? '#dc262555' : '#352f31'}`,
                       boxShadow: isLifetime
                         ? '0 0 30px rgba(220,38,37,0.12), 0 12px 40px rgba(0,0,0,0.6)'
                         : '0 8px 30px rgba(0,0,0,0.4)',
                     }}>

                  {isLifetime && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <span className="px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wide"
                            style={{ background: '#dc2625', color: '#fff' }}>
                        Best Value
                      </span>
                    </div>
                  )}

                  {/* Duration badge */}
                  <div className="mb-4">
                    <span className="px-2.5 py-1 rounded-[6px] text-[11px] font-bold uppercase tracking-wide"
                          style={{
                            background: isLifetime ? '#dc262522' : '#2a2024',
                            color: isLifetime ? '#dc2625' : '#5d585c',
                            border: `1px solid ${isLifetime ? '#dc262544' : '#352f31'}`,
                          }}>
                      {days}
                    </span>
                  </div>

                  <h2 className="text-[20px] font-bold mb-1" style={{ color: '#e5e3e4' }}>
                    {label}
                  </h2>
                  <p className="text-[12px] mb-5" style={{ color: '#5d585c' }}>{sublabel}</p>

                  <div className="mb-6">
                    <span className="text-[34px] font-bold" style={{ color: '#e5e3e4' }}>
                      {fmt(p.amount, p.currency)}
                    </span>
                    {!isLifetime && (
                      <span className="text-[13px] ml-1" style={{ color: '#5d585c' }}>
                        /{label.toLowerCase()}
                      </span>
                    )}
                  </div>

                  <ul className="mb-6 space-y-2 flex-1">
                    {features.map(f => (
                      <li key={f} className="flex items-center gap-2 text-[13px]" style={{ color: '#868283' }}>
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#dc2625" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="20 6 9 17 4 12"/>
                        </svg>
                        {f}
                      </li>
                    ))}
                  </ul>

                  <button
                    onClick={() => buy(p.id)}
                    disabled={buying === p.id}
                    className="w-full h-[44px] rounded-[9px] font-bold text-[14px] text-white transition-all disabled:opacity-50 mt-auto"
                    style={{
                      background: '#dc2625',
                      boxShadow: isLifetime ? '0 0 20px rgba(220,38,37,0.4)' : 'none',
                    }}
                    onMouseEnter={e => (e.currentTarget.style.background = '#e83433')}
                    onMouseLeave={e => (e.currentTarget.style.background = '#dc2625')}
                  >
                    {buying === p.id ? 'Redirecting…' : `Get ${label}`}
                  </button>
                </div>
              )
            })}
          </div>
        )}

        <div className="mt-10 text-center">
          <p className="text-[12px] mb-2" style={{ color: '#3a3537' }}>
            ⏱ Your key's timer starts the first time you use it, not when you buy it.
          </p>
          <a href="/download" className="text-[12px]" style={{ color: '#3a3537' }}
             onMouseEnter={e => (e.currentTarget.style.color = '#5d585c')}
             onMouseLeave={e => (e.currentTarget.style.color = '#3a3537')}>
            Already have a key? Download →
          </a>
        </div>
      </div>
    </div>
  )
}