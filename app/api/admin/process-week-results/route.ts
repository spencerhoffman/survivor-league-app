import { NextRequest, NextResponse } from 'next/server'
import { requireAdmin } from '@/lib/auth'
import { pool } from '@/lib/database'

export const runtime = 'nodejs'

export async function POST(request: NextRequest) {
  try {
    await requireAdmin(request)
    
    const settingsResult = await pool.query('SELECT * FROM game_settings WHERE id = 1')
    const settings = settingsResult.rows[0]
    const currentWeek = settings.current_week

    const gameResultsResult = await pool.query(
      'SELECT * FROM game_results WHERE week = $1',
      [currentWeek]
    )
    const gameResults = gameResultsResult.rows

    const picksResult = await pool.query(`
      SELECT wp.*, p.id as player_id, p.entry_name, p.status
      FROM weekly_picks wp
      JOIN players p ON wp.player_id = p.id
      WHERE wp.week = $1
    `, [currentWeek])
    const picks = picksResult.rows

    const eliminatedPlayers = []
    const survivingPlayers = []

    for (const pick of picks) {
      const gameResult = gameResults.find(gr => gr.team === pick.team)
      
      if (!gameResult) {
        continue
      }

      if (pick.is_redemption) {
        const playerRedemptionPicks = picks.filter(p => 
          p.player_id === pick.player_id && p.is_redemption
        )
        
        const allCorrect = playerRedemptionPicks.every(rp => {
          const result = gameResults.find(gr => gr.team === rp.team)
          return result && result.outcome === 'win'
        })

        if (allCorrect && playerRedemptionPicks.length === 3) {
          await pool.query(
            'UPDATE players SET status = $1, redemption_visits = redemption_visits + 1 WHERE id = $2',
            ['active', pick.player_id]
          )
          survivingPlayers.push(pick.player_id)
        } else {
          await pool.query(
            'UPDATE players SET status = $1, eliminated_week = $2 WHERE id = $3',
            ['eliminated', currentWeek, pick.player_id]
          )
          eliminatedPlayers.push(pick.player_id)
        }
      } else {
        if (gameResult.outcome === 'loss') {
          await pool.query(
            'UPDATE players SET status = $1, eliminated_week = $2 WHERE id = $3',
            ['redemption', currentWeek, pick.player_id]
          )
          eliminatedPlayers.push(pick.player_id)
        } else if (gameResult.outcome === 'win') {
          await pool.query(
            'UPDATE players SET weeks_survived = weeks_survived + 1 WHERE id = $1',
            [pick.player_id]
          )
          survivingPlayers.push(pick.player_id)
        }
      }
    }

    return NextResponse.json({
      message: 'Week results processed successfully',
      current_week: currentWeek,
      total_picks_processed: picks.length,
      total_eliminated: eliminatedPlayers.length,
      total_surviving: survivingPlayers.length
    })
  } catch (error) {
    console.error('Process week results error:', error)
    return NextResponse.json({ error: 'Failed to process week results' }, { status: 500 })
  }
}
