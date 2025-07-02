from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, date
from enum import Enum
import uuid
import jwt
import hashlib
import os
import shutil
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from app.database import db
from app.services import UserService, PlayerService, PickService, GameResultService, UnderdogService, GameSettingsService
from app.models import User, Player, WeeklyPick, UnderdogTeam, GameResult, GameSettings, UserRole, PlayerStatus

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    await initialize_admin_user()
    yield
    await db.disconnect()

app = FastAPI(title="Survivor League API", lifespan=lifespan)

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
    teams: List[str]
    week: int

class BuybackRequest(BaseModel):
    week: int

class RecordResultRequest(BaseModel):
    team: str
    outcome: str  # "win", "loss", or "bye"

class ResetPasswordRequest(BaseModel):
    username: str
    email: str
    new_password: str

class UpdateGameSettingsRequest(BaseModel):
    entry_fee: Optional[int] = None
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

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024

NFL_TEAMS = [
    "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN",
    "DET", "GB", "HOU", "IND", "JAX", "KC", "LV", "LAC", "LAR", "MIA",
    "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SF", "SEA", "TB",
    "TEN", "WSH"
]

def validate_image_file(file: UploadFile) -> None:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed.")

def save_profile_picture(file: UploadFile, user_id: str) -> str:
    validate_image_file(file)
    
    file_extension = file.filename.split('.')[-1] if file.filename else 'jpg'
    filename = f"{user_id}_profile.{file_extension}"
    file_path = UPLOAD_DIR / filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return f"/uploads/{filename}"

async def initialize_admin_user():
    """Initialize admin user in database if not exists"""
    if not db.db_available:
        logging.warning("Database not available - skipping admin user initialization")
        return
        
    try:
        async with db.get_connection() as conn:
            result = await conn.execute(
                "SELECT id FROM users WHERE role = 'admin' LIMIT 1"
            )
            admin_exists = await result.fetchone()
            
            if not admin_exists:
                admin_id = str(uuid.uuid4())
                await conn.execute("""
                    INSERT INTO users (id, username, email, password_hash, role, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    admin_id,
                    "Spence", 
                    "spencerhhoffman@gmail.com",
                    hashlib.sha256(os.getenv("ADMIN_PASSWORD", "admin123").encode()).hexdigest(),
                    "admin",
                    datetime.now()
                ))
                await conn.commit()
    except Exception as e:
        logging.warning(f"Failed to initialize admin user: {e}")

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

async def get_current_user(user_id: str = Depends(verify_token)) -> User:
    user = await UserService.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

@app.get("/healthz")
async def healthz():
    db_status = "connected" if db.db_available else "unavailable"
    return {"status": "ok", "database": db_status}

@app.post("/auth/register")
async def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    profile_picture: UploadFile = File(...)
):
    existing_user = await UserService.get_by_username(username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user_id = str(uuid.uuid4())
    
    profile_picture_url = save_profile_picture(profile_picture, user_id)
    
    user = User(
        id=user_id,
        username=username,
        email=email,
        password_hash=hash_password(password),
        created_at=datetime.now(),
        profile_picture_url=profile_picture_url
    )
    await UserService.create(user)
    
    token = create_token(user_id)
    return {"token": token, "user": {"id": user.id, "username": user.username, "email": user.email, "role": user.role, "profile_picture_url": user.profile_picture_url}}

@app.post("/auth/login")
async def login(request: LoginRequest):
    user = await UserService.get_by_username(request.username)
    if user and verify_password(request.password, user.password_hash):
        token = create_token(user.id)
        return {"token": token, "user": {"id": user.id, "username": user.username, "role": user.role}}
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/auth/reset-password")
async def reset_password(request: ResetPasswordRequest):
    user_found = await UserService.get_by_username_and_email(request.username, request.email)
    
    if not user_found:
        raise HTTPException(status_code=404, detail="User not found with provided username and email")
    
    user_found.password_hash = hash_password(request.new_password)
    await UserService.update(user_found)
    
    return {"message": "Password reset successfully"}

@app.post("/players")
async def create_player(request: CreatePlayerRequest, user: User = Depends(get_current_user)):
    player_id = str(uuid.uuid4())
    player = Player(
        id=player_id,
        user_id=user.id,
        entry_name=request.entry_name,
        status=PlayerStatus.ACTIVE,
        eliminated_week=None,
        redemption_visits=0,
        entry_fee_paid=True,
        financial_contribution=float((await GameSettingsService.get()).entry_fee),
        eliminated_teams=[],
        created_at=datetime.now()
    )
    return await PlayerService.create(player)

@app.get("/me")
async def get_current_user_profile(user: User = Depends(get_current_user)):
    return {"id": user.id, "username": user.username, "email": user.email, "role": user.role, "profile_picture_url": user.profile_picture_url, "created_at": user.created_at}

@app.put("/me")
async def update_profile(request: UpdateProfileRequest, user: User = Depends(get_current_user)):
    if request.username is not None:
        existing_user = await UserService.get_by_username(request.username)
        if existing_user and existing_user.id != user.id:
            raise HTTPException(status_code=400, detail="Username already exists")
        user.username = request.username
    
    if request.email is not None:
        user.email = request.email
    
    await UserService.update(user)
    return {"message": "Profile updated successfully", "user": {"id": user.id, "username": user.username, "email": user.email, "role": user.role}}

@app.put("/me/password")
async def update_password(request: UpdatePasswordRequest, user: User = Depends(get_current_user)):
    if not verify_password(request.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    user.password_hash = hash_password(request.new_password)
    await UserService.update(user)
    return {"message": "Password updated successfully"}

@app.put("/me/profile-picture")
async def update_profile_picture(profile_picture: UploadFile = File(...), user: User = Depends(get_current_user)):
    profile_picture_url = save_profile_picture(profile_picture, user.id)
    user.profile_picture_url = profile_picture_url
    await UserService.update(user)
    return {"message": "Profile picture updated successfully", "profile_picture_url": profile_picture_url}

@app.get("/players/me")
async def get_my_players(user: User = Depends(get_current_user)):
    return await PlayerService.get_by_user_id(user.id)

@app.get("/players")
async def get_all_players():
    return await PlayerService.get_all()

@app.post("/players/{player_id}/picks")
async def make_pick(player_id: str, request: MakePickRequest, user: User = Depends(get_current_user)):
    player = await PlayerService.get_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    if player.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your player")
    
    if (await GameSettingsService.get()).picks_locked:
        raise HTTPException(status_code=400, detail="Picks are locked for this week")
    
    if request.team not in NFL_TEAMS:
        raise HTTPException(status_code=400, detail="Invalid team")
    
    all_picks = await PickService.get_by_player_and_week(player_id, 0)  # Get all picks for player
    used_teams = [pick.team for pick in all_picks]
    if request.team in used_teams:
        raise HTTPException(status_code=400, detail="Team already used")
    
    current_week_picks = await PickService.get_by_player_and_week(player_id, (await GameSettingsService.get()).current_week)
    existing_pick = current_week_picks[0] if current_week_picks else None
    if existing_pick:
        raise HTTPException(status_code=400, detail="Already picked for this week")
    
    pick_id = str(uuid.uuid4())
    pick = WeeklyPick(
        id=pick_id,
        player_id=player_id,
        week=(await GameSettingsService.get()).current_week,
        team=request.team,
        is_underdog=request.is_underdog,
        created_at=datetime.now()
    )
    await PickService.create(pick)
    return pick

@app.post("/players/{player_id}/redemption-picks")
async def make_redemption_picks(player_id: str, request: RedemptionPickRequest, user: User = Depends(get_current_user)):
    player = await PlayerService.get_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    if player.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your player")
    
    if player.status != PlayerStatus.REDEMPTION:
        raise HTTPException(status_code=400, detail="Player not in redemption round")
    
    if (await GameSettingsService.get()).picks_locked:
        raise HTTPException(status_code=400, detail="Picks are locked for this week")
    
    teams = request.teams
    if len(teams) != 2:
        raise HTTPException(status_code=400, detail="Must pick exactly 2 teams for redemption")
    
    for team in teams:
        if team not in NFL_TEAMS:
            raise HTTPException(status_code=400, detail=f"Invalid team: {team}")
    
    all_picks = await PickService.get_by_player_and_week(player_id, 0)  # Get all picks for player
    used_teams = [pick.team for pick in all_picks]
    for team in teams:
        if team in used_teams or team in player.eliminated_teams:
            raise HTTPException(status_code=400, detail=f"Team already used or eliminated: {team}")
    
    underdog_teams_list = await UnderdogService.get_by_week(request.week)
    underdog_teams = [ut.team for ut in underdog_teams_list]
    for team in teams:
        if team not in underdog_teams:
            raise HTTPException(status_code=400, detail=f"Invalid underdog team: {team}")
    
    if teams[0] == teams[1]:
        raise HTTPException(status_code=400, detail="Must pick two different underdog teams")
    
    picks = []
    for team in teams:
        pick_id = str(uuid.uuid4())
        pick = WeeklyPick(
            id=pick_id,
            player_id=player_id,
            week=request.week,
            team=team,
            is_redemption=True,
            is_underdog=True,  # All redemption picks are underdog picks
            created_at=datetime.now()
        )
        await PickService.create(pick)
        picks.append(pick)
    
    return picks

@app.get("/players/{player_id}/picks")
async def get_player_picks(player_id: str):
    return await PickService.get_by_player_and_week(player_id, 0)  # Get all picks for player

@app.put("/players/{player_id}/picks/{pick_id}")
async def update_pick(player_id: str, pick_id: str, request: MakePickRequest, user: User = Depends(get_current_user)):
    player = await PlayerService.get_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    if player.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your player")
    
    if (await GameSettingsService.get()).picks_locked:
        raise HTTPException(status_code=400, detail="Picks are locked for this week")
    
    all_picks = await PickService.get_by_player_and_week(player_id, 0)  # Get all picks for player
    pick = next((p for p in all_picks if p.id == pick_id), None)
    if not pick:
        raise HTTPException(status_code=404, detail="Pick not found")
    
    if request.team not in NFL_TEAMS:
        raise HTTPException(status_code=400, detail="Invalid team")
    
    all_picks = await PickService.get_by_player_and_week(player_id, 0)  # Get all picks for player
    used_teams = [p.team for p in all_picks if p.id != pick_id]
    if request.team in used_teams or request.team in player.eliminated_teams:
        raise HTTPException(status_code=400, detail="Team already used or eliminated")
    
    pick.team = request.team
    pick.is_underdog = request.is_underdog
    await PickService.update(pick)
    
    return pick

@app.delete("/players/{player_id}/picks/{pick_id}")
async def delete_pick(player_id: str, pick_id: str, user: User = Depends(get_current_user)):
    player = await PlayerService.get_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    if player.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your player")
    
    if (await GameSettingsService.get()).picks_locked:
        raise HTTPException(status_code=400, detail="Picks are locked for this week")
    
    success = await PickService.delete(pick_id)
    if not success:
        raise HTTPException(status_code=404, detail="Pick not found")
    
    return {"message": "Pick deleted"}

@app.get("/players/{player_id}/picks/current-week")
async def get_current_week_picks(player_id: str):
    settings = await GameSettingsService.get()
    return await PickService.get_by_player_and_week(player_id, settings.current_week)

@app.post("/players/{player_id}/buyback")
async def buyback(player_id: str, request: BuybackRequest, user: User = Depends(get_current_user)):
    player = await PlayerService.get_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    if player.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your player")
    
    if player.status not in [PlayerStatus.ELIMINATED, PlayerStatus.REDEMPTION]:
        raise HTTPException(status_code=400, detail="Player must be eliminated or in redemption to buyback")
    
    if player.eliminated_week is None or request.week <= player.eliminated_week:
        raise HTTPException(status_code=400, detail="Can only buyback in weeks after elimination")
    
    cost = request.week * (await GameSettingsService.get()).buyback_multiplier  # Dynamic cost based on week
    
    player.status = PlayerStatus.ACTIVE
    player.buybacks += 1
    player.financial_contribution += cost
    await PlayerService.update(player)
    
    return {"message": f"Buyback successful for week {request.week}", "cost": cost}

@app.post("/players/{player_id}/undo")
async def undo_contribution(player_id: str, request: BuybackRequest, user: User = Depends(get_current_user)):
    player = await PlayerService.get_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    if player.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your player")
    
    cost = request.week * (await GameSettingsService.get()).buyback_multiplier  # Dynamic cost based on week
    
    player.financial_contribution += cost
    await PlayerService.update(player)
    
    return {"message": f"Undo contribution successful for week {request.week}", "cost": cost}

@app.post("/admin/underdog-teams")
async def add_underdog_team(request: dict, admin: User = Depends(require_admin)):
    teams = request.get("teams", [])
    week = request.get("week", (await GameSettingsService.get()).current_week)
    
    added_teams = []
    for team in teams:
        if team not in NFL_TEAMS:
            raise HTTPException(status_code=400, detail=f"Invalid team: {team}")
        
        underdog_team = UnderdogTeam(
            id=str(uuid.uuid4()),
            team=team, 
            week=week,
            created_at=datetime.now()
        )
        await UnderdogService.create(underdog_team)
        added_teams.append(underdog_team)
    
    return {"teams": [t.team for t in added_teams], "week": week}

@app.get("/admin/underdog-teams/{week}")
async def get_underdog_teams(week: int):
    underdog_teams = await UnderdogService.get_by_week(week)
    return [ut.team for ut in underdog_teams]

@app.post("/admin/eliminate-player")
async def eliminate_player(player_id: str, admin: User = Depends(require_admin)):
    player = await PlayerService.get_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    player.status = PlayerStatus.REDEMPTION
    player.eliminated_week = (await GameSettingsService.get()).current_week
    player.redemption_visits += 1
    await PlayerService.update(player)
    
    return {"message": f"Player {player.entry_name} moved to redemption round"}

@app.post("/admin/advance-week")
async def advance_week(admin: User = Depends(require_admin)):
    settings = await GameSettingsService.get()
    settings.current_week += 1
    settings.picks_locked = False
    await GameSettingsService.update(settings)
    return {"current_week": settings.current_week}

@app.post("/admin/lock-picks")
async def lock_picks(admin: User = Depends(require_admin)):
    settings = await GameSettingsService.get()
    settings.picks_locked = True
    await GameSettingsService.update(settings)
    return {"message": "Picks locked"}

@app.post("/admin/unlock-picks")
async def unlock_picks(admin: User = Depends(require_admin)):
    settings = await GameSettingsService.get()
    settings.picks_locked = False
    await GameSettingsService.update(settings)
    return {"message": "Picks unlocked"}

@app.get("/admin/settings")
async def get_settings():
    return await GameSettingsService.get()

@app.put("/admin/settings")
async def update_game_settings(request: UpdateGameSettingsRequest, admin: User = Depends(require_admin)):
    settings = await GameSettingsService.get()
    if request.entry_fee is not None:
        settings.entry_fee = request.entry_fee
    if request.buyback_multiplier is not None:
        settings.buyback_multiplier = request.buyback_multiplier
    await GameSettingsService.update(settings)
    return settings

@app.get("/admin/users")
async def get_all_users(admin: User = Depends(require_admin)):
    users = await UserService.get_all()
    return [{"id": user.id, "username": user.username, "email": user.email, "role": user.role} 
            for user in users]

@app.put("/admin/users/role")
async def update_user_role(request: UpdateUserRoleRequest, admin: User = Depends(require_admin)):
    user = await UserService.get_by_id(request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role = request.role
    await UserService.update(user)
    
    return {"message": f"User {user.username} role updated to {request.role}"}

@app.put("/admin/teams")
async def update_teams(request: UpdateTeamsRequest, admin: User = Depends(require_admin)):
    global NFL_TEAMS
    if len(request.teams) == 0:
        raise HTTPException(status_code=400, detail="Teams list cannot be empty")
    
    NFL_TEAMS = request.teams
    return {"message": f"Teams updated successfully", "teams": NFL_TEAMS}

@app.get("/admin/teams")
async def get_teams_admin(admin: User = Depends(require_admin)):
    return {"teams": NFL_TEAMS}

@app.get("/leaderboard")
async def get_leaderboard():
    standings = []
    players = await PlayerService.get_all()
    
    for player in players:
        user = await UserService.get_by_id(player.user_id)
        if not user:
            continue
            
        player_picks = await PickService.get_by_player_and_week(player.id, 0)  # Get all picks for player
        
        standings.append({
            "player_id": player.id,
            "entry_name": player.entry_name,
            "username": user.username,
            "status": player.status,
            "weeks_survived": len([pick for pick in player_picks if not pick.is_redemption]),
            "redemption_visits": player.redemption_visits,
            "buybacks": getattr(player, 'buybacks', 0),
            "eliminated_week": player.eliminated_week,
            "financial_contribution": player.financial_contribution,
            "profile_picture_url": user.profile_picture_url
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
    settings = await GameSettingsService.get()
    current_week = settings.current_week
    locked_picks = []
    
    for week in range(1, current_week + 1):
        week_picks = await PickService.get_by_week(week)
        for pick in week_picks:
            if pick.week < current_week or (pick.week == current_week and settings.picks_locked):
                player = await PlayerService.get_by_id(pick.player_id)
                if player:
                    user = await UserService.get_by_id(player.user_id)
                    if user:
                        locked_picks.append({
                            "pick_id": pick.id,
                            "week": pick.week,
                            "team": pick.team,
                            "player_name": player.entry_name,
                            "username": user.username,
                            "is_redemption": pick.is_redemption,
                            "is_underdog": getattr(pick, 'is_underdog', False),
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
    
    existing_results = await GameResultService.get_by_week((await GameSettingsService.get()).current_week)
    for result in existing_results:
        if result.team == request.team:
            await GameResultService.delete(result.id)
    
    result_id = str(uuid.uuid4())
    game_result = GameResult(
        id=result_id,
        week=(await GameSettingsService.get()).current_week,
        team=request.team,
        outcome=request.outcome,
        created_at=datetime.now()
    )
    await GameResultService.create(game_result)
    
    return game_result

@app.post("/admin/process-week-results")
async def process_week_results(admin: User = Depends(require_admin)):
    """Process all picks for the current week and eliminate players with incorrect picks"""
    settings = await GameSettingsService.get()
    current_week = settings.current_week
    
    week_picks = await PickService.get_by_week(current_week)
    week_results = await GameResultService.get_by_week(current_week)
    
    eliminated_players = []
    processed_players = set()
    
    player_picks = {}
    for pick in week_picks:
        if pick.player_id not in player_picks:
            player_picks[pick.player_id] = []
        player_picks[pick.player_id].append(pick)
    
    for player_id, picks in player_picks.items():
        player = await PlayerService.get_by_id(player_id)
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
                    await PlayerService.update(player)
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
            
            if correct_picks == len(redemption_picks) and len(redemption_picks) == 2:
                player.status = PlayerStatus.ACTIVE
                await PlayerService.update(player)
            else:
                player.status = PlayerStatus.ELIMINATED
                player.eliminated_week = current_week
                await PlayerService.update(player)
                eliminated_players.append({
                    "player_id": player.id,
                    "entry_name": player.entry_name,
                    "picked_team": "redemption picks",
                    "new_status": player.status
                })
        
        processed_players.add(player_id)
    
    return {
        "message": f"Processed {len(processed_players)} players for week {current_week}",
        "eliminated_players": eliminated_players,
        "total_eliminated": len(eliminated_players)
    }

@app.get("/admin/game-results/{week}")
async def get_week_results(week: int):
    """Get all game results for a specific week"""
    return await GameResultService.get_by_week(week)

@app.get("/admin/game-results")
async def get_all_results():
    """Get all game results"""
    return await GameResultService.get_all()

@app.delete("/admin/game-results/{result_id}")
async def delete_game_result(result_id: str, admin: User = Depends(require_admin)):
    """Delete a game result (in case of mistakes)"""
    success = await GameResultService.delete(result_id)
    if not success:
        raise HTTPException(status_code=404, detail="Game result not found")
    
    return {"message": "Game result deleted"}

@app.post("/admin/reset-league")
async def reset_league(admin: User = Depends(require_admin)):
    """Reset all league data - players, picks, results, underdog teams"""
    
    all_users = await UserService.get_all()
    admin_users = [user for user in all_users if user.role == UserRole.ADMIN]
    
    await db.create_tables()
    
    for admin_user in admin_users:
        await UserService.create(admin_user)
    
    settings = GameSettings()
    settings.current_week = 1
    settings.entry_fee = 35
    settings.buyback_multiplier = 3
    settings.picks_locked = False
    await GameSettingsService.update(settings)
    
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
            "current_week": settings.current_week,
            "picks_locked": settings.picks_locked
        }
    }

@app.get("/uploads/{filename}")
async def get_uploaded_file(filename: str):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

@app.get("/teams")
async def get_teams():
    return NFL_TEAMS
