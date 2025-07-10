import { NextRequest, NextResponse } from 'next/server'
import { sql } from '@vercel/postgres'
import { hashPassword } from '@/lib/auth'

export async function POST(request: NextRequest) {
  try {
    const { username, email, newPassword } = await request.json()

    if (!username || !email || !newPassword) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 })
    }

    const result = await sql`
      SELECT * FROM users WHERE username = ${username} AND email = ${email}
    `

    if (result.rows.length === 0) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    const passwordHash = await hashPassword(newPassword)
    
    await sql`
      UPDATE users SET password_hash = ${passwordHash} WHERE username = ${username}
    `

    return NextResponse.json({ message: 'Password reset successfully' })
  } catch (error) {
    console.error('Password reset error:', error)
    return NextResponse.json({ error: 'Password reset failed' }, { status: 500 })
  }
}
