import { NextRequest, NextResponse } from 'next/server'
import { requireAuth } from '@/lib/auth'
import { neon } from '@neondatabase/serverless'
import { v4 as uuidv4 } from 'uuid'

const sql = neon(process.env.DATABASE_URL!)

export const runtime = 'nodejs'

export async function POST(request: NextRequest) {
  try {
    const user = await requireAuth(request)
    const { entry_name } = await request.json()

    if (!entry_name) {
      return NextResponse.json({ error: 'Entry name is required' }, { status: 400 })
    }

    const playerId = uuidv4()
    const result = await sql`
      INSERT INTO players (id, user_id, entry_name, status, weeks_survived, redemption_visits, buybacks, financial_contribution) 
      VALUES (${playerId}, ${user.id}, ${entry_name}, ${'active'}, ${0}, ${0}, ${0}, ${35}) 
      RETURNING *
    `

    return NextResponse.json(result[0])
  } catch (error) {
    console.error('Create player error:', error)
    return NextResponse.json({ error: 'Failed to create player' }, { status: 500 })
  }
}

export async function GET() {
  try {
    const result = await sql`SELECT * FROM players ORDER BY created_at DESC`
    return NextResponse.json(result)
  } catch (error) {
    console.error('Get players error:', error)
    return NextResponse.json({ error: 'Failed to get players' }, { status: 500 })
  }
}
