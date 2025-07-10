import { NextRequest, NextResponse } from 'next/server'
import { requireAdmin } from '@/lib/auth'
import { sql } from '@vercel/postgres'
import { v4 as uuidv4 } from 'uuid'

export async function POST(request: NextRequest) {
  try {
    await requireAdmin(request)
    const { team, outcome, week } = await request.json()

    if (!team || !outcome) {
      return NextResponse.json({ error: 'Team and outcome are required' }, { status: 400 })
    }

    const settingsResult = await sql`SELECT * FROM game_settings WHERE id = 1`
    const settings = settingsResult.rows[0]
    const gameWeek = week || settings.current_week

    const existingResult = await sql`
      SELECT * FROM game_results WHERE team = ${team} AND week = ${gameWeek}
    `

    if (existingResult.rows.length > 0) {
      await sql`
        UPDATE game_results 
        SET outcome = ${outcome}
        WHERE team = ${team} AND week = ${gameWeek}
        RETURNING *
      `
      return NextResponse.json(existingResult.rows[0])
    } else {
      const resultId = uuidv4()
      const result = await sql`
        INSERT INTO game_results (id, week, team, outcome)
        VALUES (${resultId}, ${gameWeek}, ${team}, ${outcome})
        RETURNING *
      `
      return NextResponse.json(result.rows[0])
    }
  } catch (error) {
    console.error('Record result error:', error)
    return NextResponse.json({ error: 'Failed to record result' }, { status: 500 })
  }
}
