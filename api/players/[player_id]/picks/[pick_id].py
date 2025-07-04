from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from utils.database import get_pick_by_id, update_pick, delete_pick, get_player_by_id, NFL_TEAMS, get_game_settings
from utils.auth import get_current_user
from utils.validation import validate_week, validate_team, validate_player_ownership

app = FastAPI()

class UpdatePickRequest(BaseModel):
    team: str
    week: int

@app.put("/")
async def update_pick_endpoint(request: Request, pick_request: UpdatePickRequest, user: dict = Depends(get_current_user)):
    player_id = request.query_params.get('player_id')
    pick_id = request.query_params.get('pick_id')
    
    if not player_id or not pick_id:
        raise HTTPException(status_code=400, detail="Player ID and Pick ID are required")
    
    player = await get_player_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    validate_player_ownership(player['user_id'], user['id'])
    
    pick = await get_pick_by_id(pick_id)
    if not pick:
        raise HTTPException(status_code=404, detail="Pick not found")
    
    if pick['player_id'] != player_id:
        raise HTTPException(status_code=400, detail="Pick does not belong to this player")
    
    settings = await get_game_settings()
    validate_week(pick_request.week, settings.get('current_week', 1))
    validate_team(pick_request.team, NFL_TEAMS)
    
    if settings.get('picks_locked', False) and pick_request.week == settings.get('current_week', 1):
        raise HTTPException(status_code=400, detail="Picks are locked for the current week")
    
    if pick_request.team in player.get('eliminated_teams', []):
        raise HTTPException(status_code=400, detail="Cannot pick a team you've already been eliminated by")
    
    updates = {
        'team': pick_request.team,
        'week': pick_request.week
    }
    
    await update_pick(pick_id, updates)
    
    updated_pick = await get_pick_by_id(pick_id)
    return JSONResponse(updated_pick)

@app.delete("/")
async def delete_pick_endpoint(request: Request, user: dict = Depends(get_current_user)):
    player_id = request.query_params.get('player_id')
    pick_id = request.query_params.get('pick_id')
    
    if not player_id or not pick_id:
        raise HTTPException(status_code=400, detail="Player ID and Pick ID are required")
    
    player = await get_player_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    validate_player_ownership(player['user_id'], user['id'])
    
    pick = await get_pick_by_id(pick_id)
    if not pick:
        raise HTTPException(status_code=404, detail="Pick not found")
    
    if pick['player_id'] != player_id:
        raise HTTPException(status_code=400, detail="Pick does not belong to this player")
    
    settings = await get_game_settings()
    if settings.get('picks_locked', False) and pick['week'] == settings.get('current_week', 1):
        raise HTTPException(status_code=400, detail="Cannot delete picks for locked week")
    
    success = await delete_pick(pick_id)
    if not success:
        raise HTTPException(status_code=404, detail="Pick not found")
    
    return JSONResponse({"message": "Pick deleted"})

def handler(request):
    return app(request)
