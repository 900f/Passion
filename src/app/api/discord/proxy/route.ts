// app/api/discord/proxy/route.ts
//
// A lightweight proxy so Discord tokens never leave the server.
// POST body: { tokenId, action, payload? }
//   action = "guilds"              → GET /users/@me/guilds
//   action = "channels"            → GET /guilds/:guildId/channels  (payload: { guildId })
//   action = "send"                → POST /channels/:channelId/messages (payload: { channelId, content?, embed? })
//   action = "botInfo"             → GET /users/@me

import { NextRequest, NextResponse } from 'next/server'
import { getSession } from '@/lib/auth'
import sql from '@/lib/db'

const DISCORD = 'https://discord.com/api/v10'

async function discordFetch(
  token: string,
  path: string,
  options: RequestInit = {}
): Promise<{ ok: boolean; status: number; data: unknown }> {
  const res = await fetch(`${DISCORD}${path}`, {
    ...options,
    headers: {
      Authorization: `Bot ${token}`,
      'Content-Type': 'application/json',
      ...((options.headers as Record<string, string>) ?? {}),
    },
  })
  const data = await res.json().catch(() => ({}))
  return { ok: res.ok, status: res.status, data }
}

export async function POST(req: NextRequest) {
  const session = await getSession()
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { tokenId, action, payload } = await req.json()
  if (!tokenId || !action)
    return NextResponse.json({ error: 'tokenId and action required' }, { status: 400 })

  // Fetch the actual token from DB (never exposed to client)
  const [row] = await sql`SELECT token FROM discord_tokens WHERE id = ${Number(tokenId)}`
  if (!row) return NextResponse.json({ error: 'Token not found' }, { status: 404 })

  const token: string = row.token

  // Update last_used
  await sql`UPDATE discord_tokens SET last_used = NOW() WHERE id = ${Number(tokenId)}`

  if (action === 'botInfo') {
    const r = await discordFetch(token, '/users/@me')
    if (!r.ok) return NextResponse.json({ error: 'Discord error', detail: r.data }, { status: r.status })
    return NextResponse.json(r.data)
  }

  if (action === 'guilds') {
    const r = await discordFetch(token, '/users/@me/guilds')
    if (!r.ok) return NextResponse.json({ error: 'Discord error', detail: r.data }, { status: r.status })
    return NextResponse.json(r.data)
  }

  if (action === 'channels') {
    const { guildId } = payload ?? {}
    if (!guildId) return NextResponse.json({ error: 'guildId required' }, { status: 400 })
    const r = await discordFetch(token, `/guilds/${guildId}/channels`)
    if (!r.ok) return NextResponse.json({ error: 'Discord error', detail: r.data }, { status: r.status })
    // Filter to text channels (type 0) and categories (type 4) for display
    const channels = (r.data as Array<{ type: number; position: number; parent_id?: string }>)
      .filter(c => c.type === 0 || c.type === 4 || c.type === 2)
      .sort((a, b) => a.position - b.position)
    return NextResponse.json(channels)
  }

  if (action === 'send') {
    const { channelId, content, embeds } = payload ?? {}
    if (!channelId) return NextResponse.json({ error: 'channelId required' }, { status: 400 })
    if (!content && (!embeds || embeds.length === 0))
      return NextResponse.json({ error: 'content or embeds required' }, { status: 400 })

    const body: Record<string, unknown> = {}
    if (content) body.content = content
    if (embeds && embeds.length > 0) body.embeds = embeds

    const r = await discordFetch(token, `/channels/${channelId}/messages`, {
      method: 'POST',
      body: JSON.stringify(body),
    })
    if (!r.ok) return NextResponse.json({ error: 'Discord error', detail: r.data }, { status: r.status })
    return NextResponse.json(r.data)
  }

  return NextResponse.json({ error: 'Unknown action' }, { status: 400 })
}