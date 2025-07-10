import jwt from 'jsonwebtoken'
import bcrypt from 'bcryptjs'
import { NextRequest } from 'next/server'
import { getUserById } from './database'
import { User } from '@/types'

const JWT_SECRET = process.env.JWT_SECRET_KEY || 'development-key-only'

export function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, 10)
}

export function verifyPassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash)
}

export function createToken(userId: string): string {
  return jwt.sign({ userId }, JWT_SECRET, { expiresIn: '7d' })
}

export function verifyToken(token: string): { userId: string } | null {
  try {
    return jwt.verify(token, JWT_SECRET) as { userId: string }
  } catch {
    return null
  }
}

export async function getCurrentUser(request: NextRequest): Promise<User | null> {
  try {
    const authHeader = request.headers.get('authorization')
    if (!authHeader?.startsWith('Bearer ')) {
      return null
    }

    const token = authHeader.substring(7)
    const decoded = verifyToken(token)
    if (!decoded) {
      return null
    }

    return await getUserById(decoded.userId)
  } catch {
    return null
  }
}

export async function requireAuth(request: NextRequest): Promise<User> {
  const user = await getCurrentUser(request)
  if (!user) {
    throw new Error('Authentication required')
  }
  return user
}

export async function requireAdmin(request: NextRequest): Promise<User> {
  const user = await requireAuth(request)
  if (user.role !== 'admin') {
    throw new Error('Admin access required')
  }
  return user
}
