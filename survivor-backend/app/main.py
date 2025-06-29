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
    financial_contribution: float = 0.0
    eliminated_teams: List[str] = []  # Teams permanently eliminated from future picks

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
    outcome: str  # "win", "loss", or "bye"
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
    underdog_team1: str
    underdog_team2: str

class BuybackRequest(BaseModel):
    week: int

class RecordResultRequest(BaseModel):
    team: str
    outcome: str  # "win", "loss", or "bye"

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
    email="admin@example.com",
    password_hash=hashlib.sha256(os.getenv("ADMIN_PASSWORD", "admin123").encode()).hexdigest(),
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

@app.get("/me")
async def get_current_user_profile(user: User = Depends(get_current_user)):
    return user

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
    
    teams = [request.underdog_team1, request.underdog_team2]
    for team in teams:
        if team not in NFL_TEAMS:
            raise HTTPException(status_code=400, detail=f"Invalid team: {team}")
    
    used_teams = [pick.team for pick in picks_db if pick.player_id == player_id]
    for team in teams:
        if team in used_teams or team in player.eliminated_teams:
            raise HTTPException(status_code=400, detail=f"Team already used or eliminated: {team}")
    
    underdog_teams = [ut.team for ut in underdog_teams_db if ut.week == game_settings.current_week]
    for team in teams:
        if team not in underdog_teams:
            raise HTTPException(status_code=400, detail=f"Invalid underdog team: {team}")
    
    if request.underdog_team1 == request.underdog_team2:
        raise HTTPException(status_code=400, detail="Must pick two different underdog teams")
    
    picks = []
    for team in teams:
        pick_id = str(uuid.uuid4())
        pick = WeeklyPick(
            id=pick_id,
            player_id=player_id,
            week=game_settings.current_week,
            team=team,
            is_redemption=True,
            is_underdog=True,  # All redemption picks are underdog picks
            created_at=datetime.now()
        )
        picks_db.append(pick)
        picks.append(pick)
    
    return picks

@app.get("/players/{player_id}/picks")
async def get_player_picks(player_id: str):
    return [pick for pick in picks_db if pick.player_id == player_id]

@app.put("/players/{player_id}/picks/{pick_id}")
async def update_pick(player_id: str, pick_id: str, request: MakePickRequest, user: User = Depends(get_current_user)):
    if player_id not in players_db:
        raise HTTPException(status_code=404, detail="Player not found")
    
    player = players_db[player_id]
    if player.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your player")
    
    if game_settings.picks_locked:
        raise HTTPException(status_code=400, detail="Picks are locked for this week")
    
    pick = next((p for p in picks_db if p.id == pick_id and p.player_id == player_id), None)
    if not pick:
        raise HTTPException(status_code=404, detail="Pick not found")
    
    if request.team not in NFL_TEAMS:
        raise HTTPException(status_code=400, detail="Invalid team")
    
    used_teams = [p.team for p in picks_db if p.player_id == player_id and p.id != pick_id]
    if request.team in used_teams or request.team in player.eliminated_teams:
        raise HTTPException(status_code=400, detail="Team already used or eliminated")
    
    pick.team = request.team
    pick.is_underdog = request.is_underdog
    
    return pick

@app.delete("/players/{player_id}/picks/{pick_id}")
async def delete_pick(player_id: str, pick_id: str, user: User = Depends(get_current_user)):
    if player_id not in players_db:
        raise HTTPException(status_code=404, detail="Player not found")
    
    player = players_db[player_id]
    if player.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your player")
    
    if game_settings.picks_locked:
        raise HTTPException(status_code=400, detail="Picks are locked for this week")
    
    global picks_db
    original_length = len(picks_db)
    picks_db = [p for p in picks_db if not (p.id == pick_id and p.player_id == player_id)]
    
    if len(picks_db) == original_length:
        raise HTTPException(status_code=404, detail="Pick not found")
    
    return {"message": "Pick deleted"}

@app.get("/players/{player_id}/picks/current-week")
async def get_current_week_picks(player_id: str):
    current_week = game_settings.current_week
    return [pick for pick in picks_db if pick.player_id == player_id and pick.week == current_week]

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
    
    cost = 35.0  # Fixed $35 contribution
    
    player.status = PlayerStatus.ACTIVE
    player.buybacks += 1
    player.financial_contribution += cost
    players_db[player_id] = player
    
    return {"message": f"Buyback successful for week {request.week}", "cost": cost}

@app.post("/players/{player_id}/undo")
async def undo_contribution(player_id: str, request: BuybackRequest, user: User = Depends(get_current_user)):
    if player_id not in players_db:
        raise HTTPException(status_code=404, detail="Player not found")
    
    player = players_db[player_id]
    if player.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your player")
    
    cost = 35.0  # Fixed $35 contribution
    
    player.financial_contribution += cost
    players_db[player_id] = player
    
    return {"message": f"Undo contribution successful for week {request.week}", "cost": cost}

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
            "eliminated_week": player.eliminated_week,
            "financial_contribution": player.financial_contribution
        })
    
    standings.sort(key=lambda x: (
        x["status"] != "active",
        -x["weeks_survived"],
        x["redemption_visits"],
        x["buybacks"]
    ))
    
    return standings

@app.get("/picks/locked")
async def get_locked_picks():
    """Get all picks that are locked (from past weeks or current week if locked)"""
    current_week = game_settings.current_week
    locked_picks = []
    
    for pick in picks_db:
        if pick.week < current_week or (pick.week == current_week and game_settings.picks_locked):
            player = players_db.get(pick.player_id)
            if player:
                user = users_db.get(player.user_id)
                if user:
                    locked_picks.append({
                        "pick_id": pick.id,
                        "week": pick.week,
                        "team": pick.team,
                        "player_name": player.entry_name,
                        "username": user.username,
                        "is_redemption": pick.is_redemption,
                        "is_underdog": pick.is_underdog,
                        "created_at": pick.created_at.isoformat()
                    })
    
    locked_picks.sort(key=lambda x: (-x["week"], x["player_name"]))
    return locked_picks

@app.post("/admin/record-result")
async def record_game_result(request: RecordResultRequest, admin: User = Depends(require_admin)):
    if request.team not in NFL_TEAMS:
        raise HTTPException(status_code=400, detail="Invalid team")
    
    if request.outcome not in ["win", "loss", "bye"]:
        raise HTTPException(status_code=400, detail="Invalid outcome. Must be 'win', 'loss', or 'bye'")
    
    global game_results_db
    game_results_db = [
        result for result in game_results_db 
        if not (result.week == game_settings.current_week and result.team == request.team)
    ]
    
    result_id = str(uuid.uuid4())
    game_result = GameResult(
        id=result_id,
        week=game_settings.current_week,
        team=request.team,
        outcome=request.outcome,
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
    processed_players = set()
    
    player_picks = {}
    for pick in week_picks:
        if pick.player_id not in player_picks:
            player_picks[pick.player_id] = []
        player_picks[pick.player_id].append(pick)
    
    for player_id, picks in player_picks.items():
        player = players_db.get(player_id)
        if not player or player.status == PlayerStatus.ELIMINATED:
            continue
        
        if player.status == PlayerStatus.ACTIVE:
            for pick in picks:
                team_lost = any(result.team == pick.team and result.outcome == "loss" 
                              for result in week_results)
                if team_lost:
                    player.status = PlayerStatus.REDEMPTION
                    player.eliminated_week = current_week
                    player.redemption_visits += 1
                    players_db[player_id] = player
                    eliminated_players.append({
                        "player_id": player.id,
                        "entry_name": player.entry_name,
                        "picked_team": pick.team,
                        "new_status": player.status
                    })
                    break  # Only need one losing pick to move to redemption
        
        elif player.status == PlayerStatus.REDEMPTION:
            redemption_picks = [pick for pick in picks if pick.is_redemption]
            correct_picks = 0
            
            for pick in redemption_picks:
                if pick.team not in player.eliminated_teams:
                    player.eliminated_teams.append(pick.team)
                
                team_won = any(result.team == pick.team and result.outcome == "win" 
                             for result in week_results)
                if team_won:
                    correct_picks += 1
            
            if correct_picks == 0:
                player.status = PlayerStatus.ELIMINATED
                player.eliminated_week = current_week
                players_db[player_id] = player
                eliminated_players.append({
                    "player_id": player.id,
                    "entry_name": player.entry_name,
                    "picked_team": "redemption picks",
                    "new_status": player.status
                })
            else:
                player.status = PlayerStatus.ACTIVE
                players_db[player_id] = player
        
        processed_players.add(player_id)
    
    return {
        "message": f"Processed {len(processed_players)} players for week {current_week}",
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

@app.post("/admin/reset-league")
async def reset_league(admin: User = Depends(require_admin)):
    """Reset all league data - players, picks, results, underdog teams"""
    global players_db, picks_db, game_results_db, underdog_teams_db, game_settings
    
    admin_users = {user_id: user for user_id, user in users_db.items() if user.role == UserRole.ADMIN}
    users_db.clear()
    users_db.update(admin_users)
    
    players_db.clear()
    picks_db.clear()
    game_results_db.clear()
    underdog_teams_db.clear()
    
    game_settings.current_week = 1
    game_settings.entry_fee = 35
    game_settings.buyback_multiplier = 3
    game_settings.picks_locked = False
    
    return {
        "message": "League reset successfully",
        "cleared": {
            "players": True,
            "picks": True,
            "game_results": True,
            "underdog_teams": True,
            "non_admin_users": True
        },
        "reset_settings": {
            "current_week": game_settings.current_week,
            "picks_locked": game_settings.picks_locked
        }
    }

@app.get("/teams")
async def get_teams():
    return NFL_TEAMS
