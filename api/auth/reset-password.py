from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import get_user_by_username, update_user
from utils.auth import hash_password

app = FastAPI()

class ResetPasswordRequest(BaseModel):
    username: str
    email: str
    new_password: str

@app.post("/")
async def reset_password(request: ResetPasswordRequest):
    user = await get_user_by_username(request.username)
    if not user or user['email'] != request.email:
        raise HTTPException(status_code=404, detail="User not found or email mismatch")
    
    new_password_hash = hash_password(request.new_password)
    await update_user(user['id'], {'password_hash': new_password_hash})
    
    return JSONResponse({"message": "Password reset successfully"})

def handler(request):
    return app(request)
