// app/api/c2/commands/[clientId]/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { getSession } from '@/lib/auth'
import sql from '@/lib/db'

// GET pending commands for client (NO AUTH REQUIRED - called by client)
export async function GET(
  req: NextRequest,
  { params }: { params: { clientId: string } }
) {
  try {
    const clientId = Number(params.clientId)
    if (isNaN(clientId)) {
      return NextResponse.json({ error: 'Invalid client ID' }, { status: 400 })
    }

    // Clean up old commands
    await sql`DELETE FROM c2_commands_temp WHERE expires_at < NOW()`
    
    const commands = await sql`
      SELECT id, command, parameters
      FROM c2_commands_temp
      WHERE client_id = ${clientId} 
        AND status = 'pending'
      ORDER BY created_at ASC
    `
    
    return NextResponse.json(commands || [])
  } catch (error) {
    console.error('Error fetching commands:', error)
    return NextResponse.json({ error: 'Failed to fetch commands' }, { status: 500 })
  }
}

// POST new command (AUTH REQUIRED - from dashboard)
export async function POST(
  req: NextRequest,
  { params }: { params: { clientId: string } }
) {
  try {
    const session = await getSession()
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const clientId = Number(params.clientId)
    if (isNaN(clientId)) {
      return NextResponse.json({ error: 'Invalid client ID' }, { status: 400 })
    }

    const { command, parameters } = await req.json()
    
    if (!command) {
      return NextResponse.json({ error: 'Command required' }, { status: 400 })
    }

    const [cmd] = await sql`
      INSERT INTO c2_commands_temp (client_id, command, parameters, status, expires_at)
      VALUES (
        ${clientId}, 
        ${command}, 
        ${JSON.stringify(parameters || {})}, 
        'pending',
        NOW() + INTERVAL '5 minutes'
      )
      RETURNING id
    `
    
    return NextResponse.json({ 
      id: cmd.id,
      status: 'queued',
      expires: new Date(Date.now() + 5 * 60 * 1000).toISOString()
    })
  } catch (error) {
    console.error('Error creating command:', error)
    return NextResponse.json({ error: 'Failed to create command' }, { status: 500 })
  }
}

// PATCH command status (NO AUTH - called by client)
export async function PATCH(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const commandId = Number(params.id)
    if (isNaN(commandId)) {
      return NextResponse.json({ error: 'Invalid command ID' }, { status: 400 })
    }

    const { status } = await req.json()
    
    await sql`
      UPDATE c2_commands_temp
      SET status = ${status}
      WHERE id = ${commandId}
    `
    
    return NextResponse.json({ ok: true })
  } catch (error) {
    console.error('Error updating command:', error)
    return NextResponse.json({ error: 'Failed to update command' }, { status: 500 })
  }
}