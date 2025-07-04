from http.server import BaseHTTPRequestHandler
import json
import uuid
import os
import sys
import asyncio
import cgi
from io import BytesIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.database import get_user_by_username, create_user
from utils.auth import hash_password, create_token
from utils.storage import save_profile_picture

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_type = self.headers.get('Content-Type', '')
            if not content_type.startswith('multipart/form-data'):
                self.send_error(400, "Content-Type must be multipart/form-data")
                return
            
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            form = cgi.FieldStorage(
                fp=BytesIO(post_data),
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )
            
            username = form.getvalue('username')
            email = form.getvalue('email')
            password = form.getvalue('password')
            profile_picture = form['profile_picture']
            
            if not all([username, email, password, profile_picture]):
                self.send_error(400, "Missing required fields")
                return
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._register(username, email, password, profile_picture))
            loop.close()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, str(e))
    
    async def _register(self, username, email, password, profile_picture):
        existing_user = await get_user_by_username(username)
        if existing_user:
            raise Exception("Username already exists")
        
        user_id = str(uuid.uuid4())
        
        class MockUploadFile:
            def __init__(self, field_storage):
                self.filename = field_storage.filename
                self.content_type = field_storage.type
                self.file = field_storage.file
                self.size = None
            
            async def read(self):
                return self.file.read()
        
        mock_file = MockUploadFile(profile_picture)
        profile_picture_url = await save_profile_picture(mock_file, user_id)
        
        user_data = {
            'username': username,
            'email': email,
            'password_hash': hash_password(password),
            'profile_picture_url': profile_picture_url
        }
        
        created_user_id = await create_user(user_data)
        
        token = create_token(created_user_id)
        return {
            "token": token, 
            "user": {
                "id": created_user_id, 
                "username": username, 
                "email": email, 
                "role": "USER", 
                "profile_picture_url": profile_picture_url
            }
        }
