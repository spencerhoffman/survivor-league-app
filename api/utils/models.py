from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"

class PlayerStatus(str, Enum):
    ACTIVE = "ACTIVE"
    REDEMPTION = "REDEMPTION"
    ELIMINATED = "ELIMINATED"

class User(BaseModel):
    id: str
    username: str
    email: str
    password_hash: str
    role: UserRole = UserRole.USER
    profile_picture_url: Optional[str] = None
    created_at: datetime

class Player(BaseModel):
    id: str
    user_id: str
    entry_name: str
    status: PlayerStatus = PlayerStatus.ACTIVE
    eliminated_week: Optional[int] = None
    eliminated_teams: List[str] = []
    redemption_visits: int = 0
    pot_contributions: float = 0
    created_at: datetime

class WeeklyPick(BaseModel):
    id: str
    player_id: str
    week: int
    team: str
    is_redemption: bool = False
    created_at: datetime

class UnderdogTeam(BaseModel):
    id: str
    team: str
    week: int
    created_at: datetime

class GameResult(BaseModel):
    id: str
    team: str
    week: int
    outcome: str
    created_at: datetime

class GameSettings(BaseModel):
    id: int = 1
    current_week: int = 1
    entry_fee: float = 35.0
    buyback_multiplier: int = 3
    picks_locked: bool = False
    updated_at: datetime

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class CreatePlayerRequest(BaseModel):
    entry_name: str

class MakePickRequest(BaseModel):
    team: str
    week: int

class RedemptionPickRequest(BaseModel):
    teams: List[str]
    week: int

class BuybackRequest(BaseModel):
    week: int

class RecordResultRequest(BaseModel):
    team: str
    week: int
    outcome: str

class ResetPasswordRequest(BaseModel):
    username: str
    email: str
    new_password: str

class UpdateGameSettingsRequest(BaseModel):
    entry_fee: Optional[float] = None
    buyback_multiplier: Optional[int] = None

class UpdateUserRoleRequest(BaseModel):
    user_id: str
    role: UserRole

class UpdateTeamsRequest(BaseModel):
    teams: List[str]

class UpdateProfileRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None

class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str
