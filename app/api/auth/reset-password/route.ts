import { NextRequest, NextResponse } from 'next/server'
import { pool } from '@/lib/database'
import { hashPassword } from '@/lib/auth'

export const runtime = 'nodejs'

export async function POST(request: NextRequest) {
  try {
    const { username, email, newPassword } = await request.json()

    if (!username || !email || !newPassword) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 })
    }

    const result = await pool.query(
      'SELECT * FROM users WHERE username = $1 AND email = $2',
      [username, email]
    )

    if (result.rows.length === 0) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    const passwordHash = await hashPassword(newPassword)
    
    await pool.query(
      'UPDATE users SET password_hash = $1 WHERE username = $2',
      [passwordHash, username]
    )

    return NextResponse.json({ message: 'Password reset successfully' })
  } catch (error) {
    console.error('Password reset error:', error)
    return NextResponse.json({ error: 'Password reset failed' }, { status: 500 })
  }
}
