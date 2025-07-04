from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import asyncio
import cgi
from io import BytesIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.auth import verify_token
from utils.storage import save_profile_picture
from utils.database import update_user

class handler(BaseHTTPRequestHandler):
    def do_PUT(self):
        try:
            auth_header = self.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                self.send_error(401, "Authorization header required")
                return
            
            token = auth_header.split(' ')[1]
            user = verify_token(token)
            if not user:
                self.send_error(401, "Invalid token")
                return
            
            content_type = self.headers.get('Content-Type', '')
            if not content_type.startswith('multipart/form-data'):
                self.send_error(400, "Content-Type must be multipart/form-data")
                return
            
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            form = cgi.FieldStorage(
                fp=BytesIO(post_data),
                headers=self.headers,
                environ={'REQUEST_METHOD': 'PUT'}
            )
            
            profile_picture = form['profile_picture']
            if not profile_picture:
                self.send_error(400, "profile_picture required")
                return
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._update_profile_picture(user['id'], profile_picture))
            loop.close()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, str(e))
    
    async def _update_profile_picture(self, user_id, profile_picture):
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
        await update_user(user_id, {'profile_picture_url': profile_picture_url})
        
        return {
            "message": "Profile picture updated successfully", 
            "profile_picture_url": profile_picture_url
        }
