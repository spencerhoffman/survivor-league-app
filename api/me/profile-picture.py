from fastapi import FastAPI, File, UploadFile, Depends
from fastapi.responses import JSONResponse
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.auth import get_current_user
from utils.storage import save_profile_picture
from utils.database import update_user

app = FastAPI()

@app.put("/")
async def update_profile_picture(profile_picture: UploadFile = File(...), user: dict = Depends(get_current_user)):
    profile_picture_url = await save_profile_picture(profile_picture, user['id'])
    await update_user(user['id'], {'profile_picture_url': profile_picture_url})
    
    return JSONResponse({
        "message": "Profile picture updated successfully", 
        "profile_picture_url": profile_picture_url
    })

def handler(request):
    return app(request)
