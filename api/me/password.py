from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.auth import get_current_user, verify_password, hash_password
from utils.database import update_user

app = FastAPI()

class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@app.put("/")
async def update_password(request: UpdatePasswordRequest, user: dict = Depends(get_current_user)):
    if not verify_password(request.current_password, user['password_hash']):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    new_password_hash = hash_password(request.new_password)
    await update_user(user['id'], {'password_hash': new_password_hash})
    
    return JSONResponse({"message": "Password updated successfully"})

def handler(request):
    return app(request)
