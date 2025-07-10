export enum UserRole {
  ADMIN = "admin",
  PLAYER = "player"
}

export enum PlayerStatus {
  ACTIVE = "active",
  ELIMINATED = "eliminated",
  REDEMPTION = "redemption"
}

export interface User {
  id: string
  username: string
  email: string
  password_hash: string
  role: UserRole
  created_at: Date
  profile_picture_url?: string
}

export interface Player {
  id: string
  user_id: string
  entry_name: string
  status: PlayerStatus
  weeks_survived: number
  redemption_visits: number
  buybacks: number
  eliminated_week?: number
  financial_contribution: number
  created_at: Date
}

export interface WeeklyPick {
  id: string
  player_id: string
  week: number
  team: string
  is_redemption: boolean
  is_underdog: boolean
  created_at: Date
}

export interface UnderdogTeam {
  id: string
  week: number
  team: string
}

export interface GameResult {
  id: string
  week: number
  team: string
  outcome: string
  created_at: Date
}

export interface GameSettings {
  current_week: number
  entry_fee: number
  buyback_multiplier: number
  picks_locked: boolean
}

export interface LeaderboardEntry {
  player_id: string
  entry_name: string
  username: string
  status: string
  weeks_survived: number
  redemption_visits: number
  buybacks: number
  eliminated_week?: number
  financial_contribution: number
  profile_picture_url?: string
}

export interface PickEntry {
  pick_id: string
  week: number
  team: string
  player_name: string
  username: string
  is_redemption: boolean
  is_underdog: boolean
  created_at: string
}
