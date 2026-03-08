// app/purchase/success/page.tsx

'use client'
import { useEffect, useState, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'

function SuccessContent() {
  const params    = useSearchParams()
  const sessionId = params.get('session_id')
  const [status, setStatus] = useState<'loading' | 'ok' | 'error'>('loading')

  useEffect(() => {
    if (sessionId) {
      // Give the webhook a moment to process
      setTimeout(() => setStatus('ok'), 1500)
    } else {
      setStatus('error')
    }
  }, [sessionId])

  if (status === 'loading') {
    return (
      <div className="text-center">
        <div className="w-12 h-12 rounded-full border-2 border-t-transparent mx-auto mb-4 animate-spin"
             style={{ borderColor: '#dc2625', borderTopColor: 'transparent' }} />
        <p style={{ color: '#5d585c' }}>Confirming your payment…</p>
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="text-center">
        <p className="text-[16px] font-semibold mb-2" style={{ color: '#dc2625' }}>
          Something went wrong
        </p>
        <p className="text-[13px] mb-6" style={{ color: '#5d585c' }}>
          Please contact support with your order details.
        </p>
        <a href="/purchase"
           className="text-[13px] px-5 py-2 rounded-[8px]"
           style={{ background: '#2a2024', color: '#868283', border: '1px solid #352c2f' }}>
          ← Back
        </a>
      </div>
    )
  }

  return (
    <div className="text-center">
      {/* Checkmark */}
      <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6"
           style={{ background: '#16a34a18', border: '1px solid #16a34a44' }}>
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#16a34a" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
      </div>

      <h1 className="text-[24px] font-bold mb-2" style={{ color: '#e5e3e4' }}>
        Payment Successful
      </h1>
      <p className="text-[14px] mb-2" style={{ color: '#868283' }}>
        Your license key has been created and is ready to use.
      </p>
      <p className="text-[13px] mb-8" style={{ color: '#5d585c' }}>
        If you provided an email, your key will be delivered there shortly.
      </p>

      <a href="/download"
         className="inline-block h-[44px] px-8 rounded-[9px] font-bold text-[14px] text-white leading-[44px]"
         style={{
           background: '#dc2625',
           boxShadow: '0 0 20px rgba(220,38,37,0.35)',
         }}
         onMouseEnter={e => (e.currentTarget.style.background = '#e83433')}
         onMouseLeave={e => (e.currentTarget.style.background = '#dc2625')}>
        Download Now
      </a>

      {sessionId && (
        <p className="text-[11px] mt-6" style={{ color: '#3a3537' }}>
          Order ref: {sessionId.slice(-12)}
        </p>
      )}
    </div>
  )
}

export default function SuccessPage() {
  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: '#0f0b0c' }}>
      <div className="w-[420px] rounded-[17px] px-10 py-12"
           style={{
             background: 'linear-gradient(180deg,#21161a 0%,#161014 100%)',
             border: '1px solid #352f31',
             boxShadow: '0 20px 60px rgba(0,0,0,0.8)',
           }}>
        <Suspense fallback={<p style={{ color: '#5d585c', textAlign: 'center' }}>Loading…</p>}>
          <SuccessContent />
        </Suspense>
      </div>
    </div>
  )
}