
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username VARCHAR(255) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL DEFAULT 'player',
  profile_picture_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS players (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  entry_name VARCHAR(255) NOT NULL,
  status VARCHAR(50) NOT NULL DEFAULT 'active',
  eliminated_week INTEGER,
  redemption_visits INTEGER DEFAULT 0,
  buybacks INTEGER DEFAULT 0,
  financial_contribution DECIMAL(10,2) DEFAULT 0.00,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS weekly_picks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
  week INTEGER NOT NULL,
  team VARCHAR(255) NOT NULL,
  is_redemption BOOLEAN DEFAULT FALSE,
  is_underdog BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(player_id, week, is_redemption)
);

CREATE TABLE IF NOT EXISTS game_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  week INTEGER NOT NULL,
  team VARCHAR(255) NOT NULL,
  outcome VARCHAR(50) NOT NULL, -- 'win', 'loss', 'bye'
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(week, team)
);

CREATE TABLE IF NOT EXISTS underdog_teams (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  week INTEGER NOT NULL,
  team VARCHAR(255) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(week, team)
);

CREATE TABLE IF NOT EXISTS game_settings (
  id INTEGER PRIMARY KEY DEFAULT 1,
  current_week INTEGER NOT NULL DEFAULT 1,
  picks_locked BOOLEAN DEFAULT FALSE,
  entry_fee DECIMAL(10,2) DEFAULT 25.00,
  buyback_multiplier DECIMAL(5,2) DEFAULT 1.5,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO game_settings (id, current_week, picks_locked, entry_fee, buyback_multiplier)
VALUES (1, 1, FALSE, 25.00, 1.5)
ON CONFLICT (id) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_players_user_id ON players(user_id);
CREATE INDEX IF NOT EXISTS idx_players_status ON players(status);
CREATE INDEX IF NOT EXISTS idx_weekly_picks_player_id ON weekly_picks(player_id);
CREATE INDEX IF NOT EXISTS idx_weekly_picks_week ON weekly_picks(week);
CREATE INDEX IF NOT EXISTS idx_game_results_week ON game_results(week);
CREATE INDEX IF NOT EXISTS idx_underdog_teams_week ON underdog_teams(week);
