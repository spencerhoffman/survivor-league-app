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
    const { team1, team2, underdog_team } = await request.json()
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

    if (player.status !== 'redemption') {
      return NextResponse.json({ error: 'Player not in redemption round' }, { status: 400 })
    }

    const settingsResult = await pool.query('SELECT * FROM game_settings WHERE id = 1')
    const settings = settingsResult.rows[0]

    const existingPicksResult = await pool.query(
      'SELECT * FROM weekly_picks WHERE player_id = $1 AND week = $2 AND is_redemption = true',
      [playerId, settings.current_week]
    )

    if (existingPicksResult.rows.length > 0) {
      return NextResponse.json({ error: 'Redemption picks already submitted' }, { status: 400 })
    }

    const picks = [
      { team: team1, is_underdog: false },
      { team: team2, is_underdog: false },
      { team: underdog_team, is_underdog: true }
    ]

    const insertedPicks = []
    for (const pick of picks) {
      const pickId = uuidv4()
      const result = await pool.query(
        'INSERT INTO weekly_picks (id, player_id, week, team, is_redemption, is_underdog) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *',
        [pickId, playerId, settings.current_week, pick.team, true, pick.is_underdog]
      )
      insertedPicks.push(result.rows[0])
    }

    return NextResponse.json(insertedPicks)
  } catch (error) {
    console.error('Make redemption picks error:', error)
    return NextResponse.json({ error: 'Failed to make redemption picks' }, { status: 500 })
  }
}
