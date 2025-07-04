from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import get_user_by_username
from utils.auth import verify_password, create_token

app = FastAPI()

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/")
async def login(request: LoginRequest):
    user = await get_user_by_username(request.username)
    if not user or not verify_password(request.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user['id'])
    return JSONResponse({
        "token": token, 
        "user": {
            "id": user['id'], 
            "username": user['username'], 
            "role": user['role']
        }
    })

def handler(request):
    return app(request)
