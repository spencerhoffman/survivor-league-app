import { NextRequest, NextResponse } from 'next/server'
import { requireAdmin } from '@/lib/auth'
import { sql } from '@vercel/postgres'

export async function POST(request: NextRequest) {
  try {
    await requireAdmin(request)
    
    const result = await sql`
      UPDATE game_settings 
      SET current_week = current_week + 1, picks_locked = false 
      WHERE id = 1 
      RETURNING current_week
    `
    
    return NextResponse.json({ current_week: result.rows[0].current_week })
  } catch (error) {
    console.error('Advance week error:', error)
    return NextResponse.json({ error: 'Failed to advance week' }, { status: 500 })
  }
}
