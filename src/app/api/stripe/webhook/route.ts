// app/api/stripe/webhook/route.ts

import { NextRequest, NextResponse } from 'next/server'
import Stripe from 'stripe'
import bcrypt from 'bcryptjs'
import { v4 as uuidv4 } from 'uuid'
import sql from '@/lib/db'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2025-01-27.acacia',
})

// Disable Next.js body parsing — Stripe needs the raw body for signature verification
export const config = { api: { bodyParser: false } }

export async function POST(req: NextRequest) {
  const sig      = req.headers.get('stripe-signature') ?? ''
  const rawBody  = await req.text()

  let event: Stripe.Event
  try {
    event = stripe.webhooks.constructEvent(rawBody, sig, process.env.STRIPE_WEBHOOK_SECRET!)
  } catch (err) {
    console.error('Webhook signature failed:', err)
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 })
  }

  if (event.type === 'checkout.session.completed') {
    const session = event.data.object as Stripe.Checkout.Session

    // Only handle paid sessions
    if (session.payment_status !== 'paid') {
      return NextResponse.json({ received: true })
    }

    const customerEmail = session.customer_details?.email ?? session.customer_email ?? null

    try {
      // How many keys to create (quantity support)
      const lineItems = await stripe.checkout.sessions.listLineItems(session.id, { limit: 10 })
      const totalKeys = lineItems.data.reduce((acc, item) => acc + (item.quantity ?? 1), 0)

      const createdKeys: string[] = []

      for (let i = 0; i < totalKeys; i++) {
        // Generate PASS-XXXX-XXXX-XXXX-XXXX
        const raw = 'PASS-' + uuidv4().toUpperCase().replace(/-/g, '').slice(0, 16)
          .match(/.{4}/g)!.join('-')

        const hash = await bcrypt.hash(raw, 10)

        await sql`
          INSERT INTO license_keys (key_value, key_hash, label, status)
          VALUES (
            ${raw},
            ${hash},
            ${customerEmail ? `Purchase – ${customerEmail}` : `Stripe – ${session.id.slice(-8)}`},
            'active'
          )`

        createdKeys.push(raw)
      }

      // Store purchase record
      await sql`
        INSERT INTO purchases (stripe_session_id, stripe_payment_intent, customer_email, amount_total, currency, keys_created, created_at)
        VALUES (
          ${session.id},
          ${session.payment_intent?.toString() ?? null},
          ${customerEmail},
          ${session.amount_total ?? 0},
          ${session.currency ?? 'usd'},
          ${createdKeys.length},
          NOW()
        )
        ON CONFLICT (stripe_session_id) DO NOTHING`

      // Optional: send keys by email here using Resend / Nodemailer
      // await sendKeyEmail(customerEmail, createdKeys)

      console.log(`✓ Created ${createdKeys.length} key(s) for ${customerEmail ?? 'unknown'}`)
    } catch (err) {
      console.error('Error processing purchase:', err)
      return NextResponse.json({ error: 'DB error' }, { status: 500 })
    }
  }

  return NextResponse.json({ received: true })
}