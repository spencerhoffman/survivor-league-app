import { NextRequest, NextResponse } from 'next/server'
import { requireAuth } from '@/lib/auth'
import { pool } from '@/lib/database'

export const runtime = 'nodejs'

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  try {
    const user = await requireAuth(request)
    const { week } = await request.json()
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

    if (player.status !== 'eliminated') {
      return NextResponse.json({ error: 'Player not eliminated' }, { status: 400 })
    }

    const settingsResult = await pool.query('SELECT * FROM game_settings WHERE id = 1')
    const settings = settingsResult.rows[0]
    
    const cost = week * settings.buyback_multiplier

    await pool.query(
      'UPDATE players SET status = $1, buybacks = buybacks + 1, financial_contribution = financial_contribution + $2 WHERE id = $3',
      ['active', cost, playerId]
    )

    return NextResponse.json({ 
      message: `Buyback successful for week ${week}`, 
      cost 
    })
  } catch (error) {
    console.error('Buyback error:', error)
    return NextResponse.json({ error: 'Failed to process buyback' }, { status: 500 })
  }
}
