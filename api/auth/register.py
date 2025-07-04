from fastapi import FastAPI, Form, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import uuid
from datetime import datetime
from utils.database import get_user_by_username, create_user
from utils.auth import hash_password, create_token
from utils.storage import save_profile_picture

app = FastAPI()

@app.post("/")
async def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    profile_picture: UploadFile = File(...)
):
    existing_user = await get_user_by_username(username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user_id = str(uuid.uuid4())
    
    profile_picture_url = await save_profile_picture(profile_picture, user_id)
    
    user_data = {
        'username': username,
        'email': email,
        'password_hash': hash_password(password),
        'profile_picture_url': profile_picture_url
    }
    
    created_user_id = await create_user(user_data)
    
    token = create_token(created_user_id)
    return JSONResponse({
        "token": token, 
        "user": {
            "id": created_user_id, 
            "username": username, 
            "email": email, 
            "role": "USER", 
            "profile_picture_url": profile_picture_url
        }
    })

def handler(request):
    return app(request)
