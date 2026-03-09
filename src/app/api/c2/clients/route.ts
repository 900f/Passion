// app/api/c2/clients/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { getSession } from '@/lib/auth'
import sql from '@/lib/db'

export async function GET(req: NextRequest) {
  const session = await getSession()
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { searchParams } = new URL(req.url)
  const status = searchParams.get('status') || 'all'
  const search = searchParams.get('q') || ''

  let clients
  if (status !== 'all' && search) {
    clients = await sql`
      SELECT 
        id, hwid, alias, ip_address, country, city, 
        is_admin, status, 
        EXTRACT(EPOCH FROM (NOW() - last_seen)) as seconds_since_last_seen,
        last_seen, created_at, system_info,
        tags
      FROM c2_clients
      WHERE status = ${status}
        AND (hwid ILIKE ${'%' + search + '%'} OR ip_address ILIKE ${'%' + search + '%'})
      ORDER BY last_seen DESC
    `
  } else if (status !== 'all') {
    clients = await sql`
      SELECT 
        id, hwid, alias, ip_address, country, city, 
        is_admin, status, 
        EXTRACT(EPOCH FROM (NOW() - last_seen)) as seconds_since_last_seen,
        last_seen, created_at, system_info,
        tags
      FROM c2_clients
      WHERE status = ${status}
      ORDER BY last_seen DESC
    `
  } else if (search) {
    clients = await sql`
      SELECT 
        id, hwid, alias, ip_address, country, city, 
        is_admin, status, 
        EXTRACT(EPOCH FROM (NOW() - last_seen)) as seconds_since_last_seen,
        last_seen, created_at, system_info,
        tags
      FROM c2_clients
      WHERE hwid ILIKE ${'%' + search + '%'} OR ip_address ILIKE ${'%' + search + '%'}
      ORDER BY last_seen DESC
    `
  } else {
    clients = await sql`
      SELECT 
        id, hwid, alias, ip_address, country, city, 
        is_admin, status, 
        EXTRACT(EPOCH FROM (NOW() - last_seen)) as seconds_since_last_seen,
        last_seen, created_at, system_info,
        tags
      FROM c2_clients
      ORDER BY last_seen DESC
    `
  }

  // Format clients
  const formatted = clients.map(c => ({
    ...c,
    status: c.seconds_since_last_seen < 10 ? 'active' : 
            c.seconds_since_last_seen < 30 ? 'inactive' : 'offline',
    last_seen_ago: formatTimeAgo(c.seconds_since_last_seen)
  }))

  return NextResponse.json(formatted)
}

function formatTimeAgo(seconds: number): string {
  if (seconds < 60) return `${Math.floor(seconds)}s ago`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
}