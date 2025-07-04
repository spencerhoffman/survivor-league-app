from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import asyncio
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.database import get_user_by_username, update_user
from utils.auth import hash_password

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            try:
                request_data = json.loads(post_data)
                username = request_data.get('username')
                email = request_data.get('email')
                new_password = request_data.get('new_password')
            except json.JSONDecodeError:
                form_data = urllib.parse.parse_qs(post_data)
                username = form_data.get('username', [None])[0]
                email = form_data.get('email', [None])[0]
                new_password = form_data.get('new_password', [None])[0]
            
            if not username or not email or not new_password:
                self.send_error(400, "Username, email and new_password required")
                return
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._reset_password(username, email, new_password))
            loop.close()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            self.send_error(404 if "User not found" in str(e) else 500, str(e))
    
    async def _reset_password(self, username, email, new_password):
        user = await get_user_by_username(username)
        if not user or user['email'] != email:
            raise Exception("User not found or email mismatch")
        
        new_password_hash = hash_password(new_password)
        await update_user(user['id'], {'password_hash': new_password_hash})
        
        return {"message": "Password reset successfully"}
