import { NextRequest, NextResponse } from 'next/server'
import { requireAdmin } from '@/lib/auth'
import { pool } from '@/lib/database'
import { v4 as uuidv4 } from 'uuid'

export const runtime = 'nodejs'

export async function POST(request: NextRequest) {
  try {
    await requireAdmin(request)
    const { team, outcome, week } = await request.json()

    if (!team || !outcome) {
      return NextResponse.json({ error: 'Team and outcome are required' }, { status: 400 })
    }

    const settingsResult = await pool.query('SELECT * FROM game_settings WHERE id = 1')
    const settings = settingsResult.rows[0]
    const gameWeek = week || settings.current_week

    const existingResult = await pool.query(
      'SELECT * FROM game_results WHERE team = $1 AND week = $2',
      [team, gameWeek]
    )

    if (existingResult.rows.length > 0) {
      await pool.query(
        'UPDATE game_results SET outcome = $1 WHERE team = $2 AND week = $3 RETURNING *',
        [outcome, team, gameWeek]
      )
      return NextResponse.json(existingResult.rows[0])
    } else {
      const resultId = uuidv4()
      const result = await pool.query(
        'INSERT INTO game_results (id, week, team, outcome) VALUES ($1, $2, $3, $4) RETURNING *',
        [resultId, gameWeek, team, outcome]
      )
      return NextResponse.json(result.rows[0])
    }
  } catch (error) {
    console.error('Record result error:', error)
    return NextResponse.json({ error: 'Failed to record result' }, { status: 500 })
  }
}
