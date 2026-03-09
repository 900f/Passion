// app/api/c2/clients/[id]/commands/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { getSession } from '@/lib/auth'
import sql from '@/lib/db'

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const session = await getSession()
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const commands = await sql`
    SELECT id, command, parameters, status, output, created_at, completed_at
    FROM c2_commands
    WHERE client_id = ${Number(params.id)}
    ORDER BY created_at DESC
    LIMIT 50
  `
  
  return NextResponse.json(commands)
}

export async function POST(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const session = await getSession()
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { command, parameters } = await req.json()
  
  const [cmd] = await sql`
    INSERT INTO c2_commands (client_id, command, parameters, issued_by)
    VALUES (${Number(params.id)}, ${command}, ${parameters}, ${session.username})
    RETURNING id
  `
  
  return NextResponse.json(cmd)
}