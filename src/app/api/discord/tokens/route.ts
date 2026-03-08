// app/api/discord/tokens/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { getSession } from '@/lib/auth'
import sql from '@/lib/db'

export async function GET() {
  const session = await getSession()
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const tokens = await sql`
    SELECT id, alias, created_at, last_used
    FROM discord_tokens
    ORDER BY created_at DESC`

  return NextResponse.json(tokens)
}

export async function POST(req: NextRequest) {
  const session = await getSession()
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { alias, token } = await req.json()
  if (!alias?.trim() || !token?.trim())
    return NextResponse.json({ error: 'Alias and token are required' }, { status: 400 })

  const [row] = await sql`
    INSERT INTO discord_tokens (alias, token)
    VALUES (${alias.trim()}, ${token.trim()})
    RETURNING id, alias, created_at, last_used`

  return NextResponse.json(row, { status: 201 })
}