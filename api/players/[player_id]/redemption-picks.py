from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.database import get_player_by_id, create_pick, get_picks_by_player_and_week, get_game_settings, NFL_TEAMS, update_player
from utils.auth import get_current_user
from utils.validation import validate_week, validate_team, validate_player_ownership

app = FastAPI()

class RedemptionPickRequest(BaseModel):
    teams: List[str]
    week: int

@app.post("/")
async def make_redemption_picks(request: Request, pick_request: RedemptionPickRequest, user: dict = Depends(get_current_user)):
    player_id = request.query_params.get('player_id')
    if not player_id:
        raise HTTPException(status_code=400, detail="Player ID is required")
    
    player = await get_player_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    validate_player_ownership(player['user_id'], user['id'])
    
    if player['status'] != 'REDEMPTION':
        raise HTTPException(status_code=400, detail="Player must be in redemption status to make redemption picks")
    
    settings = await get_game_settings()
    validate_week(pick_request.week, settings.get('current_week', 1))
    
    if settings.get('picks_locked', False) and pick_request.week == settings.get('current_week', 1):
        raise HTTPException(status_code=400, detail="Picks are locked for the current week")
    
    if len(pick_request.teams) != 3:
        raise HTTPException(status_code=400, detail="Must select exactly 3 teams for redemption picks")
    
    for team in pick_request.teams:
        validate_team(team, NFL_TEAMS)
        if team in player.get('eliminated_teams', []):
            raise HTTPException(status_code=400, detail=f"Cannot pick team {team} - you've already been eliminated by them")
    
    if len(set(pick_request.teams)) != len(pick_request.teams):
        raise HTTPException(status_code=400, detail="Cannot select duplicate teams")
    
    existing_picks = await get_picks_by_player_and_week(player_id, pick_request.week)
    redemption_picks = [p for p in existing_picks if p.get('is_redemption', False)]
    if redemption_picks:
        raise HTTPException(status_code=400, detail="You already have redemption picks for this week")
    
    created_picks = []
    for team in pick_request.teams:
        pick_data = {
            'player_id': player_id,
            'week': pick_request.week,
            'team': team,
            'is_redemption': True
        }
        pick_id = await create_pick(pick_data)
        created_picks.append({
            'id': pick_id,
            'player_id': player_id,
            'week': pick_request.week,
            'team': team,
            'is_redemption': True
        })
    
    redemption_visits = player.get('redemption_visits', 0) + 1
    await update_player(player_id, {'redemption_visits': redemption_visits})
    
    return JSONResponse({
        "message": "Redemption picks created successfully",
        "picks": created_picks,
        "redemption_visits": redemption_visits
    })

def handler(request):
    return app(request)
