import { NextRequest, NextResponse } from 'next/server'
import { requireAuth } from '@/lib/auth'
import { neon } from '@neondatabase/serverless'

const sql = neon(process.env.DATABASE_URL!)

export const runtime = 'nodejs'

export async function PUT(
  request: NextRequest,
  context: { params: Promise<{ id: string; pickId: string }> }
) {
  try {
    const user = await requireAuth(request)
    const { team } = await request.json()
    const params = await context.params
    const { id: playerId, pickId } = params

    const playerResult = await sql`SELECT * FROM players WHERE id = ${playerId}`
    if (playerResult.length === 0) {
      return NextResponse.json({ error: 'Player not found' }, { status: 404 })
    }

    const player = playerResult[0]
    if (player.user_id !== user.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 403 })
    }

    const settingsResult = await sql`SELECT * FROM game_settings WHERE id = 1`
    const settings = settingsResult[0]

    if (settings.picks_locked) {
      return NextResponse.json({ error: 'Picks are locked' }, { status: 400 })
    }

    const result = await sql`UPDATE weekly_picks SET team = ${team} WHERE id = ${pickId} AND player_id = ${playerId} RETURNING *`

    if (result.length === 0) {
      return NextResponse.json({ error: 'Pick not found' }, { status: 404 })
    }

    return NextResponse.json(result[0])
  } catch (error) {
    console.error('Update pick error:', error)
    return NextResponse.json({ error: 'Failed to update pick' }, { status: 500 })
  }
}

export async function DELETE(
  request: NextRequest,
  context: { params: Promise<{ id: string; pickId: string }> }
) {
  try {
    const user = await requireAuth(request)
    const params = await context.params
    const { id: playerId, pickId } = params

    const playerResult = await sql`SELECT * FROM players WHERE id = ${playerId}`
    if (playerResult.length === 0) {
      return NextResponse.json({ error: 'Player not found' }, { status: 404 })
    }

    const player = playerResult[0]
    if (player.user_id !== user.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 403 })
    }

    const settingsResult = await sql`SELECT * FROM game_settings WHERE id = 1`
    const settings = settingsResult[0]

    if (settings.picks_locked) {
      return NextResponse.json({ error: 'Picks are locked' }, { status: 400 })
    }

    await sql`DELETE FROM weekly_picks WHERE id = ${pickId} AND player_id = ${playerId}`

    return NextResponse.json({ message: 'Pick deleted' })
  } catch (error) {
    console.error('Delete pick error:', error)
    return NextResponse.json({ error: 'Failed to delete pick' }, { status: 500 })
  }
}
