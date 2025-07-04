from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import asyncio
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.database import get_all_players, create_player, get_game_settings
from utils.auth import verify_token

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._get_players())
            loop.close()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def do_POST(self):
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
                entry_name = request_data.get('entry_name')
            except json.JSONDecodeError:
                form_data = urllib.parse.parse_qs(post_data)
                entry_name = form_data.get('entry_name', [None])[0]
            
            if not entry_name:
                self.send_error(400, "entry_name required")
                return
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._create_player(user, entry_name))
            loop.close()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, str(e))
    
    async def _get_players(self):
        players = await get_all_players()
        return players
    
    async def _create_player(self, user, entry_name):
        settings = await get_game_settings()
        
        player_data = {
            'user_id': user['id'],
            'entry_name': entry_name,
            'status': 'ACTIVE',
            'pot_contributions': settings.get('entry_fee', 35.0)
        }
        
        player_id = await create_player(player_data)
        
        return {
            'id': player_id,
            'user_id': user['id'],
            'entry_name': entry_name,
            'status': 'ACTIVE',
            'eliminated_week': None,
            'eliminated_teams': [],
            'redemption_visits': 0,
            'pot_contributions': settings.get('entry_fee', 35.0)
        }
