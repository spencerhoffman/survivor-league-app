import pytest
from httpx import AsyncClient
import asyncio

class TestComprehensiveScenarios:
    """Test comprehensive game scenarios across 10 teams over 10 weeks."""
    
    @pytest.mark.asyncio
    async def test_ten_teams_ten_weeks_scenario(self, client: AsyncClient, mock_profile_picture, admin_token, nfl_teams):
        """Test complete 10 teams over 10 weeks survivor league scenario."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        users_and_players = []
        for i in range(10):
            user_data = {
                "username": f"user{i+1}",
                "email": f"user{i+1}@test.com",
                "password": "password123"
            }
            files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
            data = {
                "username": user_data["username"],
                "email": user_data["email"],
                "password": user_data["password"]
            }
            register_response = await client.post("/auth/register", data=data, files=files)
            token = register_response.json()["token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            player_response = await client.post("/players", json={"entry_name": f"Entry {i+1}"}, headers=headers)
            player_id = player_response.json()["id"]
            
            users_and_players.append({
                "user_id": register_response.json()["user"]["id"],
                "player_id": player_id,
                "token": token,
                "headers": headers,
                "username": f"user{i+1}",
                "eliminated_week": None
            })
        
        for week in range(1, 11):
            print(f"\n--- Week {week} ---")
            
            underdog_teams = nfl_teams[:4]  # First 4 teams as underdogs
            underdog_data = {"teams": underdog_teams, "week": week}
            await client.post("/admin/underdog-teams", json=underdog_data, headers=admin_headers)
            
            week_picks = {}
            for user_player in users_and_players:
                if user_player["eliminated_week"] is None:  # Still active
                    response = await client.get("/players/me", headers=user_player["headers"])
                    players = response.json()
                    player = next(p for p in players if p["id"] == user_player["player_id"])
                    
                    if player["status"] == "active":
                        team_index = (week - 1 + int(user_player["username"][-1])) % len(nfl_teams)
                        selected_team = nfl_teams[team_index]
                        
                        pick_data = {"team": selected_team}
                        response = await client.post(f"/players/{user_player['player_id']}/picks", 
                                                   json=pick_data, headers=user_player["headers"])
                        if response.status_code == 200:
                            week_picks[user_player["player_id"]] = selected_team
                    
                    elif player["status"] == "redemption":
                        redemption_teams = underdog_teams[:2]
                        redemption_data = {
                            "teams": redemption_teams,
                            "week": week
                        }
                        response = await client.post(f"/players/{user_player['player_id']}/redemption-picks",
                                                   json=redemption_data, headers=user_player["headers"])
                        if response.status_code == 200:
                            week_picks[user_player["player_id"]] = redemption_teams
            
            await client.post("/admin/lock-picks", headers=admin_headers)
            
            teams_with_results = set()
            for player_id, picked_teams in week_picks.items():
                if isinstance(picked_teams, list):  # Redemption picks
                    for team in picked_teams:
                        if team not in teams_with_results:
                            outcome = "win" if (week + hash(team)) % 2 == 0 else "loss"
                            result_data = {"team": team, "outcome": outcome}
                            await client.post("/admin/record-result", json=result_data, headers=admin_headers)
                            teams_with_results.add(team)
                else:  # Regular pick
                    team = picked_teams
                    if team not in teams_with_results:
                        outcome = "win" if (week + hash(team)) % 2 == 0 else "loss"
                        result_data = {"team": team, "outcome": outcome}
                        await client.post("/admin/record-result", json=result_data, headers=admin_headers)
                        teams_with_results.add(team)
            
            response = await client.post("/admin/process-week-results", headers=admin_headers)
            assert response.status_code == 200
            
            for user_player in users_and_players:
                if user_player["eliminated_week"] is None:
                    response = await client.get("/players/me", headers=user_player["headers"])
                    players = response.json()
                    player = next(p for p in players if p["id"] == user_player["player_id"])
                    
                    if player["status"] == "eliminated":
                        user_player["eliminated_week"] = week
            
            if week < 10:
                await client.post("/admin/advance-week", headers=admin_headers)
                await client.post("/admin/unlock-picks", headers=admin_headers)
        
        response = await client.get("/leaderboard")
        assert response.status_code == 200
        leaderboard = response.json()
        assert len(leaderboard) == 10
        
        active_players = [p for p in leaderboard if p["status"] == "active"]
        eliminated_players = [p for p in leaderboard if p["status"] == "eliminated"]
        
        print(f"\nFinal Results:")
        print(f"Active players: {len(active_players)}")
        print(f"Eliminated players: {len(eliminated_players)}")
        
        assert len(eliminated_players) > 0, "Expected some players to be eliminated"
        
        for player in leaderboard:
            assert player["weeks_survived"] >= 0
            assert player["weeks_survived"] <= 10
    
    @pytest.mark.asyncio
    async def test_multiple_entries_per_user(self, client: AsyncClient, mock_profile_picture, admin_token, nfl_teams):
        """Test users with multiple entries across several weeks."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        user_data = {
            "username": "multiuser",
            "email": "multi@test.com",
            "password": "password123"
        }
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": user_data["username"],
            "email": user_data["email"],
            "password": user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        player_ids = []
        for i in range(3):
            player_response = await client.post("/players", json={"entry_name": f"Multi Entry {i+1}"}, headers=headers)
            player_ids.append(player_response.json()["id"])
        
        for week in range(1, 6):
            for i, player_id in enumerate(player_ids):
                response = await client.get("/players/me", headers=headers)
                players = response.json()
                player = next(p for p in players if p["id"] == player_id)
                
                if player["status"] == "active":
                    team_index = (week - 1 + i) % len(nfl_teams)
                    selected_team = nfl_teams[team_index]
                    
                    pick_data = {"team": selected_team}
                    await client.post(f"/players/{player_id}/picks", json=pick_data, headers=headers)
            
            for i in range(3):
                team_index = (week - 1 + i) % len(nfl_teams)
                team = nfl_teams[team_index]
                outcome = "win" if i != 1 else "loss"  # Middle entry loses
                
                result_data = {"team": team, "outcome": outcome}
                await client.post("/admin/record-result", json=result_data, headers=admin_headers)
            
            await client.post("/admin/process-week-results", headers=admin_headers)
            
            if week < 5:
                await client.post("/admin/advance-week", headers=admin_headers)
        
        response = await client.get("/players/me", headers=headers)
        players = response.json()
        assert len(players) == 3
        
        statuses = [p["status"] for p in players]
        assert "eliminated" in statuses or "redemption" in statuses
    
    @pytest.mark.asyncio
    async def test_edge_case_scenarios(self, client: AsyncClient, mock_profile_picture, admin_token, nfl_teams):
        """Test various edge cases and boundary conditions."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        user_data = {"username": "edgeuser", "email": "edge@test.com", "password": "password123"}
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": user_data["username"],
            "email": user_data["email"],
            "password": user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        player_response = await client.post("/players", json={"entry_name": "Edge Entry"}, headers=headers)
        player_id = player_response.json()["id"]
        
        pick_data = {"team": nfl_teams[0]}
        await client.post(f"/players/{player_id}/picks", json=pick_data, headers=headers)
        
        result_data = {"team": nfl_teams[0], "outcome": "loss"}
        await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        await client.post("/admin/process-week-results", headers=admin_headers)
        
        response = await client.get("/players/me", headers=headers)
        players = response.json()
        player = players[0]
        assert player["status"] == "redemption"
        
        await client.post("/admin/advance-week", headers=admin_headers)
        
        user_data2 = {"username": "user2", "email": "user2@test.com", "password": "password123"}
        files2 = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data2 = {
            "username": user_data2["username"],
            "email": user_data2["email"],
            "password": user_data2["password"]
        }
        register_response2 = await client.post("/auth/register", data=data2, files=files2)
        token2 = register_response2.json()["token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        player_response2 = await client.post("/players", json={"entry_name": "Entry 2"}, headers=headers2)
        player_id2 = player_response2.json()["id"]
        
        await client.post(f"/players/{player_id2}/picks", json={"team": nfl_teams[1]}, headers=headers2)
        
        for team in nfl_teams[:5]:
            result_data = {"team": team, "outcome": "loss"}
            await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        
        await client.post("/admin/process-week-results", headers=admin_headers)
        
        await client.post("/admin/advance-week", headers=admin_headers)
        
        result_data = {"team": nfl_teams[2], "outcome": "bye"}
        await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        
        response = await client.get("/admin/game-results/3")
        results = response.json()
        bye_results = [r for r in results if r["outcome"] == "bye"]
        assert len(bye_results) >= 1
    
    @pytest.mark.asyncio
    async def test_buyback_scenarios_with_corrected_pricing(self, client: AsyncClient, mock_profile_picture, admin_token, nfl_teams):
        """Test buyback scenarios with the corrected week-based pricing."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        user_data = {"username": "buybackuser", "email": "buyback@test.com", "password": "password123"}
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": user_data["username"],
            "email": user_data["email"],
            "password": user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        player_response = await client.post("/players", json={"entry_name": "Buyback Entry"}, headers=headers)
        player_id = player_response.json()["id"]
        
        pick_data = {"team": nfl_teams[0]}
        await client.post(f"/players/{player_id}/picks", json=pick_data, headers=headers)
        
        result_data = {"team": nfl_teams[0], "outcome": "loss"}
        await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        await client.post("/admin/process-week-results", headers=admin_headers)
        
        for week in range(2, 6):
            await client.post("/admin/advance-week", headers=admin_headers)
            
            buyback_data = {"week": week}
            response = await client.post(f"/players/{player_id}/buyback", json=buyback_data, headers=headers)
            assert response.status_code == 200
            
            expected_cost = week * 3  # week * buyback_multiplier
            assert response.json()["cost"] == expected_cost
            
            response = await client.get("/players/me", headers=headers)
            player = response.json()[0]
            assert player["status"] == "active"
            
            pick_data = {"team": nfl_teams[week % len(nfl_teams)]}
            await client.post(f"/players/{player_id}/picks", json=pick_data, headers=headers)
            
            result_data = {"team": nfl_teams[week % len(nfl_teams)], "outcome": "loss"}
            await client.post("/admin/record-result", json=result_data, headers=admin_headers)
            await client.post("/admin/process-week-results", headers=admin_headers)
        
        response = await client.get("/players/me", headers=headers)
        player = response.json()[0]
        
        expected_total_cost = 35 + sum(week * 3 for week in range(2, 6))  # entry + buybacks
        assert player["financial_contribution"] == expected_total_cost
        assert player["buybacks"] == 4
