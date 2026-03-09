// app/api/c2/heartbeat/[clientId]/route.ts
import { NextRequest, NextResponse } from 'next/server'
import sql from '@/lib/db'

export async function POST(
  req: NextRequest,
  { params }: { params: { clientId: string } }
) {
  try {
    const clientId = Number(params.clientId)
    if (isNaN(clientId)) {
      return NextResponse.json({ error: 'Invalid client ID' }, { status: 400 })
    }

    const { status, cpu, ram, active_window } = await req.json().catch(() => ({}))

    await sql`
      UPDATE c2_clients 
      SET 
        last_seen = NOW(),
        status = ${status || 'active'}
      WHERE id = ${clientId}
    `
    
    return NextResponse.json({ ok: true })
  } catch (error) {
    console.error('Heartbeat error:', error)
    return NextResponse.json({ error: 'Heartbeat failed' }, { status: 500 })
  }
}