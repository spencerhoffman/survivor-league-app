from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.database import get_player_by_id, update_player, get_game_settings
from utils.auth import get_current_user
from utils.validation import validate_week, validate_player_ownership

app = FastAPI()

class BuybackRequest(BaseModel):
    week: int

@app.post("/")
async def buyback_player(request: Request, buyback_request: BuybackRequest, user: dict = Depends(get_current_user)):
    player_id = request.query_params.get('player_id')
    if not player_id:
        raise HTTPException(status_code=400, detail="Player ID is required")
    
    player = await get_player_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    validate_player_ownership(player['user_id'], user['id'])
    
    if player['status'] != 'ELIMINATED':
        raise HTTPException(status_code=400, detail="Player must be eliminated to buy back in")
    
    settings = await get_game_settings()
    validate_week(buyback_request.week, settings.get('current_week', 1))
    
    if buyback_request.week != player.get('eliminated_week'):
        raise HTTPException(status_code=400, detail="Can only buy back in the week you were eliminated")
    
    buyback_cost = settings.get('entry_fee', 35.0) * settings.get('buyback_multiplier', 3)
    new_pot_contributions = player.get('pot_contributions', 0) + buyback_cost
    
    updates = {
        'status': 'REDEMPTION',
        'pot_contributions': new_pot_contributions
    }
    
    await update_player(player_id, updates)
    
    return JSONResponse({
        "message": "Player bought back successfully",
        "status": "REDEMPTION",
        "buyback_cost": buyback_cost,
        "total_contributions": new_pot_contributions
    })

def handler(request):
    return app(request)
