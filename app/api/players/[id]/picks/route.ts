import { NextRequest, NextResponse } from 'next/server'
import { requireAuth } from '@/lib/auth'
import { neon } from '@neondatabase/serverless'
import { v4 as uuidv4 } from 'uuid'

const sql = neon(process.env.DATABASE_URL!)

export const runtime = 'nodejs'

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  try {
    const user = await requireAuth(request)
    const { team, is_redemption = false, is_underdog = false } = await request.json()
    const params = await context.params
    const playerId = params.id

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

    const existingPickResult = await sql`SELECT * FROM weekly_picks WHERE player_id = ${playerId} AND week = ${settings.current_week}`

    if (existingPickResult.length > 0) {
      return NextResponse.json({ error: 'Pick already exists for this week' }, { status: 400 })
    }

    const pickId = uuidv4()
    const result = await sql`INSERT INTO weekly_picks (id, player_id, week, team, is_redemption, is_underdog) VALUES (${pickId}, ${playerId}, ${settings.current_week}, ${team}, ${is_redemption}, ${is_underdog}) RETURNING *`

    return NextResponse.json(result[0])
  } catch (error) {
    console.error('Make pick error:', error)
    return NextResponse.json({ error: 'Failed to make pick' }, { status: 500 })
  }
}

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  try {
    const params = await context.params
    const playerId = params.id
    
    const result = await sql`SELECT * FROM weekly_picks WHERE player_id = ${playerId} ORDER BY week DESC`
    
    return NextResponse.json(result)
  } catch (error) {
    console.error('Get player picks error:', error)
    return NextResponse.json({ error: 'Failed to get picks' }, { status: 500 })
  }
}
