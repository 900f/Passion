// app/api/stripe/webhook/route.ts

import { NextRequest, NextResponse } from 'next/server'
import Stripe from 'stripe'
import bcrypt from 'bcryptjs'
import { v4 as uuidv4 } from 'uuid'
import sql from '@/lib/db'
import { Resend } from 'resend'

function getDurationDays(productName: string): number | null {
  const name = productName.toLowerCase()
  if (name.includes('daily')   || name.includes('day'))   return 1
  if (name.includes('weekly')  || name.includes('week'))  return 7
  if (name.includes('monthly') || name.includes('month')) return 30
  if (name.includes('lifetime'))                          return null
  return null
}

function getDurationLabel(days: number | null): string {
  if (days === null) return 'Lifetime (never expires)'
  if (days === 1)    return '1 day — activates on first use'
  if (days === 7)    return '7 days — activates on first use'
  if (days === 30)   return '30 days — activates on first use'
  return `${days} days — activates on first use`
}

async function sendKeyEmail(email: string, keys: string[], productName: string, durationDays: number | null) {
  const resend = new Resend(process.env.RESEND_API_KEY!)
  const durationLabel = getDurationLabel(durationDays)
  const planName = productName

  const keyRows = keys.map(k => `
    <tr>
      <td style="padding: 12px 16px; font-family: 'Courier New', monospace; font-size: 15px; font-weight: 700; color: #f0ecee; background: #1a1218; border-radius: 8px; letter-spacing: 1px;">
        ${k}
      </td>
    </tr>
  `).join('')

  await resend.emails.send({
    from: 'Passion <noreply@getpassion.xyz>',
    to: email,
    subject: `Your Passion License Key — ${planName}`,
    html: `
      <!DOCTYPE html>
      <html>
      <head><meta charset="utf-8"></head>
      <body style="margin: 0; padding: 0; background: #0a0809; font-family: -apple-system, sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background: #0a0809; padding: 40px 20px;">
          <tr>
            <td align="center">
              <table width="520" cellpadding="0" cellspacing="0" style="background: linear-gradient(180deg, #1a1218 0%, #130e10 100%); border-radius: 16px; border: 1px solid #2a2226; overflow: hidden;">

                <!-- Header -->
                <tr>
                  <td style="padding: 36px 40px 28px; border-bottom: 1px solid #1e1a1c;">
                    <div style="display: inline-block; background: rgba(220,38,37,0.1); border: 1px solid rgba(220,38,37,0.25); border-radius: 100px; padding: 4px 14px; margin-bottom: 16px;">
                      <span style="font-size: 10px; font-weight: 700; letter-spacing: 2px; color: #dc2625; text-transform: uppercase;">License Key</span>
                    </div>
                    <h1 style="margin: 0; font-size: 26px; font-weight: 800; color: #f0ecee; letter-spacing: -0.5px;">
                      Here's your key
                    </h1>
                    <p style="margin: 8px 0 0; font-size: 14px; color: #5d585c;">
                      ${planName} · ${durationLabel}
                    </p>
                  </td>
                </tr>

                <!-- Keys -->
                <tr>
                  <td style="padding: 28px 40px;">
                    <p style="margin: 0 0 12px; font-size: 11px; font-weight: 600; letter-spacing: 1.5px; color: #3a3537; text-transform: uppercase;">
                      Your license ${keys.length > 1 ? 'keys' : 'key'}
                    </p>
                    <table width="100%" cellpadding="0" cellspacing="4">
                      ${keyRows}
                    </table>
                  </td>
                </tr>

                <!-- Info -->
                <tr>
                  <td style="padding: 0 40px 28px;">
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid #1e1a1c; border-radius: 10px; padding: 16px;">
                      <p style="margin: 0 0 8px; font-size: 13px; color: #868283; line-height: 1.6;">
                        ⏱ <strong style="color: #c5c0c2;">Your timer starts on first use</strong>, not now. Keep this key safe until you're ready to activate.
                      </p>
                      <p style="margin: 0; font-size: 13px; color: #5d585c; line-height: 1.6;">
                        To download, visit <a href="${process.env.NEXT_PUBLIC_BASE_URL}/download" style="color: #dc2625;">${process.env.NEXT_PUBLIC_BASE_URL}/download</a> and enter your key.
                      </p>
                    </div>
                  </td>
                </tr>

                <!-- Footer -->
                <tr>
                  <td style="padding: 20px 40px; border-top: 1px solid #1e1a1c;">
                    <p style="margin: 0; font-size: 12px; color: #2a2527; text-align: center;">
                      Passion · Questions? Reply to this email.
                    </p>
                  </td>
                </tr>

              </table>
            </td>
          </tr>
        </table>
      </body>
      </html>
    `,
  })
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
      let lastProductName = 'Passion'
      let lastDuration: number | null = null

      for (const item of lineItems.data) {
        const quantity = item.quantity ?? 1
        const product  = item.price?.product as Stripe.Product | undefined
        const duration = product ? getDurationDays(product.name) : null
        if (product) { lastProductName = product.name; lastDuration = duration }

        for (let i = 0; i < quantity; i++) {
          const raw = 'PASS-' + uuidv4().toUpperCase().replace(/-/g, '').slice(0, 16)
            .match(/.{4}/g)!.join('-')

          const hash = await bcrypt.hash(raw, 10)

          const label = customerEmail
            ? `Purchase – ${customerEmail}`
            : `Stripe – ${session.id.slice(-8)}`

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

      // Send keys via Resend if customer provided email
      if (customerEmail && createdKeys.length > 0) {
        try {
          await sendKeyEmail(customerEmail, createdKeys, lastProductName, lastDuration)
          console.log(`✉ Key email sent to ${customerEmail}`)
        } catch (emailErr) {
          // Don't fail the webhook if email fails — key is already created
          console.error('Email send failed:', emailErr)
        }
      }

      console.log(`✓ Created ${createdKeys.length} key(s) for ${customerEmail ?? 'unknown'}`)
    } catch (err) {
      console.error('Error processing purchase:', err)
      return NextResponse.json({ error: 'DB error' }, { status: 500 })
    }
  }

  return NextResponse.json({ received: true })
}