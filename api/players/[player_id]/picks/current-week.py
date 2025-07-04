from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from utils.database import get_picks_by_player_and_week, get_game_settings

app = FastAPI()

@app.get("/")
async def get_current_week_picks(request: Request):
    player_id = request.query_params.get('player_id')
    if not player_id:
        raise HTTPException(status_code=400, detail="Player ID is required")
    
    settings = await get_game_settings()
    current_week = settings.get('current_week', 1)
    
    picks = await get_picks_by_player_and_week(player_id, current_week)
    return JSONResponse(picks)

def handler(request):
    return app(request)
