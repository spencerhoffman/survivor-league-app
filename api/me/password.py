from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import asyncio
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.auth import verify_token, verify_password, hash_password
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
            
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            try:
                request_data = json.loads(post_data)
                current_password = request_data.get('current_password')
                new_password = request_data.get('new_password')
            except json.JSONDecodeError:
                form_data = urllib.parse.parse_qs(post_data)
                current_password = form_data.get('current_password', [None])[0]
                new_password = form_data.get('new_password', [None])[0]
            
            if not current_password or not new_password:
                self.send_error(400, "current_password and new_password required")
                return
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._update_password(user, current_password, new_password))
            loop.close()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            self.send_error(400 if "Current password is incorrect" in str(e) else 500, str(e))
    
    async def _update_password(self, user, current_password, new_password):
        if not verify_password(current_password, user['password_hash']):
            raise Exception("Current password is incorrect")
        
        new_password_hash = hash_password(new_password)
        await update_user(user['id'], {'password_hash': new_password_hash})
        
        return {"message": "Password updated successfully"}
