from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import get_all_players, create_player, get_game_settings
from utils.auth import get_current_user
from utils.validation import validate_player_ownership

app = FastAPI()

class CreatePlayerRequest(BaseModel):
    entry_name: str

@app.get("/")
async def get_all_players_endpoint():
    players = await get_all_players()
    return JSONResponse(players)

@app.post("/")
async def create_player_endpoint(request: CreatePlayerRequest, user: dict = Depends(get_current_user)):
    settings = await get_game_settings()
    
    player_data = {
        'user_id': user['id'],
        'entry_name': request.entry_name,
        'status': 'ACTIVE',
        'pot_contributions': settings.get('entry_fee', 35.0)
    }
    
    player_id = await create_player(player_data)
    
    player_response = {
        'id': player_id,
        'user_id': user['id'],
        'entry_name': request.entry_name,
        'status': 'ACTIVE',
        'eliminated_week': None,
        'eliminated_teams': [],
        'redemption_visits': 0,
        'pot_contributions': settings.get('entry_fee', 35.0)
    }
    
    return JSONResponse(player_response)

def handler(request):
    return app(request)
