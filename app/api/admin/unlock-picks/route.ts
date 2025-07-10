import { NextRequest, NextResponse } from 'next/server'
import { requireAdmin } from '@/lib/auth'
import { neon } from '@neondatabase/serverless'

const sql = neon(process.env.DATABASE_URL!)

export const runtime = 'nodejs'

export async function POST(request: NextRequest) {
  try {
    await requireAdmin(request)
    
    await sql`UPDATE game_settings SET picks_locked = false WHERE id = 1`
    
    return NextResponse.json({ message: 'Picks unlocked' })
  } catch (error) {
    console.error('Unlock picks error:', error)
    return NextResponse.json({ error: 'Failed to unlock picks' }, { status: 500 })
  }
}
