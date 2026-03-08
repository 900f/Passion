// app/dashboard/purchases/page.tsx

'use client'
import { useState, useEffect, useCallback } from 'react'

type Purchase = {
  id: number
  stripe_session_id: string
  stripe_payment_intent: string | null
  customer_email: string | null
  amount_total: number
  currency: string
  keys_created: number
  created_at: string
}

function fmt(amount: number, currency: string) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency.toUpperCase(),
    minimumFractionDigits: 2,
  }).format(amount / 100)
}

export default function PurchasesPage() {
  const [purchases, setPurchases] = useState<Purchase[]>([])
  const [loading, setLoading]     = useState(true)
  const [search, setSearch]       = useState('')
  const [total, setTotal]         = useState(0)

  const load = useCallback(async () => {
    setLoading(true)
    const p = new URLSearchParams()
    if (search) p.set('q', search)
    const r = await fetch('/api/purchases?' + p)
    const data: Purchase[] = await r.json()
    setPurchases(data)
    // Sum revenue
    const sum = data.reduce((acc, d) => acc + (d.amount_total ?? 0), 0)
    setTotal(sum)
    setLoading(false)
  }, [search])

  useEffect(() => { load() }, [load])

  const inputSt = { background: '#2a2024', border: '1px solid #352c2f', color: '#c5c0c2' }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-[22px] font-bold" style={{ color: '#e5e3e4' }}>Purchases</h1>
          <p className="text-[13px] mt-0.5" style={{ color: '#5d585c' }}>
            {purchases.length} orders
            {purchases.length > 0 && (
              <span className="ml-2" style={{ color: '#868283' }}>
                · {fmt(total, purchases[0]?.currency ?? 'usd')} total
              </span>
            )}
          </p>
        </div>
        <a href="https://dashboard.stripe.com" target="_blank" rel="noreferrer"
           className="h-[36px] px-4 rounded-[8px] text-[12px] font-semibold flex items-center gap-2"
           style={{ background: '#2a2024', color: '#868283', border: '1px solid #352c2f' }}
           onMouseEnter={e => (e.currentTarget.style.color = '#e5e3e4')}
           onMouseLeave={e => (e.currentTarget.style.color = '#868283')}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
          </svg>
          Stripe Dashboard
        </a>
      </div>

      {/* Search */}
      <div className="mb-5">
        <input
          placeholder="Search by email or session ID…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="h-[36px] rounded-[7px] px-3 text-[13px] outline-none max-w-xs w-full"
          style={inputSt}
        />
      </div>

      {/* Table */}
      <div className="rounded-[12px] overflow-hidden border" style={{ borderColor: '#352f31' }}>
        <table className="w-full text-[13px]">
          <thead>
            <tr style={{ background: '#1a1218', borderBottom: '1px solid #352f31' }}>
              {['Date', 'Customer', 'Amount', 'Keys Created', 'Session ID', 'Payment Intent'].map(h => (
                <th key={h} className="px-4 py-3 text-left font-semibold uppercase tracking-widest text-[11px]"
                    style={{ color: '#5d585c' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={6} className="px-4 py-10 text-center" style={{ color: '#5d585c' }}>Loading…</td></tr>
            )}
            {!loading && purchases.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center" style={{ color: '#5d585c' }}>
                  No purchases yet. Share <code className="font-mono text-[12px]" style={{ color: '#dc2625' }}>/purchase</code> with your customers.
                </td>
              </tr>
            )}
            {purchases.map((p, i) => (
              <tr key={p.id}
                  style={{
                    background: i % 2 === 0 ? '#1c1318' : '#1a1216',
                    borderBottom: '1px solid #2a2226',
                  }}>
                <td className="px-4 py-3 whitespace-nowrap" style={{ color: '#868283' }}>
                  {new Date(p.created_at).toLocaleString()}
                </td>
                <td className="px-4 py-3" style={{ color: '#c5c0c2' }}>
                  {p.customer_email ?? <span style={{ color: '#5d585c' }}>—</span>}
                </td>
                <td className="px-4 py-3 font-semibold" style={{ color: '#16a34a' }}>
                  {fmt(p.amount_total, p.currency)}
                </td>
                <td className="px-4 py-3 text-center" style={{ color: '#868283' }}>
                  {p.keys_created}
                </td>
                <td className="px-4 py-3">
                  <code className="text-[11px] font-mono" style={{ color: '#5d585c' }}>
                    {p.stripe_session_id.slice(-16)}
                  </code>
                </td>
                <td className="px-4 py-3">
                  {p.stripe_payment_intent ? (
                    <a
                      href={`https://dashboard.stripe.com/payments/${p.stripe_payment_intent}`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-[11px] font-mono transition-colors"
                      style={{ color: '#5d585c' }}
                      onMouseEnter={e => (e.currentTarget.style.color = '#dc2625')}
                      onMouseLeave={e => (e.currentTarget.style.color = '#5d585c')}>
                      {p.stripe_payment_intent.slice(-14)} ↗
                    </a>
                  ) : <span style={{ color: '#3a3537' }}>—</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}