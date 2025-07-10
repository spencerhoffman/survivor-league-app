import { NextRequest, NextResponse } from 'next/server'
import { requireAuth } from '@/lib/auth'
import { pool } from '@/lib/database'
import { v4 as uuidv4 } from 'uuid'

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

    const playerResult = await pool.query('SELECT * FROM players WHERE id = $1', [playerId])
    if (playerResult.rows.length === 0) {
      return NextResponse.json({ error: 'Player not found' }, { status: 404 })
    }

    const player = playerResult.rows[0]
    if (player.user_id !== user.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 403 })
    }

    const settingsResult = await pool.query('SELECT * FROM game_settings WHERE id = 1')
    const settings = settingsResult.rows[0]

    if (settings.picks_locked) {
      return NextResponse.json({ error: 'Picks are locked' }, { status: 400 })
    }

    const existingPickResult = await pool.query(
      'SELECT * FROM weekly_picks WHERE player_id = $1 AND week = $2',
      [playerId, settings.current_week]
    )

    if (existingPickResult.rows.length > 0) {
      return NextResponse.json({ error: 'Pick already exists for this week' }, { status: 400 })
    }

    const pickId = uuidv4()
    const result = await pool.query(
      'INSERT INTO weekly_picks (id, player_id, week, team, is_redemption, is_underdog) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *',
      [pickId, playerId, settings.current_week, team, is_redemption, is_underdog]
    )

    return NextResponse.json(result.rows[0])
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
    
    const result = await pool.query(
      'SELECT * FROM weekly_picks WHERE player_id = $1 ORDER BY week DESC',
      [playerId]
    )
    
    return NextResponse.json(result.rows)
  } catch (error) {
    console.error('Get player picks error:', error)
    return NextResponse.json({ error: 'Failed to get picks' }, { status: 500 })
  }
}
