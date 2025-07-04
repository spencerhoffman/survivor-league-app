from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import asyncio
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from utils.database import get_player_by_id, create_pick, get_picks_by_player_and_week, get_game_settings, NFL_TEAMS, update_player
from utils.auth import verify_token
from utils.validation import validate_week, validate_team, validate_player_ownership

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
                teams = request_data.get('teams', [])
                week = request_data.get('week')
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON data")
                return
            
            if not teams or not week:
                self.send_error(400, "teams and week required")
                return
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._make_redemption_picks(player_id, user, teams, week))
            loop.close()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            self.send_error(400 if any(msg in str(e) for msg in ["Player not found", "Must select exactly 3", "already have redemption"]) else 500, str(e))
    
    async def _make_redemption_picks(self, player_id, user, teams, week):
        player = await get_player_by_id(player_id)
        if not player:
            raise Exception("Player not found")
        
        validate_player_ownership(player['user_id'], user['id'])
        
        if player['status'] != 'REDEMPTION':
            raise Exception("Player must be in redemption status to make redemption picks")
        
        settings = await get_game_settings()
        validate_week(week, settings.get('current_week', 1))
        
        if settings.get('picks_locked', False) and week == settings.get('current_week', 1):
            raise Exception("Picks are locked for the current week")
        
        if len(teams) != 3:
            raise Exception("Must select exactly 3 teams for redemption picks")
        
        for team in teams:
            validate_team(team, NFL_TEAMS)
            if team in player.get('eliminated_teams', []):
                raise Exception(f"Cannot pick team {team} - you've already been eliminated by them")
        
        if len(set(teams)) != len(teams):
            raise Exception("Cannot select duplicate teams")
        
        existing_picks = await get_picks_by_player_and_week(player_id, week)
        redemption_picks = [p for p in existing_picks if p.get('is_redemption', False)]
        if redemption_picks:
            raise Exception("You already have redemption picks for this week")
        
        created_picks = []
        for team in teams:
            pick_data = {
                'player_id': player_id,
                'week': week,
                'team': team,
                'is_redemption': True
            }
            pick_id = await create_pick(pick_data)
            created_picks.append({
                'id': pick_id,
                'player_id': player_id,
                'week': week,
                'team': team,
                'is_redemption': True
            })
        
        redemption_visits = player.get('redemption_visits', 0) + 1
        await update_player(player_id, {'redemption_visits': redemption_visits})
        
        return {
            "message": "Redemption picks created successfully",
            "picks": created_picks,
            "redemption_visits": redemption_visits
        }
