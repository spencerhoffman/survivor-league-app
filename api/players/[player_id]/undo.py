from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.database import get_player_by_id, update_player, get_picks_by_player_and_week, delete_pick, get_game_settings
from utils.auth import require_admin

app = FastAPI()

@app.post("/")
async def undo_elimination(request: Request, admin: dict = Depends(require_admin)):
    player_id = request.query_params.get('player_id')
    if not player_id:
        raise HTTPException(status_code=400, detail="Player ID is required")
    
    player = await get_player_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    if player['status'] not in ['ELIMINATED', 'REDEMPTION']:
        raise HTTPException(status_code=400, detail="Player must be eliminated or in redemption to undo")
    
    eliminated_week = player.get('eliminated_week')
    if not eliminated_week:
        raise HTTPException(status_code=400, detail="No elimination week found")
    
    eliminated_teams = player.get('eliminated_teams', [])
    if eliminated_teams:
        eliminated_teams = eliminated_teams[:-1]
    
    updates = {
        'status': 'ACTIVE',
        'eliminated_week': None,
        'eliminated_teams': eliminated_teams
    }
    
    await update_player(player_id, updates)
    
    picks_to_delete = await get_picks_by_player_and_week(player_id, eliminated_week)
    redemption_picks = [p for p in picks_to_delete if p.get('is_redemption', False)]
    
    for pick in redemption_picks:
        await delete_pick(pick['id'])
    
    return JSONResponse({
        "message": "Player elimination undone successfully",
        "status": "ACTIVE",
        "eliminated_teams": eliminated_teams,
        "redemption_picks_deleted": len(redemption_picks)
    })

def handler(request):
    return app(request)
