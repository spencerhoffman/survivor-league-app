import os
import asyncpg
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import json
from datetime import datetime
import uuid

DATABASE_URL = os.getenv("DATABASE_URL")

@asynccontextmanager
async def get_db_connection():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        await conn.close()

async def init_database():
    async with get_db_connection() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'USER',
                profile_picture_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id UUID PRIMARY KEY,
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                entry_name VARCHAR(255) NOT NULL,
                status VARCHAR(50) DEFAULT 'ACTIVE',
                eliminated_week INTEGER,
                eliminated_teams TEXT[] DEFAULT '{}',
                redemption_visits INTEGER DEFAULT 0,
                pot_contributions DECIMAL(10,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS picks (
                id UUID PRIMARY KEY,
                player_id UUID REFERENCES players(id) ON DELETE CASCADE,
                week INTEGER NOT NULL,
                team VARCHAR(10) NOT NULL,
                is_redemption BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(player_id, week, team, is_redemption)
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS underdog_teams (
                id UUID PRIMARY KEY,
                team VARCHAR(10) NOT NULL,
                week INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(team, week)
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS game_results (
                id UUID PRIMARY KEY,
                team VARCHAR(10) NOT NULL,
                week INTEGER NOT NULL,
                outcome VARCHAR(10) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(team, week)
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS game_settings (
                id INTEGER PRIMARY KEY DEFAULT 1,
                current_week INTEGER DEFAULT 1,
                entry_fee DECIMAL(10,2) DEFAULT 35.00,
                buyback_multiplier INTEGER DEFAULT 3,
                picks_locked BOOLEAN DEFAULT FALSE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CHECK (id = 1)
            )
        ''')
        
        settings_exists = await conn.fetchval('SELECT COUNT(*) FROM game_settings WHERE id = 1')
        if settings_exists == 0:
            await conn.execute('''
                INSERT INTO game_settings (id, current_week, entry_fee, buyback_multiplier, picks_locked)
                VALUES (1, 1, 35.00, 3, FALSE)
            ''')
        
        admin_exists = await conn.fetchval('SELECT COUNT(*) FROM users WHERE role = $1', 'ADMIN')
        if admin_exists == 0:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            admin_id = str(uuid.uuid4())
            admin_password_hash = pwd_context.hash(os.getenv("ADMIN_PASSWORD", "admin123"))
            await conn.execute('''
                INSERT INTO users (id, username, email, password_hash, role)
                VALUES ($1, $2, $3, $4, $5)
            ''', admin_id, "admin", "admin@example.com", admin_password_hash, "ADMIN")

async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    async with get_db_connection() as conn:
        row = await conn.fetchrow('SELECT * FROM users WHERE id = $1', user_id)
        return dict(row) if row else None

async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    async with get_db_connection() as conn:
        row = await conn.fetchrow('SELECT * FROM users WHERE username = $1', username)
        return dict(row) if row else None

async def create_user(user_data: Dict[str, Any]) -> str:
    user_id = str(uuid.uuid4())
    async with get_db_connection() as conn:
        await conn.execute('''
            INSERT INTO users (id, username, email, password_hash, profile_picture_url)
            VALUES ($1, $2, $3, $4, $5)
        ''', user_id, user_data['username'], user_data['email'], 
            user_data['password_hash'], user_data.get('profile_picture_url'))
    return user_id

async def update_user(user_id: str, updates: Dict[str, Any]):
    set_clauses = []
    values = []
    param_count = 1
    
    for key, value in updates.items():
        if key in ['username', 'email', 'password_hash', 'profile_picture_url', 'role']:
            set_clauses.append(f"{key} = ${param_count}")
            values.append(value)
            param_count += 1
    
    if set_clauses:
        values.append(user_id)
        query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ${param_count}"
        async with get_db_connection() as conn:
            await conn.execute(query, *values)

async def get_game_settings() -> Dict[str, Any]:
    async with get_db_connection() as conn:
        row = await conn.fetchrow('SELECT * FROM game_settings WHERE id = 1')
        return dict(row) if row else {}

async def update_game_settings(updates: Dict[str, Any]):
    set_clauses = []
    values = []
    param_count = 1
    
    for key, value in updates.items():
        if key in ['current_week', 'entry_fee', 'buyback_multiplier', 'picks_locked']:
            set_clauses.append(f"{key} = ${param_count}")
            values.append(value)
            param_count += 1
    
    if set_clauses:
        set_clauses.append(f"updated_at = ${param_count}")
        values.append(datetime.now())
        query = f"UPDATE game_settings SET {', '.join(set_clauses)} WHERE id = 1"
        async with get_db_connection() as conn:
            await conn.execute(query, *values)

NFL_TEAMS = [
    "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN",
    "DET", "GB", "HOU", "IND", "JAX", "KC", "LV", "LAC", "LAR", "MIA",
    "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SF", "SEA", "TB",
    "TEN", "WAS"
]
