from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from utils.database import get_picks_by_player_id, get_player_by_id, create_pick, get_game_settings, NFL_TEAMS, get_picks_by_player_and_week
from utils.auth import get_current_user
from utils.validation import validate_week, validate_team, validate_player_ownership

app = FastAPI()

class MakePickRequest(BaseModel):
    team: str
    week: int

@app.get("/")
async def get_player_picks(request: Request):
    player_id = request.query_params.get('player_id')
    if not player_id:
        raise HTTPException(status_code=400, detail="Player ID is required")
    
    picks = await get_picks_by_player_id(player_id)
    return JSONResponse(picks)

@app.post("/")
async def make_pick(request: Request, pick_request: MakePickRequest, user: dict = get_current_user):
    player_id = request.query_params.get('player_id')
    if not player_id:
        raise HTTPException(status_code=400, detail="Player ID is required")
    
    player = await get_player_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    validate_player_ownership(player['user_id'], user['id'])
    
    settings = await get_game_settings()
    validate_week(pick_request.week, settings.get('current_week', 1))
    validate_team(pick_request.team, NFL_TEAMS)
    
    if settings.get('picks_locked', False) and pick_request.week == settings.get('current_week', 1):
        raise HTTPException(status_code=400, detail="Picks are locked for the current week")
    
    if player['status'] != 'ACTIVE':
        raise HTTPException(status_code=400, detail="Player must be active to make picks")
    
    if pick_request.team in player.get('eliminated_teams', []):
        raise HTTPException(status_code=400, detail="Cannot pick a team you've already been eliminated by")
    
    existing_picks = await get_picks_by_player_and_week(player_id, pick_request.week)
    non_redemption_picks = [p for p in existing_picks if not p.get('is_redemption', False)]
    if non_redemption_picks:
        raise HTTPException(status_code=400, detail="You already have a pick for this week")
    
    pick_data = {
        'player_id': player_id,
        'week': pick_request.week,
        'team': pick_request.team,
        'is_redemption': False
    }
    
    pick_id = await create_pick(pick_data)
    
    pick_response = {
        'id': pick_id,
        'player_id': player_id,
        'week': pick_request.week,
        'team': pick_request.team,
        'is_redemption': False
    }
    
    return JSONResponse(pick_response)

def handler(request):
    return app(request)
