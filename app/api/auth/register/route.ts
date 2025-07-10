import { NextRequest, NextResponse } from 'next/server'
import { createUser } from '@/lib/database'
import { hashPassword, createToken } from '@/lib/auth'
import { UserRole } from '@/types'
import { v4 as uuidv4 } from 'uuid'

export const runtime = 'nodejs'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const username = formData.get('username') as string
    const email = formData.get('email') as string
    const password = formData.get('password') as string
    const profilePicture = formData.get('profile_picture') as File | null

    if (!username || !email || !password) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 })
    }

    let profilePictureUrl = null

    const userId = uuidv4()
    const passwordHash = await hashPassword(password)

    const user = await createUser({
      id: userId,
      username,
      email,
      password_hash: passwordHash,
      role: UserRole.PLAYER,
      profile_picture_url: profilePictureUrl || undefined
    })

    const token = createToken(userId)

    return NextResponse.json({
      token,
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        role: user.role,
        profile_picture_url: user.profile_picture_url
      }
    })
  } catch (error) {
    console.error('Registration error:', error)
    return NextResponse.json({ error: 'Registration failed' }, { status: 500 })
  }
}
