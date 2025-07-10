import { createClient } from '@vercel/postgres'
import { User, Player, WeeklyPick, GameResult, UnderdogTeam, GameSettings, UserRole, PlayerStatus } from '@/types'

const client = createClient({
  connectionString: process.env.POSTGRES_URL || process.env.POSTGRES_PRISMA_URL || process.env.DATABASE_URL
})

export async function initializeDatabase() {
  try {
    await client.sql`
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

    await client.sql`
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

    await client.sql`
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

    await client.sql`
      CREATE TABLE IF NOT EXISTS game_results (
        id VARCHAR(255) PRIMARY KEY,
        week INTEGER NOT NULL,
        team VARCHAR(255) NOT NULL,
        outcome VARCHAR(50) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `

    await client.sql`
      CREATE TABLE IF NOT EXISTS underdog_teams (
        id VARCHAR(255) PRIMARY KEY,
        week INTEGER NOT NULL,
        team VARCHAR(255) NOT NULL
      )
    `

    await client.sql`
      CREATE TABLE IF NOT EXISTS game_settings (
        id INTEGER PRIMARY KEY DEFAULT 1,
        current_week INTEGER DEFAULT 1,
        entry_fee DECIMAL(10,2) DEFAULT 35,
        buyback_multiplier DECIMAL(10,2) DEFAULT 3,
        picks_locked BOOLEAN DEFAULT FALSE
      )
    `

    const settingsResult = await client.sql`SELECT COUNT(*) as count FROM game_settings`
    if (settingsResult.rows[0].count === '0') {
      await client.sql`
        INSERT INTO game_settings (current_week, entry_fee, buyback_multiplier, picks_locked)
        VALUES (1, 35, 3, false)
      `
    }

    const adminResult = await client.sql`SELECT COUNT(*) as count FROM users WHERE role = 'admin'`
    if (adminResult.rows[0].count === '0') {
      const bcrypt = require('bcryptjs')
      const hashedPassword = await bcrypt.hash(process.env.ADMIN_PASSWORD || 'admin123', 10)
      await client.sql`
        INSERT INTO users (id, username, email, password_hash, role)
        VALUES ('admin-id', 'admin', 'admin@example.com', ${hashedPassword}, 'admin')
      `
    }

    console.log('Database initialized successfully')
  } catch (error) {
    console.error('Database initialization error:', error)
    throw error
  }
}

export async function getUserByUsername(username: string): Promise<User | null> {
  try {
    const result = await client.sql`SELECT * FROM users WHERE username = ${username}`
    return result.rows[0] as User || null
  } catch (error) {
    console.error('Error getting user by username:', error)
    return null
  }
}

export async function getUserById(id: string): Promise<User | null> {
  try {
    const result = await client.sql`SELECT * FROM users WHERE id = ${id}`
    return result.rows[0] as User || null
  } catch (error) {
    console.error('Error getting user by id:', error)
    return null
  }
}

export async function createUser(user: Omit<User, 'created_at'>): Promise<User> {
  try {
    const result = await client.sql`
      INSERT INTO users (id, username, email, password_hash, role, profile_picture_url)
      VALUES (${user.id}, ${user.username}, ${user.email}, ${user.password_hash}, ${user.role}, ${user.profile_picture_url})
      RETURNING *
    `
    return result.rows[0] as User
  } catch (error) {
    console.error('Error creating user:', error)
    throw error
  }
}

export async function updateUser(id: string, updates: Partial<User>): Promise<User> {
  try {
    const setClause = Object.keys(updates)
      .filter(key => key !== 'id' && updates[key as keyof User] !== undefined)
      .map(key => `${key} = $${Object.keys(updates).indexOf(key) + 2}`)
      .join(', ')
    
    const values = [id, ...Object.values(updates).filter(val => val !== undefined)]
    
    const result = await client.query(
      `UPDATE users SET ${setClause} WHERE id = $1 RETURNING *`,
      values
    )
    return result.rows[0] as User
  } catch (error) {
    console.error('Error updating user:', error)
    throw error
  }
}

export async function getGameSettings(): Promise<GameSettings> {
  try {
    const result = await client.sql`SELECT * FROM game_settings WHERE id = 1`
    return result.rows[0] as GameSettings
  } catch (error) {
    console.error('Error getting game settings:', error)
    throw error
  }
}

export async function updateGameSettings(updates: Partial<GameSettings>): Promise<GameSettings> {
  try {
    const setClause = Object.keys(updates)
      .map(key => `${key} = $${Object.keys(updates).indexOf(key) + 1}`)
      .join(', ')
    
    const values = Object.values(updates)
    
    const result = await client.query(
      `UPDATE game_settings SET ${setClause} WHERE id = 1 RETURNING *`,
      values
    )
    return result.rows[0] as GameSettings
  } catch (error) {
    console.error('Error updating game settings:', error)
    throw error
  }
}
