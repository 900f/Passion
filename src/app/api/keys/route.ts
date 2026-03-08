// app/api/keys/route.ts

import { NextRequest, NextResponse } from 'next/server'
import { getSession } from '@/lib/auth'
import sql from '@/lib/db'
import bcrypt from 'bcryptjs'
import { v4 as uuidv4 } from 'uuid'

function authGuard() {
  return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
}

// GET /api/keys — list all keys
export async function GET(req: NextRequest) {
  const session = await getSession()
  if (!session) return authGuard()

  const { searchParams } = new URL(req.url)
  const search = searchParams.get('q') ?? ''
  const status = searchParams.get('status') ?? ''

  let rows
  if (search && status) {
    rows = await sql`
      SELECT id, key_value, label, status, hwid, uses, max_uses, expires_at, duration_days, created_at, last_used
      FROM license_keys
      WHERE (key_value ILIKE ${'%' + search + '%'} OR label ILIKE ${'%' + search + '%'})
        AND status = ${status}
      ORDER BY created_at DESC`
  } else if (search) {
    rows = await sql`
      SELECT id, key_value, label, status, hwid, uses, max_uses, expires_at, duration_days, created_at, last_used
      FROM license_keys
      WHERE key_value ILIKE ${'%' + search + '%'} OR label ILIKE ${'%' + search + '%'}
      ORDER BY created_at DESC`
  } else if (status) {
    rows = await sql`
      SELECT id, key_value, label, status, hwid, uses, max_uses, expires_at, duration_days, created_at, last_used
      FROM license_keys WHERE status = ${status}
      ORDER BY created_at DESC`
  } else {
    rows = await sql`
      SELECT id, key_value, label, status, hwid, uses, max_uses, expires_at, duration_days, created_at, last_used
      FROM license_keys ORDER BY created_at DESC`
  }

  return NextResponse.json(rows)
}

// POST /api/keys — create key
export async function POST(req: NextRequest) {
  const session = await getSession()
  if (!session) return authGuard()

  const body = await req.json().catch(() => ({}))
  const label       = body.label        ?? null
  const maxUses     = body.max_uses     ? Number(body.max_uses)     : null
  const durationDays = body.duration_days ? Number(body.duration_days) : null

  // Generate: PASS-XXXX-XXXX-XXXX-XXXX
  const raw = 'PASS-' + uuidv4().toUpperCase().replace(/-/g, '').slice(0, 16)
    .match(/.{4}/g)!.join('-')

  const hash = await bcrypt.hash(raw, 10)

  // expires_at stays NULL — gets set on first activation in the validate route
  const rows = await sql`
    INSERT INTO license_keys (key_value, key_hash, label, max_uses, duration_days)
    VALUES (${raw}, ${hash}, ${label}, ${maxUses}, ${durationDays})
    RETURNING id, key_value, label, status, hwid, uses, max_uses, expires_at, duration_days, created_at, last_used`

  return NextResponse.json(rows[0], { status: 201 })
}