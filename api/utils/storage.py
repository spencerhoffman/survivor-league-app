import os
from typing import Optional
from fastapi import UploadFile, HTTPException
from vercel_blob import put, delete
import uuid

BLOB_READ_WRITE_TOKEN = os.getenv("BLOB_READ_WRITE_TOKEN")
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024

def validate_image_file(file: UploadFile):
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB.")
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed.")

async def save_profile_picture(file: UploadFile, user_id: str) -> str:
    validate_image_file(file)
    
    file_extension = file.filename.split('.')[-1] if file.filename else 'jpg'
    filename = f"profile-{user_id}-{uuid.uuid4().hex[:8]}.{file_extension}"
    
    file_content = await file.read()
    
    try:
        blob_response = put(
            pathname=f"profile-pictures/{filename}",
            body=file_content,
            options={
                "access": "public",
                "token": BLOB_READ_WRITE_TOKEN
            }
        )
        return blob_response.url
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

async def delete_profile_picture(url: str) -> bool:
    try:
        pathname = url.split('/')[-2:]
        pathname = '/'.join(pathname)
        delete(
            url=url,
            options={"token": BLOB_READ_WRITE_TOKEN}
        )
        return True
    except Exception:
        return False
