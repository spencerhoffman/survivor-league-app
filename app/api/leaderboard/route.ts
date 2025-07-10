import { NextResponse } from 'next/server'
import { sql } from '@vercel/postgres'

export async function GET() {
  try {
    const result = await sql`
      SELECT 
        p.id as player_id,
        p.entry_name,
        u.username,
        p.status,
        p.weeks_survived,
        p.redemption_visits,
        p.buybacks,
        p.eliminated_week,
        p.financial_contribution,
        u.profile_picture_url
      FROM players p
      JOIN users u ON p.user_id = u.id
      ORDER BY p.weeks_survived DESC, p.redemption_visits ASC, p.buybacks ASC
    `
    
    return NextResponse.json(result.rows)
  } catch (error) {
    console.error('Get leaderboard error:', error)
    return NextResponse.json({ error: 'Failed to get leaderboard' }, { status: 500 })
  }
}
