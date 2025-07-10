import { NextRequest, NextResponse } from 'next/server'
import { requireAuth } from '@/lib/auth'
import { sql } from '@vercel/postgres'

export async function GET(request: NextRequest) {
  try {
    const user = await requireAuth(request)
    
    const result = await sql`
      SELECT * FROM players WHERE user_id = ${user.id} ORDER BY created_at DESC
    `
    
    return NextResponse.json(result.rows)
  } catch (error) {
    console.error('Get my players error:', error)
    return NextResponse.json({ error: 'Failed to get players' }, { status: 500 })
  }
}
