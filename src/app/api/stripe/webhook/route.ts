// app/api/stripe/webhook/route.ts

import { NextRequest, NextResponse } from 'next/server'
import Stripe from 'stripe'
import bcrypt from 'bcryptjs'
import { v4 as uuidv4 } from 'uuid'
import sql from '@/lib/db'

// Maps your Stripe product names (lowercase) to duration in days.
// NULL = lifetime. Must match your exact Stripe product names.
function getDurationDays(productName: string): number | null {
  const name = productName.toLowerCase()
  if (name.includes('daily')   || name.includes('day'))   return 1
  if (name.includes('weekly')  || name.includes('week'))  return 7
  if (name.includes('monthly') || name.includes('month')) return 30
  if (name.includes('lifetime'))                          return null
  return null // default to lifetime if unknown
}

export async function POST(req: NextRequest) {
  const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
    apiVersion: '2026-02-25.clover',
  })

  const sig     = req.headers.get('stripe-signature') ?? ''
  const rawBody = await req.text()

  let event: Stripe.Event
  try {
    event = stripe.webhooks.constructEvent(rawBody, sig, process.env.STRIPE_WEBHOOK_SECRET!)
  } catch (err) {
    console.error('Webhook signature failed:', err)
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 })
  }

  if (event.type === 'checkout.session.completed') {
    const session = event.data.object as Stripe.Checkout.Session

    if (session.payment_status !== 'paid') {
      return NextResponse.json({ received: true })
    }

    const customerEmail = session.customer_details?.email ?? session.customer_email ?? null

    try {
      const lineItems = await stripe.checkout.sessions.listLineItems(session.id, {
        limit: 10,
        expand: ['data.price.product'],
      })

      const createdKeys: string[] = []

      for (const item of lineItems.data) {
        const quantity = item.quantity ?? 1
        const product  = item.price?.product as Stripe.Product | undefined
        const duration = product ? getDurationDays(product.name) : null

        for (let i = 0; i < quantity; i++) {
          const raw = 'PASS-' + uuidv4().toUpperCase().replace(/-/g, '').slice(0, 16)
            .match(/.{4}/g)!.join('-')

          const hash = await bcrypt.hash(raw, 10)

          const label = customerEmail
            ? `Purchase – ${customerEmail}`
            : `Stripe – ${session.id.slice(-8)}`

          // expires_at stays NULL — gets set on first activation in validate route
          // duration_days stores how long the key lasts once activated
          await sql`
            INSERT INTO license_keys (key_value, key_hash, label, status, duration_days)
            VALUES (${raw}, ${hash}, ${label}, 'active', ${duration})`

          createdKeys.push(raw)
        }
      }

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

      console.log(`✓ Created ${createdKeys.length} key(s) for ${customerEmail ?? 'unknown'}`)
    } catch (err) {
      console.error('Error processing purchase:', err)
      return NextResponse.json({ error: 'DB error' }, { status: 500 })
    }
  }

  return NextResponse.json({ received: true })
}