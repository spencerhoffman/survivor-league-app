from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import asyncio
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from utils.database import get_picks_by_player_id, get_player_by_id, create_pick, get_game_settings, NFL_TEAMS, get_picks_by_player_and_week
from utils.auth import verify_token
from utils.validation import validate_week, validate_team, validate_player_ownership

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            query_string = self.path.split('?', 1)[1] if '?' in self.path else ''
            query_params = urllib.parse.parse_qs(query_string)
            player_id = query_params.get('player_id', [None])[0]
            
            if not player_id:
                self.send_error(400, "Player ID is required")
                return
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._get_player_picks(player_id))
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
                team = request_data.get('team')
                week = request_data.get('week')
            except json.JSONDecodeError:
                form_data = urllib.parse.parse_qs(post_data)
                team = form_data.get('team', [None])[0]
                week = int(form_data.get('week', [0])[0]) if form_data.get('week', [None])[0] else None
            
            if not team or not week:
                self.send_error(400, "team and week required")
                return
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._make_pick(player_id, user, team, week))
            loop.close()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            self.send_error(400 if any(msg in str(e) for msg in ["Player not found", "Picks are locked", "already have a pick"]) else 500, str(e))
    
    async def _get_player_picks(self, player_id):
        picks = await get_picks_by_player_id(player_id)
        return picks
    
    async def _make_pick(self, player_id, user, team, week):
        player = await get_player_by_id(player_id)
        if not player:
            raise Exception("Player not found")
        
        validate_player_ownership(player['user_id'], user['id'])
        
        settings = await get_game_settings()
        validate_week(week, settings.get('current_week', 1))
        validate_team(team, NFL_TEAMS)
        
        if settings.get('picks_locked', False) and week == settings.get('current_week', 1):
            raise Exception("Picks are locked for the current week")
        
        if player['status'] != 'ACTIVE':
            raise Exception("Player must be active to make picks")
        
        if team in player.get('eliminated_teams', []):
            raise Exception("Cannot pick a team you've already been eliminated by")
        
        existing_picks = await get_picks_by_player_and_week(player_id, week)
        non_redemption_picks = [p for p in existing_picks if not p.get('is_redemption', False)]
        if non_redemption_picks:
            raise Exception("You already have a pick for this week")
        
        pick_data = {
            'player_id': player_id,
            'week': week,
            'team': team,
            'is_redemption': False
        }
        
        pick_id = await create_pick(pick_data)
        
        return {
            'id': pick_id,
            'player_id': player_id,
            'week': week,
            'team': team,
            'is_redemption': False
        }
