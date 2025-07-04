from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import asyncio
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.database import get_user_by_username
from utils.auth import verify_password, create_token

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            try:
                request_data = json.loads(post_data)
                username = request_data.get('username')
                password = request_data.get('password')
            except json.JSONDecodeError:
                form_data = urllib.parse.parse_qs(post_data)
                username = form_data.get('username', [None])[0]
                password = form_data.get('password', [None])[0]
            
            if not username or not password:
                self.send_error(400, "Username and password required")
                return
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._login(username, password))
            loop.close()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            self.send_error(401 if "Invalid credentials" in str(e) else 500, str(e))
    
    async def _login(self, username, password):
        user = await get_user_by_username(username)
        if not user or not verify_password(password, user['password_hash']):
            raise Exception("Invalid credentials")
        
        token = create_token(user['id'])
        return {
            "token": token,
            "user": {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "role": user['role'],
                "profile_picture_url": user.get('profile_picture_url')
            }
        }
