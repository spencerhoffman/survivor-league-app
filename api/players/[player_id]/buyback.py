from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import asyncio
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from utils.database import get_player_by_id, update_player, get_game_settings
from utils.auth import verify_token
from utils.validation import validate_week, validate_player_ownership

class handler(BaseHTTPRequestHandler):
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
            
            query_string = self.path.split('?', 1)[1] if '?' in self.path else ''
            query_params = urllib.parse.parse_qs(query_string)
            player_id = query_params.get('player_id', [None])[0]
            
            if not player_id:
                self.send_error(400, "Player ID is required")
                return
            
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            try:
                request_data = json.loads(post_data)
                week = request_data.get('week')
            except json.JSONDecodeError:
                form_data = urllib.parse.parse_qs(post_data)
                week = int(form_data.get('week', [0])[0]) if form_data.get('week', [None])[0] else None
            
            if not week:
                self.send_error(400, "week required")
                return
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._buyback_player(player_id, user, week))
            loop.close()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            self.send_error(400 if any(msg in str(e) for msg in ["Player not found", "must be eliminated", "Can only buy back"]) else 500, str(e))
    
    async def _buyback_player(self, player_id, user, week):
        player = await get_player_by_id(player_id)
        if not player:
            raise Exception("Player not found")
        
        validate_player_ownership(player['user_id'], user['id'])
        
        if player['status'] != 'ELIMINATED':
            raise Exception("Player must be eliminated to buy back in")
        
        settings = await get_game_settings()
        validate_week(week, settings.get('current_week', 1))
        
        if week != player.get('eliminated_week'):
            raise Exception("Can only buy back in the week you were eliminated")
        
        buyback_cost = settings.get('entry_fee', 35.0) * settings.get('buyback_multiplier', 3)
        new_pot_contributions = player.get('pot_contributions', 0) + buyback_cost
        
        updates = {
            'status': 'REDEMPTION',
            'pot_contributions': new_pot_contributions
        }
        
        await update_player(player_id, updates)
        
        return {
            "message": "Player bought back successfully",
            "status": "REDEMPTION",
            "buyback_cost": buyback_cost,
            "total_contributions": new_pot_contributions
        }
