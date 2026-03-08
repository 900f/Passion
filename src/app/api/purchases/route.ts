// app/api/purchases/route.ts

import { NextRequest, NextResponse } from 'next/server'
import { getSession } from '@/lib/auth'
import sql from '@/lib/db'

export async function GET(req: NextRequest) {
  const session = await getSession()
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { searchParams } = new URL(req.url)
  const search = searchParams.get('q') ?? ''

  const rows = search
    ? await sql`
        SELECT id, stripe_session_id, stripe_payment_intent, customer_email,
               amount_total, currency, keys_created, created_at
        FROM purchases
        WHERE customer_email ILIKE ${'%' + search + '%'}
           OR stripe_session_id ILIKE ${'%' + search + '%'}
        ORDER BY created_at DESC
        LIMIT 200`
    : await sql`
        SELECT id, stripe_session_id, stripe_payment_intent, customer_email,
               amount_total, currency, keys_created, created_at
        FROM purchases
        ORDER BY created_at DESC
        LIMIT 200`

  return NextResponse.json(rows)
}