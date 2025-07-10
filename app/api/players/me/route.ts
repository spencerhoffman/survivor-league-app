import { NextRequest, NextResponse } from 'next/server'
import { requireAuth } from '@/lib/auth'
import { neon } from '@neondatabase/serverless'

const sql = neon(process.env.DATABASE_URL!)

export const runtime = 'nodejs'

export async function GET(request: NextRequest) {
  try {
    const user = await requireAuth(request)
    
    const result = await sql`SELECT * FROM players WHERE user_id = ${user.id} ORDER BY created_at DESC`
    
    return NextResponse.json(result)
  } catch (error) {
    console.error('Get my players error:', error)
    return NextResponse.json({ error: 'Failed to get players' }, { status: 500 })
  }
}
