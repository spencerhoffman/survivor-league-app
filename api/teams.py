from fastapi import FastAPI
from fastapi.responses import JSONResponse
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.database import NFL_TEAMS

app = FastAPI()

@app.get("/")
async def get_teams():
    return JSONResponse(NFL_TEAMS)

def handler(request):
    return app(request)
