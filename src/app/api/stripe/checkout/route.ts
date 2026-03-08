// app/api/stripe/checkout/route.ts

import { NextRequest, NextResponse } from 'next/server'
import Stripe from 'stripe'

export async function POST(req: NextRequest) {
  const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
    apiVersion: '2026-02-25.clover',
  })
  try {
    const body = await req.json().catch(() => ({}))
    const { priceId, quantity = 1, customerEmail } = body

    if (!priceId) {
      return NextResponse.json({ error: 'priceId is required' }, { status: 400 })
    }

    const origin = req.headers.get('origin') ?? process.env.NEXT_PUBLIC_BASE_URL ?? 'http://localhost:3000'

    const session = await stripe.checkout.sessions.create({
      mode: 'payment',
      line_items: [{ price: priceId, quantity }],
      customer_email: customerEmail ?? undefined,
      success_url: `${origin}/purchase/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url:  `${origin}/purchase`,
      metadata: { source: 'passion_dashboard' },
      // Automatically deliver a license key after payment
      // via the webhook below
    })

    return NextResponse.json({ url: session.url })
  } catch (err: unknown) {
    console.error('Stripe checkout error:', err)
    const message = err instanceof Error ? err.message : 'Stripe error'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}