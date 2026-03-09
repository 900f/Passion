// app/api/c2/commands/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { getSession } from '@/lib/auth'
import sql from '@/lib/db'

export async function PATCH(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const session = await getSession()
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { status } = await req.json()
  
  await sql`
    UPDATE c2_commands
    SET status = ${status}
    WHERE id = ${Number(params.id)}
  `
  
  return NextResponse.json({ ok: true })
}