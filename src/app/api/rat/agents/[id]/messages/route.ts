// app/api/rat/agents/[id]/messages/route.ts
// Called automatically — deletes all messages for an agent that has gone offline.
// The heartbeat route already marks agents offline via last_seen timeout.
// This route is called by the dashboard when it detects an agent just went offline.

import { NextRequest, NextResponse } from 'next/server'
import sql from '@/lib/db'
import { getSession } from '@/lib/auth'

// DELETE /api/rat/agents/[id]/messages
// Clears all messages for an agent (called when they go offline)
export async function DELETE(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const session = await getSession()
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const agentId = decodeURIComponent(params.id)

  try {
    await sql`DELETE FROM rat_messages WHERE agent_id = ${agentId}`
    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Error deleting messages:', error)
    return NextResponse.json({ error: 'Failed to delete messages' }, { status: 500 })
  }
}

// GET /api/rat/agents/[id]/messages — fetch messages for an agent
export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const session = await getSession()
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const agentId = decodeURIComponent(params.id)

  try {
    const messages = await sql`
      SELECT id, sender, body, created_at
      FROM rat_messages
      WHERE agent_id = ${agentId}
      ORDER BY created_at ASC
      LIMIT 100
    `
    return NextResponse.json(messages)
  } catch (error) {
    console.error('Error fetching messages:', error)
    return NextResponse.json({ error: 'Failed to fetch messages' }, { status: 500 })
  }
}