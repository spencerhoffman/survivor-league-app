from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import get_players_by_user_id
from utils.auth import get_current_user

app = FastAPI()

@app.get("/")
async def get_my_players(user: dict = Depends(get_current_user)):
    players = await get_players_by_user_id(user['id'])
    return JSONResponse(players)

def handler(request):
    return app(request)
