import pytest
from httpx import AsyncClient

class TestLeaderboard:
    """Test leaderboard functionality."""
    
    @pytest.mark.asyncio
    async def test_basic_leaderboard(self, client: AsyncClient, test_user_data, mock_profile_picture):
        """Test basic leaderboard functionality."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        await client.post("/players", json={"entry_name": "Test Entry"}, headers=headers)
        
        response = await client.get("/leaderboard")
        assert response.status_code == 200
        
        leaderboard = response.json()
        assert len(leaderboard) == 1
        assert leaderboard[0]["entry_name"] == "Test Entry"
        assert leaderboard[0]["status"] == "active"
        assert leaderboard[0]["weeks_survived"] == 0
        assert leaderboard[0]["financial_contribution"] == 35
    
    @pytest.mark.asyncio
    async def test_leaderboard_sorting(self, client: AsyncClient, mock_profile_picture, admin_token, nfl_teams):
        """Test leaderboard sorting logic."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        users_and_players = []
        for i in range(3):
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
                "player_id": player_id,
                "headers": headers,
                "username": f"user{i+1}"
            })
        
        for i, user_player in enumerate(users_and_players):
            pick_data = {"team": nfl_teams[i]}
            await client.post(f"/players/{user_player['player_id']}/picks", 
                            json=pick_data, headers=user_player["headers"])
        
        for i, team in enumerate(nfl_teams[:3]):
            outcome = "win" if i == 0 else "loss"  # First player wins, others lose
            result_data = {"team": team, "outcome": outcome}
            await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        
        await client.post("/admin/process-week-results", headers=admin_headers)
        
        response = await client.get("/leaderboard")
        leaderboard = response.json()
        
        active_players = [p for p in leaderboard if p["status"] == "active"]
        redemption_players = [p for p in leaderboard if p["status"] == "redemption"]
        
        assert len(active_players) == 1
        assert len(redemption_players) == 2
        assert active_players[0]["entry_name"] == "Entry 1"
    
    @pytest.mark.asyncio
    async def test_leaderboard_financial_tracking(self, client: AsyncClient, test_user_data, mock_profile_picture, admin_token, nfl_teams):
        """Test financial contribution tracking in leaderboard."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        player_response = await client.post("/players", json={"entry_name": "Test Entry"}, headers=headers)
        player_id = player_response.json()["id"]
        
        pick_data = {"team": nfl_teams[0]}
        await client.post(f"/players/{player_id}/picks", json=pick_data, headers=headers)
        
        result_data = {"team": nfl_teams[0], "outcome": "loss"}
        await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        await client.post("/admin/process-week-results", headers=admin_headers)
        
        await client.post("/admin/advance-week", headers=admin_headers)
        
        buyback_data = {"week": 2}
        await client.post(f"/players/{player_id}/buyback", json=buyback_data, headers=headers)
        
        response = await client.get("/leaderboard")
        leaderboard = response.json()
        player = leaderboard[0]
        
        expected_contribution = 35 + (2 * 3)  # entry fee + week 2 buyback
        assert player["financial_contribution"] == expected_contribution
        assert player["buybacks"] == 1
    
    @pytest.mark.asyncio
    async def test_leaderboard_multiple_entries(self, client: AsyncClient, mock_profile_picture, admin_token, nfl_teams):
        """Test leaderboard with multiple entries from same user."""
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
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        player_ids = []
        for i in range(3):
            player_response = await client.post("/players", json={"entry_name": f"Multi Entry {i+1}"}, headers=headers)
            player_ids.append(player_response.json()["id"])
        
        for i, player_id in enumerate(player_ids):
            pick_data = {"team": nfl_teams[i]}
            await client.post(f"/players/{player_id}/picks", json=pick_data, headers=headers)
        
        for i, team in enumerate(nfl_teams[:3]):
            outcome = "win" if i < 2 else "loss"  # First two win, last loses
            result_data = {"team": team, "outcome": outcome}
            await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        
        await client.post("/admin/process-week-results", headers=admin_headers)
        
        response = await client.get("/leaderboard")
        leaderboard = response.json()
        assert len(leaderboard) == 3
        
        active_players = [p for p in leaderboard if p["status"] == "active"]
        redemption_players = [p for p in leaderboard if p["status"] == "redemption"]
        
        assert len(active_players) == 2
        assert len(redemption_players) == 1
        
        for player in leaderboard:
            assert player["username"] == "multiuser"
    
    @pytest.mark.asyncio
    async def test_weeks_survived_calculation(self, client: AsyncClient, mock_profile_picture, admin_token, nfl_teams):
        """Test weeks survived calculation in leaderboard."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        user_data = {"username": "testuser", "email": "test@test.com", "password": "password123"}
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": user_data["username"],
            "email": user_data["email"],
            "password": user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        player_response = await client.post("/players", json={"entry_name": "Test Entry"}, headers=headers)
        player_id = player_response.json()["id"]
        
        for week in range(1, 4):
            pick_data = {"team": nfl_teams[week-1]}
            await client.post(f"/players/{player_id}/picks", json=pick_data, headers=headers)
            
            result_data = {"team": nfl_teams[week-1], "outcome": "win"}
            await client.post("/admin/record-result", json=result_data, headers=admin_headers)
            await client.post("/admin/process-week-results", headers=admin_headers)
            
            if week < 3:
                await client.post("/admin/advance-week", headers=admin_headers)
        
        response = await client.get("/leaderboard")
        leaderboard = response.json()
        player = leaderboard[0]
        
        assert player["weeks_survived"] == 3
        assert player["status"] == "active"
