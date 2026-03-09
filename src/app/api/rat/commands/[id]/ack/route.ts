// app/api/rat/commands/[id]/ack/route.ts
// Agent calls this to acknowledge a command was received and executed.

import { NextRequest, NextResponse } from 'next/server'
import sql from '@/lib/db'

export async function POST(req: NextRequest, { params }: { params: { id: string } }) {
  const secret = req.headers.get('x-rat-secret')
  if (!secret || secret !== process.env.RAT_SECRET)
    return NextResponse.json({ error: 'Unauthorized' }, { status: 403 })

  await sql`
    UPDATE rat_commands SET acked_at = NOW() WHERE id = ${Number(params.id)}
  `
  return NextResponse.json({ ok: true })
}