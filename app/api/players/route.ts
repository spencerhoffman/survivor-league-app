import { NextRequest, NextResponse } from 'next/server'
import { requireAuth } from '@/lib/auth'
import { pool } from '@/lib/database'
import { v4 as uuidv4 } from 'uuid'

export const runtime = 'nodejs'

export async function POST(request: NextRequest) {
  try {
    const user = await requireAuth(request)
    const { entry_name } = await request.json()

    if (!entry_name) {
      return NextResponse.json({ error: 'Entry name is required' }, { status: 400 })
    }

    const playerId = uuidv4()
    const result = await pool.query(
      'INSERT INTO players (id, user_id, entry_name, status, weeks_survived, redemption_visits, buybacks, financial_contribution) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING *',
      [playerId, user.id, entry_name, 'active', 0, 0, 0, 35]
    )

    return NextResponse.json(result.rows[0])
  } catch (error) {
    console.error('Create player error:', error)
    return NextResponse.json({ error: 'Failed to create player' }, { status: 500 })
  }
}

export async function GET() {
  try {
    const result = await pool.query('SELECT * FROM players ORDER BY created_at DESC')
    return NextResponse.json(result.rows)
  } catch (error) {
    console.error('Get players error:', error)
    return NextResponse.json({ error: 'Failed to get players' }, { status: 500 })
  }
}
