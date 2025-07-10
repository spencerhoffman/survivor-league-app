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
    const { team1, team2, underdog_team } = await request.json()
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

    if (player.status !== 'redemption') {
      return NextResponse.json({ error: 'Player not in redemption round' }, { status: 400 })
    }

    const settingsResult = await sql`SELECT * FROM game_settings WHERE id = 1`
    const settings = settingsResult[0]

    const existingPicksResult = await sql`SELECT * FROM weekly_picks WHERE player_id = ${playerId} AND week = ${settings.current_week} AND is_redemption = true`

    if (existingPicksResult.length > 0) {
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
      const result = await sql`INSERT INTO weekly_picks (id, player_id, week, team, is_redemption, is_underdog) VALUES (${pickId}, ${playerId}, ${settings.current_week}, ${pick.team}, ${true}, ${pick.is_underdog}) RETURNING *`
      insertedPicks.push(result[0])
    }

    return NextResponse.json(insertedPicks)
  } catch (error) {
    console.error('Make redemption picks error:', error)
    return NextResponse.json({ error: 'Failed to make redemption picks' }, { status: 500 })
  }
}
