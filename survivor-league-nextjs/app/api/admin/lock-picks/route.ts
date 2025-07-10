import { NextRequest, NextResponse } from 'next/server'
import { requireAdmin } from '@/lib/auth'
import { sql } from '@vercel/postgres'

export async function POST(request: NextRequest) {
  try {
    await requireAdmin(request)
    
    await sql`UPDATE game_settings SET picks_locked = true WHERE id = 1`
    
    return NextResponse.json({ message: 'Picks locked' })
  } catch (error) {
    console.error('Lock picks error:', error)
    return NextResponse.json({ error: 'Failed to lock picks' }, { status: 500 })
  }
}
