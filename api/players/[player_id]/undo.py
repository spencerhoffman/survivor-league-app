from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import asyncio
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from utils.database import get_player_by_id, update_player, get_picks_by_player_and_week, delete_pick, get_game_settings
from utils.auth import verify_token

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            auth_header = self.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                self.send_error(401, "Authorization header required")
                return
            
            token = auth_header.split(' ')[1]
            user = verify_token(token)
            if not user or user.get('role') != 'ADMIN':
                self.send_error(403, "Admin access required")
                return
            
            query_string = self.path.split('?', 1)[1] if '?' in self.path else ''
            query_params = urllib.parse.parse_qs(query_string)
            player_id = query_params.get('player_id', [None])[0]
            
            if not player_id:
                self.send_error(400, "Player ID is required")
                return
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._undo_elimination(player_id))
            loop.close()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            self.send_error(400 if any(msg in str(e) for msg in ["Player not found", "must be eliminated", "No elimination week"]) else 500, str(e))
    
    async def _undo_elimination(self, player_id):
        player = await get_player_by_id(player_id)
        if not player:
            raise Exception("Player not found")
        
        if player['status'] not in ['ELIMINATED', 'REDEMPTION']:
            raise Exception("Player must be eliminated or in redemption to undo")
        
        eliminated_week = player.get('eliminated_week')
        if not eliminated_week:
            raise Exception("No elimination week found")
        
        eliminated_teams = player.get('eliminated_teams', [])
        if eliminated_teams:
            eliminated_teams = eliminated_teams[:-1]
        
        updates = {
            'status': 'ACTIVE',
            'eliminated_week': None,
            'eliminated_teams': eliminated_teams
        }
        
        await update_player(player_id, updates)
        
        picks_to_delete = await get_picks_by_player_and_week(player_id, eliminated_week)
        redemption_picks = [p for p in picks_to_delete if p.get('is_redemption', False)]
        
        for pick in redemption_picks:
            await delete_pick(pick['id'])
        
        return {
            "message": "Player elimination undone successfully",
            "status": "ACTIVE",
            "eliminated_teams": eliminated_teams,
            "redemption_picks_deleted": len(redemption_picks)
        }
