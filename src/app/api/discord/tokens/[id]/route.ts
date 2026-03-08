// app/api/discord/tokens/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { getSession } from '@/lib/auth'
import sql from '@/lib/db'

export async function DELETE(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  const session = await getSession()
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  await sql`DELETE FROM discord_tokens WHERE id = ${Number(params.id)}`
  return NextResponse.json({ ok: true })
}