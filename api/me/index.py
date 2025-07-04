from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.auth import get_current_user

app = FastAPI()

@app.get("/")
async def get_current_user_profile(user: dict = Depends(get_current_user)):
    return JSONResponse({
        "id": user['id'], 
        "username": user['username'], 
        "email": user['email'], 
        "role": user['role'], 
        "profile_picture_url": user.get('profile_picture_url'), 
        "created_at": user['created_at'].isoformat()
    })

def handler(request):
    return app(request)
