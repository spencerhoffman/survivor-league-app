import { neon } from '@neondatabase/serverless'
import { User, Player, WeeklyPick, GameResult, UnderdogTeam, GameSettings, UserRole, PlayerStatus } from '@/types'

const sql = neon(process.env.DATABASE_URL!)

export async function initializeDatabase() {
  try {
    await sql`
      CREATE TABLE IF NOT EXISTS users (
        id VARCHAR(255) PRIMARY KEY,
        username VARCHAR(255) UNIQUE NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(50) DEFAULT 'player',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        profile_picture_url TEXT
      )
    `

    await sql`
      CREATE TABLE IF NOT EXISTS players (
        id VARCHAR(255) PRIMARY KEY,
        user_id VARCHAR(255) REFERENCES users(id),
        entry_name VARCHAR(255) NOT NULL,
        status VARCHAR(50) DEFAULT 'active',
        weeks_survived INTEGER DEFAULT 0,
        redemption_visits INTEGER DEFAULT 0,
        buybacks INTEGER DEFAULT 0,
        eliminated_week INTEGER,
        financial_contribution DECIMAL(10,2) DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `

    await sql`
      CREATE TABLE IF NOT EXISTS weekly_picks (
        id VARCHAR(255) PRIMARY KEY,
        player_id VARCHAR(255) REFERENCES players(id),
        week INTEGER NOT NULL,
        team VARCHAR(255) NOT NULL,
        is_redemption BOOLEAN DEFAULT FALSE,
        is_underdog BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `

    await sql`
      CREATE TABLE IF NOT EXISTS game_results (
        id VARCHAR(255) PRIMARY KEY,
        week INTEGER NOT NULL,
        team VARCHAR(255) NOT NULL,
        outcome VARCHAR(50) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `

    await sql`
      CREATE TABLE IF NOT EXISTS underdog_teams (
        id VARCHAR(255) PRIMARY KEY,
        week INTEGER NOT NULL,
        team VARCHAR(255) NOT NULL
      )
    `

    await sql`
      CREATE TABLE IF NOT EXISTS game_settings (
        id INTEGER PRIMARY KEY DEFAULT 1,
        current_week INTEGER DEFAULT 1,
        entry_fee DECIMAL(10,2) DEFAULT 35,
        buyback_multiplier DECIMAL(10,2) DEFAULT 3,
        picks_locked BOOLEAN DEFAULT FALSE
      )
    `

    const settingsResult = await sql`SELECT COUNT(*) as count FROM game_settings`
    if (settingsResult[0].count === '0') {
      await sql`
        INSERT INTO game_settings (current_week, entry_fee, buyback_multiplier, picks_locked)
        VALUES (1, 35, 3, false)
      `
    }

    const adminResult = await sql`SELECT COUNT(*) as count FROM users WHERE role = 'admin'`
    if (adminResult[0].count === '0') {
      const bcrypt = require('bcryptjs')
      const hashedPassword = await bcrypt.hash(process.env.ADMIN_PASSWORD || 'admin123', 10)
      await sql`INSERT INTO users (id, username, email, password_hash, role) VALUES (${'admin-id'}, ${'admin'}, ${'admin@example.com'}, ${hashedPassword}, ${'admin'})`
    }

    console.log('Database initialized successfully')
  } catch (error) {
    console.error('Database initialization error:', error)
    throw error
  }
}

export async function getUserByUsername(username: string): Promise<User | null> {
  try {
    const result = await sql`SELECT * FROM users WHERE username = ${username}`
    return result[0] as User || null
  } catch (error) {
    console.error('Error getting user by username:', error)
    return null
  }
}

export async function getUserById(id: string): Promise<User | null> {
  try {
    const result = await sql`SELECT * FROM users WHERE id = ${id}`
    return result[0] as User || null
  } catch (error) {
    console.error('Error getting user by id:', error)
    return null
  }
}

export async function createUser(user: Omit<User, 'created_at'>): Promise<User> {
  try {
    const result = await sql`
      INSERT INTO users (id, username, email, password_hash, role, profile_picture_url) 
      VALUES (${user.id}, ${user.username}, ${user.email}, ${user.password_hash}, ${user.role}, ${user.profile_picture_url}) 
      RETURNING *
    `
    return result[0] as User
  } catch (error) {
    console.error('Error creating user:', error)
    throw error
  }
}

export async function updateUser(id: string, updates: Partial<User>): Promise<User> {
  try {
    const updateFields = Object.entries(updates)
      .filter(([key, value]) => key !== 'id' && value !== undefined)
    
    if (updateFields.length === 0) {
      throw new Error('No valid fields to update')
    }
    
    if (updateFields.length === 1) {
      const [key, value] = updateFields[0]
      if (key === 'username') {
        const result = await sql`UPDATE users SET username = ${value} WHERE id = ${id} RETURNING *`
        return result[0] as User
      } else if (key === 'email') {
        const result = await sql`UPDATE users SET email = ${value} WHERE id = ${id} RETURNING *`
        return result[0] as User
      } else if (key === 'password_hash') {
        const result = await sql`UPDATE users SET password_hash = ${value} WHERE id = ${id} RETURNING *`
        return result[0] as User
      } else if (key === 'profile_picture_url') {
        const result = await sql`UPDATE users SET profile_picture_url = ${value} WHERE id = ${id} RETURNING *`
        return result[0] as User
      } else {
        throw new Error(`Unsupported update field: ${key}`)
      }
    }
    
    let result
    if (updateFields.some(([key]) => key === 'username')) {
      const username = updateFields.find(([key]) => key === 'username')?.[1]
      result = await sql`UPDATE users SET username = ${username} WHERE id = ${id} RETURNING *`
    } else if (updateFields.some(([key]) => key === 'email')) {
      const email = updateFields.find(([key]) => key === 'email')?.[1]
      result = await sql`UPDATE users SET email = ${email} WHERE id = ${id} RETURNING *`
    } else if (updateFields.some(([key]) => key === 'password_hash')) {
      const password_hash = updateFields.find(([key]) => key === 'password_hash')?.[1]
      result = await sql`UPDATE users SET password_hash = ${password_hash} WHERE id = ${id} RETURNING *`
    } else {
      throw new Error('Unsupported update field')
    }
    
    return result[0] as User
  } catch (error) {
    console.error('Error updating user:', error)
    throw error
  }
}

export async function getGameSettings(): Promise<GameSettings> {
  try {
    const result = await sql`SELECT * FROM game_settings WHERE id = 1`
    return result[0] as GameSettings
  } catch (error) {
    console.error('Error getting game settings:', error)
    throw error
  }
}

export async function updateGameSettings(updates: Partial<GameSettings>): Promise<GameSettings> {
  try {
    const updateFields = Object.entries(updates)
      .filter(([, value]) => value !== undefined)
    
    if (updateFields.length === 0) {
      throw new Error('No valid fields to update')
    }
    
    let result
    if (updateFields.some(([key]) => key === 'current_week')) {
      const current_week = updateFields.find(([key]) => key === 'current_week')?.[1]
      result = await sql`UPDATE game_settings SET current_week = ${current_week} WHERE id = 1 RETURNING *`
    } else if (updateFields.some(([key]) => key === 'picks_locked')) {
      const picks_locked = updateFields.find(([key]) => key === 'picks_locked')?.[1]
      result = await sql`UPDATE game_settings SET picks_locked = ${picks_locked} WHERE id = 1 RETURNING *`
    } else if (updateFields.some(([key]) => key === 'entry_fee')) {
      const entry_fee = updateFields.find(([key]) => key === 'entry_fee')?.[1]
      result = await sql`UPDATE game_settings SET entry_fee = ${entry_fee} WHERE id = 1 RETURNING *`
    } else if (updateFields.some(([key]) => key === 'buyback_multiplier')) {
      const buyback_multiplier = updateFields.find(([key]) => key === 'buyback_multiplier')?.[1]
      result = await sql`UPDATE game_settings SET buyback_multiplier = ${buyback_multiplier} WHERE id = 1 RETURNING *`
    } else {
      throw new Error('Unsupported update field')
    }
    
    return result[0] as GameSettings
  } catch (error) {
    console.error('Error updating game settings:', error)
    throw error
  }
}
