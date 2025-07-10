import { NextRequest, NextResponse } from 'next/server'
import { requireAdmin } from '@/lib/auth'
import { pool } from '@/lib/database'

export const runtime = 'nodejs'

export async function POST(request: NextRequest) {
  try {
    await requireAdmin(request)
    
    await pool.query('UPDATE game_settings SET picks_locked = false WHERE id = 1')
    
    return NextResponse.json({ message: 'Picks unlocked' })
  } catch (error) {
    console.error('Unlock picks error:', error)
    return NextResponse.json({ error: 'Failed to unlock picks' }, { status: 500 })
  }
}
