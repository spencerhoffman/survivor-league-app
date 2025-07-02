import os
import asyncio
from typing import AsyncGenerator
import psycopg
from psycopg.rows import dict_row
from contextlib import asynccontextmanager
import logging

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/survivor_league")

class Database:
    def __init__(self):
        self.connection_string = DATABASE_URL
        self.db_available = True
    
    async def connect(self):
        """Initialize database connection"""
        try:
            await self.create_tables()
            logging.info("PostgreSQL database connected successfully")
        except Exception as e:
            logging.warning(f"PostgreSQL connection failed: {e}. Backend will start without database.")
            self.db_available = False
    
    async def disconnect(self):
        """Close database connection"""
        pass
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection"""
        if not self.db_available:
            raise Exception("Database not available - using fallback mode")
        
        async with await psycopg.AsyncConnection.connect(
            self.connection_string,
            row_factory=dict_row
        ) as conn:
            yield conn
    
    async def create_tables(self):
        """Create all database tables"""
        try:
            async with await psycopg.AsyncConnection.connect(
                self.connection_string,
                row_factory=dict_row
            ) as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id VARCHAR PRIMARY KEY,
                        username VARCHAR UNIQUE NOT NULL,
                        email VARCHAR UNIQUE NOT NULL,
                        password_hash VARCHAR NOT NULL,
                        role VARCHAR NOT NULL DEFAULT 'player',
                        profile_picture_url VARCHAR,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE TABLE IF NOT EXISTS players (
                        id VARCHAR PRIMARY KEY,
                        user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        entry_name VARCHAR NOT NULL,
                        status VARCHAR NOT NULL DEFAULT 'active',
                        eliminated_week INTEGER,
                        redemption_visits INTEGER DEFAULT 0,
                        entry_fee_paid BOOLEAN DEFAULT FALSE,
                        financial_contribution DECIMAL DEFAULT 0,
                        eliminated_teams TEXT[] DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE TABLE IF NOT EXISTS weekly_picks (
                        id VARCHAR PRIMARY KEY,
                        player_id VARCHAR NOT NULL REFERENCES players(id) ON DELETE CASCADE,
                        week INTEGER NOT NULL,
                        team VARCHAR NOT NULL,
                        is_redemption BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(player_id, week, team)
                    );
                    
                    CREATE TABLE IF NOT EXISTS underdog_teams (
                        id VARCHAR PRIMARY KEY,
                        week INTEGER NOT NULL,
                        team VARCHAR NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(week, team)
                    );
                    
                    CREATE TABLE IF NOT EXISTS game_results (
                        id VARCHAR PRIMARY KEY,
                        week INTEGER NOT NULL,
                        team VARCHAR NOT NULL,
                        outcome VARCHAR NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(week, team)
                    );
                    
                    CREATE TABLE IF NOT EXISTS game_settings (
                        id INTEGER PRIMARY KEY DEFAULT 1,
                        current_week INTEGER DEFAULT 1,
                        entry_fee INTEGER DEFAULT 35,
                        buyback_multiplier INTEGER DEFAULT 3,
                        picks_locked BOOLEAN DEFAULT FALSE,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CHECK (id = 1)
                    );
                    
                    INSERT INTO game_settings (id) VALUES (1) ON CONFLICT (id) DO NOTHING;
                """)
                await conn.commit()
        except Exception as e:
            logging.warning(f"Failed to create database tables: {e}")
            self.db_available = False

db = Database()
