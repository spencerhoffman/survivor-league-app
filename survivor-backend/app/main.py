from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, date
from enum import Enum
import uuid
import jwt
import hashlib
import os

app = FastAPI(title="Survivor League API")

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "development-key-only")
security = HTTPBearer()

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
    created_at: datetime

class Player(BaseModel):
    id: str
    user_id: str
    entry_name: str  # e.g., "Tord 1", "Tord 2"
    status: PlayerStatus = PlayerStatus.ACTIVE
    eliminated_week: Optional[int] = None
    redemption_visits: int = 0
    buybacks: int = 0
    entry_fee_paid: bool = False

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
    winning_team: str
    losing_team: str
    created_at: datetime

class GameSettings(BaseModel):
    current_week: int = 1
    entry_fee: int = 35
    buyback_multiplier: int = 3
    picks_locked: bool = False

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
    is_underdog: bool = False

class RedemptionPickRequest(BaseModel):
    team1: str
    team2: str
    underdog_team: str

class BuybackRequest(BaseModel):
    week: int

class RecordResultRequest(BaseModel):
    winning_team: str
    losing_team: str

class ResetPasswordRequest(BaseModel):
    username: str
    email: str
    new_password: str

users_db: Dict[str, User] = {}
players_db: Dict[str, Player] = {}
picks_db: List[WeeklyPick] = []
underdog_teams_db: List[UnderdogTeam] = []
game_results_db: List[GameResult] = []
game_settings = GameSettings()

NFL_TEAMS = [
    "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN",
    "DET", "GB", "HOU", "IND", "JAX", "KC", "LV", "LAC", "LAR", "MIA",
    "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SF", "SEA", "TB",
    "TEN", "WSH"
]

admin_id = str(uuid.uuid4())
admin_user = User(
    id=admin_id,
    username="admin",
    email="admin@survivorleague.com",
    password_hash=hashlib.sha256(os.getenv("ADMIN_PASSWORD", "defaultpass").encode()).hexdigest(),
    role=UserRole.ADMIN,
    created_at=datetime.now()
)
users_db[admin_id] = admin_user

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash

def create_token(user_id: str) -> str:
    return jwt.encode({"user_id": user_id}, SECRET_KEY, algorithm="HS256")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload["user_id"]
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(user_id: str = Depends(verify_token)) -> User:
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]

def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.post("/auth/register")
async def register(request: RegisterRequest):
    for user in users_db.values():
        if user.username == request.username:
            raise HTTPException(status_code=400, detail="Username already exists")
    
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username=request.username,
        email=request.email,
        password_hash=hash_password(request.password),
        created_at=datetime.now()
    )
    users_db[user_id] = user
    
    token = create_token(user_id)
    return {"token": token, "user": {"id": user.id, "username": user.username, "role": user.role}}

@app.post("/auth/login")
async def login(request: LoginRequest):
    for user in users_db.values():
        if user.username == request.username and verify_password(request.password, user.password_hash):
            token = create_token(user.id)
            return {"token": token, "user": {"id": user.id, "username": user.username, "role": user.role}}
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/auth/reset-password")
async def reset_password(request: ResetPasswordRequest):
    user_found = None
    for user in users_db.values():
        if user.username == request.username and user.email == request.email:
            user_found = user
            break
    
    if not user_found:
        raise HTTPException(status_code=404, detail="User not found with provided username and email")
    
    user_found.password_hash = hash_password(request.new_password)
    users_db[user_found.id] = user_found
    
    return {"message": "Password reset successfully"}

@app.post("/players")
async def create_player(request: CreatePlayerRequest, user: User = Depends(get_current_user)):
    player_id = str(uuid.uuid4())
    player = Player(
        id=player_id,
        user_id=user.id,
        entry_name=request.entry_name
    )
    players_db[player_id] = player
    return player

@app.get("/players/me")
async def get_my_players(user: User = Depends(get_current_user)):
    return [player for player in players_db.values() if player.user_id == user.id]

@app.get("/players")
async def get_all_players():
    return list(players_db.values())

@app.post("/players/{player_id}/picks")
async def make_pick(player_id: str, request: MakePickRequest, user: User = Depends(get_current_user)):
    if player_id not in players_db:
        raise HTTPException(status_code=404, detail="Player not found")
    
    player = players_db[player_id]
    if player.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your player")
    
    if game_settings.picks_locked:
        raise HTTPException(status_code=400, detail="Picks are locked for this week")
    
    if request.team not in NFL_TEAMS:
        raise HTTPException(status_code=400, detail="Invalid team")
    
    used_teams = [pick.team for pick in picks_db if pick.player_id == player_id]
    if request.team in used_teams:
        raise HTTPException(status_code=400, detail="Team already used")
    
    existing_pick = next((pick for pick in picks_db if pick.player_id == player_id and pick.week == game_settings.current_week), None)
    if existing_pick:
        raise HTTPException(status_code=400, detail="Already picked for this week")
    
    pick_id = str(uuid.uuid4())
    pick = WeeklyPick(
        id=pick_id,
        player_id=player_id,
        week=game_settings.current_week,
        team=request.team,
        is_underdog=request.is_underdog,
        created_at=datetime.now()
    )
    picks_db.append(pick)
    return pick

@app.post("/players/{player_id}/redemption-picks")
async def make_redemption_picks(player_id: str, request: RedemptionPickRequest, user: User = Depends(get_current_user)):
    if player_id not in players_db:
        raise HTTPException(status_code=404, detail="Player not found")
    
    player = players_db[player_id]
    if player.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your player")
    
    if player.status != PlayerStatus.REDEMPTION:
        raise HTTPException(status_code=400, detail="Player not in redemption round")
    
    if game_settings.picks_locked:
        raise HTTPException(status_code=400, detail="Picks are locked for this week")
    
    teams = [request.team1, request.team2, request.underdog_team]
    for team in teams:
        if team not in NFL_TEAMS:
            raise HTTPException(status_code=400, detail=f"Invalid team: {team}")
    
    used_teams = [pick.team for pick in picks_db if pick.player_id == player_id]
    for team in teams:
        if team in used_teams:
            raise HTTPException(status_code=400, detail=f"Team already used: {team}")
    
    underdog_teams = [ut.team for ut in underdog_teams_db if ut.week == game_settings.current_week]
    if request.underdog_team not in underdog_teams:
        raise HTTPException(status_code=400, detail="Invalid underdog team")
    
    picks = []
    for i, team in enumerate([request.team1, request.team2, request.underdog_team]):
        pick_id = str(uuid.uuid4())
        pick = WeeklyPick(
            id=pick_id,
            player_id=player_id,
            week=game_settings.current_week,
            team=team,
            is_redemption=True,
            is_underdog=(team == request.underdog_team),
            created_at=datetime.now()
        )
        picks_db.append(pick)
        picks.append(pick)
    
    return picks

@app.get("/players/{player_id}/picks")
async def get_player_picks(player_id: str):
    return [pick for pick in picks_db if pick.player_id == player_id]

@app.post("/players/{player_id}/buyback")
async def buyback(player_id: str, request: BuybackRequest, user: User = Depends(get_current_user)):
    if player_id not in players_db:
        raise HTTPException(status_code=404, detail="Player not found")
    
    player = players_db[player_id]
    if player.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your player")
    
    if player.status != PlayerStatus.ELIMINATED:
        raise HTTPException(status_code=400, detail="Player not eliminated")
    
    if player.eliminated_week is None or request.week != player.eliminated_week + 1:
        raise HTTPException(status_code=400, detail="Can only buyback the week after elimination")
    
    cost = game_settings.buyback_multiplier * request.week
    
    player.status = PlayerStatus.ACTIVE
    player.buybacks += 1
    players_db[player_id] = player
    
    return {"message": f"Buyback successful for week {request.week}", "cost": cost}

@app.post("/admin/underdog-teams")
async def add_underdog_team(team: str, week: int, admin: User = Depends(require_admin)):
    if team not in NFL_TEAMS:
        raise HTTPException(status_code=400, detail="Invalid team")
    
    underdog_team = UnderdogTeam(team=team, week=week)
    underdog_teams_db.append(underdog_team)
    return underdog_team

@app.get("/admin/underdog-teams/{week}")
async def get_underdog_teams(week: int):
    return [ut.team for ut in underdog_teams_db if ut.week == week]

@app.post("/admin/eliminate-player")
async def eliminate_player(player_id: str, admin: User = Depends(require_admin)):
    if player_id not in players_db:
        raise HTTPException(status_code=404, detail="Player not found")
    
    player = players_db[player_id]
    player.status = PlayerStatus.REDEMPTION
    player.eliminated_week = game_settings.current_week
    player.redemption_visits += 1
    players_db[player_id] = player
    
    return {"message": f"Player {player.entry_name} moved to redemption round"}

@app.post("/admin/advance-week")
async def advance_week(admin: User = Depends(require_admin)):
    game_settings.current_week += 1
    game_settings.picks_locked = False
    return {"current_week": game_settings.current_week}

@app.post("/admin/lock-picks")
async def lock_picks(admin: User = Depends(require_admin)):
    game_settings.picks_locked = True
    return {"message": "Picks locked"}

@app.post("/admin/unlock-picks")
async def unlock_picks(admin: User = Depends(require_admin)):
    game_settings.picks_locked = False
    return {"message": "Picks unlocked"}

@app.get("/admin/settings")
async def get_settings():
    return game_settings

@app.get("/leaderboard")
async def get_leaderboard():
    standings = []
    for player in players_db.values():
        user = users_db[player.user_id]
        player_picks = [pick for pick in picks_db if pick.player_id == player.id]
        
        standings.append({
            "player_id": player.id,
            "entry_name": player.entry_name,
            "username": user.username,
            "status": player.status,
            "weeks_survived": len([pick for pick in player_picks if not pick.is_redemption]),
            "redemption_visits": player.redemption_visits,
            "buybacks": player.buybacks,
            "eliminated_week": player.eliminated_week
        })
    
    standings.sort(key=lambda x: (
        x["status"] != "active",
        -x["weeks_survived"],
        x["redemption_visits"],
        x["buybacks"]
    ))
    
    return standings

@app.post("/admin/record-result")
async def record_game_result(request: RecordResultRequest, admin: User = Depends(require_admin)):
    if request.winning_team not in NFL_TEAMS or request.losing_team not in NFL_TEAMS:
        raise HTTPException(status_code=400, detail="Invalid team")
    
    if request.winning_team == request.losing_team:
        raise HTTPException(status_code=400, detail="Teams cannot be the same")
    
    existing_result = next((
        result for result in game_results_db 
        if result.week == game_settings.current_week and 
        ((result.winning_team == request.winning_team and result.losing_team == request.losing_team) or
         (result.winning_team == request.losing_team and result.losing_team == request.winning_team))
    ), None)
    
    if existing_result:
        raise HTTPException(status_code=400, detail="Result already recorded for these teams this week")
    
    result_id = str(uuid.uuid4())
    game_result = GameResult(
        id=result_id,
        week=game_settings.current_week,
        winning_team=request.winning_team,
        losing_team=request.losing_team,
        created_at=datetime.now()
    )
    game_results_db.append(game_result)
    
    return game_result

@app.post("/admin/process-week-results")
async def process_week_results(admin: User = Depends(require_admin)):
    """Process all picks for the current week and eliminate players with incorrect picks"""
    current_week = game_settings.current_week
    
    week_picks = [pick for pick in picks_db if pick.week == current_week]
    
    week_results = [result for result in game_results_db if result.week == current_week]
    
    eliminated_players = []
    processed_picks = 0
    
    for pick in week_picks:
        player = players_db.get(pick.player_id)
        if not player or player.status == PlayerStatus.ELIMINATED:
            continue
            
        team_lost = False
        for result in week_results:
            if result.losing_team == pick.team:
                team_lost = True
                break
        
        if team_lost:
            if player.status == PlayerStatus.REDEMPTION:
                player.status = PlayerStatus.ELIMINATED
                player.eliminated_week = current_week
            else:
                player.status = PlayerStatus.REDEMPTION
                player.eliminated_week = current_week
                player.redemption_visits += 1
            
            players_db[pick.player_id] = player
            eliminated_players.append({
                "player_id": player.id,
                "entry_name": player.entry_name,
                "picked_team": pick.team,
                "new_status": player.status
            })
        
        processed_picks += 1
    
    return {
        "message": f"Processed {processed_picks} picks for week {current_week}",
        "eliminated_players": eliminated_players,
        "total_eliminated": len(eliminated_players)
    }

@app.get("/admin/game-results/{week}")
async def get_week_results(week: int):
    """Get all game results for a specific week"""
    return [result for result in game_results_db if result.week == week]

@app.get("/admin/game-results")
async def get_all_results():
    """Get all game results"""
    return game_results_db

@app.delete("/admin/game-results/{result_id}")
async def delete_game_result(result_id: str, admin: User = Depends(require_admin)):
    """Delete a game result (in case of mistakes)"""
    global game_results_db
    original_length = len(game_results_db)
    game_results_db = [result for result in game_results_db if result.id != result_id]
    
    if len(game_results_db) == original_length:
        raise HTTPException(status_code=404, detail="Game result not found")
    
    return {"message": "Game result deleted"}

@app.get("/teams")
async def get_teams():
    return NFL_TEAMS
