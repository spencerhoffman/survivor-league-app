from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.auth import verify_token

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
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
            
            result = {
                "id": user['id'], 
                "username": user['username'], 
                "email": user['email'], 
                "role": user['role'], 
                "profile_picture_url": user.get('profile_picture_url')
            }
            
            if 'created_at' in user:
                result['created_at'] = user['created_at'].isoformat() if hasattr(user['created_at'], 'isoformat') else str(user['created_at'])
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, str(e))
