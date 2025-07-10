import { NextRequest, NextResponse } from 'next/server'
import { requireAuth } from '@/lib/auth'
import { pool } from '@/lib/database'

export const runtime = 'nodejs'

export async function GET(request: NextRequest) {
  try {
    const user = await requireAuth(request)
    
    const result = await pool.query(
      'SELECT * FROM players WHERE user_id = $1 ORDER BY created_at DESC',
      [user.id]
    )
    
    return NextResponse.json(result.rows)
  } catch (error) {
    console.error('Get my players error:', error)
    return NextResponse.json({ error: 'Failed to get players' }, { status: 500 })
  }
}
