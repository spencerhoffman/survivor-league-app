from typing import List, Optional, Dict, Any
from database import db
from models import User, Player, WeeklyPick, UnderdogTeam, GameResult, GameSettings, UserRole, PlayerStatus
from datetime import datetime
import uuid

class UserService:
    @staticmethod
    async def get_by_id(user_id: str) -> Optional[User]:
        async with db.get_connection() as conn:
            result = await conn.execute(
                "SELECT * FROM users WHERE id = %s", (user_id,)
            )
            row = await result.fetchone()
            if row:
                return User(**row)
            return None
    
    @staticmethod
    async def get_by_username(username: str) -> Optional[User]:
        async with db.get_connection() as conn:
            result = await conn.execute(
                "SELECT * FROM users WHERE username = %s", (username,)
            )
            row = await result.fetchone()
            if row:
                return User(**row)
            return None
    
    @staticmethod
    async def get_by_username_and_email(username: str, email: str) -> Optional[User]:
        async with db.get_connection() as conn:
            result = await conn.execute(
                "SELECT * FROM users WHERE username = %s AND email = %s", (username, email)
            )
            row = await result.fetchone()
            if row:
                return User(**row)
            return None
    
    @staticmethod
    async def create(user: User) -> User:
        async with db.get_connection() as conn:
            await conn.execute("""
                INSERT INTO users (id, username, email, password_hash, role, profile_picture_url, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                user.id, user.username, user.email, user.password_hash, 
                user.role.value, user.profile_picture_url, user.created_at
            ))
            await conn.commit()
            return user
    
    @staticmethod
    async def update(user: User) -> User:
        async with db.get_connection() as conn:
            await conn.execute("""
                UPDATE users SET username = %s, email = %s, password_hash = %s, 
                       role = %s, profile_picture_url = %s
                WHERE id = %s
            """, (
                user.username, user.email, user.password_hash,
                user.role.value, user.profile_picture_url, user.id
            ))
            await conn.commit()
            return user
    
    @staticmethod
    async def get_all() -> List[User]:
        async with db.get_connection() as conn:
            result = await conn.execute("SELECT * FROM users ORDER BY created_at")
            rows = await result.fetchall()
            return [User(**row) for row in rows]

class PlayerService:
    @staticmethod
    async def get_by_id(player_id: str) -> Optional[Player]:
        async with db.get_connection() as conn:
            result = await conn.execute(
                "SELECT * FROM players WHERE id = %s", (player_id,)
            )
            row = await result.fetchone()
            if row:
                return Player(**row)
            return None
    
    @staticmethod
    async def get_by_user_id(user_id: str) -> List[Player]:
        async with db.get_connection() as conn:
            result = await conn.execute(
                "SELECT * FROM players WHERE user_id = %s ORDER BY created_at", (user_id,)
            )
            rows = await result.fetchall()
            return [Player(**row) for row in rows]
    
    @staticmethod
    async def get_all() -> List[Player]:
        async with db.get_connection() as conn:
            result = await conn.execute("SELECT * FROM players ORDER BY created_at")
            rows = await result.fetchall()
            return [Player(**row) for row in rows]
    
    @staticmethod
    async def create(player: Player) -> Player:
        async with db.get_connection() as conn:
            await conn.execute("""
                INSERT INTO players (id, user_id, entry_name, status, eliminated_week, 
                                   redemption_visits, entry_fee_paid, financial_contribution, 
                                   eliminated_teams, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                player.id, player.user_id, player.entry_name, player.status.value,
                player.eliminated_week, player.redemption_visits, player.entry_fee_paid,
                player.financial_contribution, player.eliminated_teams, player.created_at
            ))
            await conn.commit()
            return player
    
    @staticmethod
    async def update(player: Player) -> Player:
        async with db.get_connection() as conn:
            await conn.execute("""
                UPDATE players SET entry_name = %s, status = %s, eliminated_week = %s,
                       redemption_visits = %s, entry_fee_paid = %s, financial_contribution = %s,
                       eliminated_teams = %s
                WHERE id = %s
            """, (
                player.entry_name, player.status.value, player.eliminated_week,
                player.redemption_visits, player.entry_fee_paid, player.financial_contribution,
                player.eliminated_teams, player.id
            ))
            await conn.commit()
            return player

class PickService:
    @staticmethod
    async def get_by_player_and_week(player_id: str, week: int) -> List[WeeklyPick]:
        async with db.get_connection() as conn:
            result = await conn.execute(
                "SELECT * FROM weekly_picks WHERE player_id = %s AND week = %s", 
                (player_id, week)
            )
            rows = await result.fetchall()
            return [WeeklyPick(**row) for row in rows]
    
    @staticmethod
    async def get_by_week(week: int) -> List[WeeklyPick]:
        async with db.get_connection() as conn:
            result = await conn.execute(
                "SELECT * FROM weekly_picks WHERE week = %s", (week,)
            )
            rows = await result.fetchall()
            return [WeeklyPick(**row) for row in rows]
    
    @staticmethod
    async def create(pick: WeeklyPick) -> WeeklyPick:
        async with db.get_connection() as conn:
            await conn.execute("""
                INSERT INTO weekly_picks (id, player_id, week, team, is_redemption, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                pick.id, pick.player_id, pick.week, pick.team, 
                pick.is_redemption, pick.created_at
            ))
            await conn.commit()
            return pick
    
    @staticmethod
    async def update(pick: WeeklyPick) -> WeeklyPick:
        async with db.get_connection() as conn:
            await conn.execute("""
                UPDATE weekly_picks SET team = %s, is_redemption = %s
                WHERE id = %s
            """, (pick.team, pick.is_redemption, pick.id))
            await conn.commit()
            return pick
    
    @staticmethod
    async def delete(pick_id: str) -> bool:
        async with db.get_connection() as conn:
            result = await conn.execute(
                "DELETE FROM weekly_picks WHERE id = %s", (pick_id,)
            )
            await conn.commit()
            return result.rowcount > 0

class GameResultService:
    @staticmethod
    async def get_by_week(week: int) -> List[GameResult]:
        async with db.get_connection() as conn:
            result = await conn.execute(
                "SELECT * FROM game_results WHERE week = %s", (week,)
            )
            rows = await result.fetchall()
            return [GameResult(**row) for row in rows]
    
    @staticmethod
    async def get_all() -> List[GameResult]:
        async with db.get_connection() as conn:
            result = await conn.execute("SELECT * FROM game_results ORDER BY week, team")
            rows = await result.fetchall()
            return [GameResult(**row) for row in rows]
    
    @staticmethod
    async def create(result: GameResult) -> GameResult:
        async with db.get_connection() as conn:
            await conn.execute("""
                INSERT INTO game_results (id, week, team, outcome, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (result.id, result.week, result.team, result.outcome, result.created_at))
            await conn.commit()
            return result
    
    @staticmethod
    async def delete(result_id: str) -> bool:
        async with db.get_connection() as conn:
            result = await conn.execute(
                "DELETE FROM game_results WHERE id = %s", (result_id,)
            )
            await conn.commit()
            return result.rowcount > 0

class UnderdogService:
    @staticmethod
    async def get_by_week(week: int) -> List[UnderdogTeam]:
        async with db.get_connection() as conn:
            result = await conn.execute(
                "SELECT * FROM underdog_teams WHERE week = %s", (week,)
            )
            rows = await result.fetchall()
            return [UnderdogTeam(**row) for row in rows]
    
    @staticmethod
    async def create(underdog: UnderdogTeam) -> UnderdogTeam:
        async with db.get_connection() as conn:
            await conn.execute("""
                INSERT INTO underdog_teams (id, week, team, created_at)
                VALUES (%s, %s, %s, %s)
            """, (underdog.id, underdog.week, underdog.team, underdog.created_at))
            await conn.commit()
            return underdog

class GameSettingsService:
    @staticmethod
    async def get() -> GameSettings:
        async with db.get_connection() as conn:
            result = await conn.execute("SELECT * FROM game_settings WHERE id = 1")
            row = await result.fetchone()
            if row:
                return GameSettings(
                    current_week=row['current_week'],
                    entry_fee=row['entry_fee'],
                    buyback_multiplier=row['buyback_multiplier'],
                    picks_locked=row['picks_locked']
                )
            return GameSettings()
    
    @staticmethod
    async def update(settings: GameSettings) -> GameSettings:
        async with db.get_connection() as conn:
            await conn.execute("""
                UPDATE game_settings SET current_week = %s, entry_fee = %s, 
                       buyback_multiplier = %s, picks_locked = %s, updated_at = %s
                WHERE id = 1
            """, (
                settings.current_week, settings.entry_fee, 
                settings.buyback_multiplier, settings.picks_locked, datetime.now()
            ))
            await conn.commit()
            return settings
