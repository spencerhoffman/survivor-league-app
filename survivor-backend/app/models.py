from enum import Enum
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserRole(str, Enum):
    ADMIN = "admin"
    PLAYER = "player"

class PlayerStatus(str, Enum):
    ACTIVE = "active"
    ELIMINATED = "eliminated"
    REDEMPTION = "redemption"

class User(BaseModel):
    id: str
    username: str
    email: str
    password_hash: str
    role: UserRole = UserRole.PLAYER
    profile_picture_url: Optional[str] = None
    created_at: datetime

class Player(BaseModel):
    id: str
    user_id: str
    entry_name: str
    status: PlayerStatus = PlayerStatus.ACTIVE
    eliminated_week: Optional[int] = None
    redemption_visits: int = 0
    buybacks: int = 0
    entry_fee_paid: bool = False
    financial_contribution: float = 0.0
    eliminated_teams: List[str] = []
    created_at: datetime

class WeeklyPick(BaseModel):
    id: str
    player_id: str
    week: int
    team: str
    is_redemption: bool = False
    is_underdog: bool = False
    created_at: datetime

class UnderdogTeam(BaseModel):
    team: str
    week: int

class GameResult(BaseModel):
    id: str
    week: int
    team: str
    outcome: str
    created_at: datetime

class GameSettings(BaseModel):
    current_week: int = 1
    entry_fee: int = 35
    buyback_multiplier: int = 3
    picks_locked: bool = False
