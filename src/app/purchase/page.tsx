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

export default function PurchasePage() {
  const [prices, setPrices]   = useState<Price[]>([])
  const [loading, setLoading] = useState(true)
  const [buying, setBuying]   = useState<string | null>(null)
  const [email, setEmail]     = useState('')
  const [error, setError]     = useState('')

  useEffect(() => {
    fetch('/api/stripe/prices')
      .then(r => r.json())
      .then(d => { setPrices(Array.isArray(d) ? d : []); setLoading(false) })
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

      {/* Glow */}
      <div className="absolute pointer-events-none"
           style={{
             width: 700, height: 700,
             background: 'radial-gradient(circle, rgba(220,38,37,0.05) 0%, transparent 65%)',
             top: '50%', left: '50%',
             transform: 'translate(-50%, -50%)',
           }} />

      <div className="relative w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-[32px] font-bold tracking-tight mb-3"
              style={{ color: '#e5e3e4', textShadow: '0 0 30px rgba(220,38,37,0.3)' }}>
            Passion
          </h1>
          <p className="text-[15px]" style={{ color: '#5d585c' }}>
            Choose a plan and get your license key instantly.
          </p>
        </div>

        {/* Optional email */}
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

        {/* Plans */}
        {loading ? (
          <div className="text-center py-16" style={{ color: '#5d585c' }}>Loading plans…</div>
        ) : prices.length === 0 ? (
          <div className="text-center py-16" style={{ color: '#5d585c' }}>
            No plans configured yet.{' '}
            <a href="/login" style={{ color: '#dc2625' }}>Admin →</a>
          </div>
        ) : (
          <div className={`grid gap-4 ${prices.length === 1 ? 'max-w-sm mx-auto' : 'grid-cols-1 sm:grid-cols-2'}`}>
            {prices.map((p, i) => {
              const isPopular = prices.length > 1 && i === Math.floor(prices.length / 2)
              return (
                <div key={p.id}
                     className="rounded-[16px] p-6 relative"
                     style={{
                       background: isPopular
                         ? 'linear-gradient(180deg,#2a1518 0%,#1f1013 100%)'
                         : 'linear-gradient(180deg,#21161a 0%,#161014 100%)',
                       border: `1px solid ${isPopular ? '#dc262555' : '#352f31'}`,
                       boxShadow: isPopular
                         ? '0 0 30px rgba(220,38,37,0.12), 0 12px 40px rgba(0,0,0,0.6)'
                         : '0 8px 30px rgba(0,0,0,0.4)',
                     }}>

                  {isPopular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <span className="px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wide"
                            style={{ background: '#dc2625', color: '#fff' }}>
                        Most Popular
                      </span>
                    </div>
                  )}

                  <div className="mb-5">
                    <h2 className="text-[17px] font-bold mb-1" style={{ color: '#e5e3e4' }}>
                      {p.productName}
                    </h2>
                    {p.productDesc && (
                      <p className="text-[13px]" style={{ color: '#868283' }}>{p.productDesc}</p>
                    )}
                  </div>

                  <div className="mb-6">
                    <span className="text-[34px] font-bold" style={{ color: '#e5e3e4' }}>
                      {fmt(p.amount, p.currency)}
                    </span>
                    {p.recurring && (
                      <span className="text-[13px] ml-1" style={{ color: '#5d585c' }}>
                        /{p.recurring.interval}
                      </span>
                    )}
                  </div>

                  {/* Features placeholder */}
                  <ul className="mb-6 space-y-2">
                    {['License key delivered instantly', 'HWID-lock support', 'Access to all updates'].map(f => (
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
                    className="w-full h-[44px] rounded-[9px] font-bold text-[14px] text-white transition-all disabled:opacity-50"
                    style={{
                      background: '#dc2625',
                      boxShadow: '0 0 20px rgba(220,38,37,0.35)',
                    }}
                    onMouseEnter={e => (e.currentTarget.style.background = '#e83433')}
                    onMouseLeave={e => (e.currentTarget.style.background = '#dc2625')}
                  >
                    {buying === p.id ? 'Redirecting…' : 'Buy Now'}
                  </button>
                </div>
              )
            })}
          </div>
        )}

        <div className="mt-10 text-center">
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