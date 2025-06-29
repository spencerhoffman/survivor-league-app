import pytest
from httpx import AsyncClient

class TestAdminControls:
    """Test admin control functionality."""
    
    @pytest.mark.asyncio
    async def test_advance_week(self, client: AsyncClient, admin_token):
        """Test advancing to next week."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await client.get("/admin/settings")
        assert response.json()["current_week"] == 1
        
        response = await client.post("/admin/advance-week", headers=admin_headers)
        assert response.status_code == 200
        
        response = await client.get("/admin/settings")
        assert response.json()["current_week"] == 2
    
    @pytest.mark.asyncio
    async def test_lock_picks(self, client: AsyncClient, admin_token):
        """Test locking picks."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await client.get("/admin/settings")
        assert response.json()["picks_locked"] == False
        
        response = await client.post("/admin/lock-picks", headers=admin_headers)
        assert response.status_code == 200
        
        response = await client.get("/admin/settings")
        assert response.json()["picks_locked"] == True
    
    @pytest.mark.asyncio
    async def test_unlock_picks(self, client: AsyncClient, admin_token):
        """Test unlocking picks."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        await client.post("/admin/lock-picks", headers=admin_headers)
        
        response = await client.post("/admin/unlock-picks", headers=admin_headers)
        assert response.status_code == 200
        
        response = await client.get("/admin/settings")
        assert response.json()["picks_locked"] == False
    
    @pytest.mark.asyncio
    async def test_update_game_settings(self, client: AsyncClient, admin_token):
        """Test updating game settings."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        settings_data = {
            "entry_fee": 50,
            "buyback_multiplier": 4
        }
        response = await client.put("/admin/settings", json=settings_data, headers=admin_headers)
        assert response.status_code == 200
        
        response = await client.get("/admin/settings")
        settings = response.json()
        assert settings["entry_fee"] == 50
        assert settings["buyback_multiplier"] == 4
    
    @pytest.mark.asyncio
    async def test_record_game_result(self, client: AsyncClient, admin_token, nfl_teams):
        """Test recording game results."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        result_data = {"team": nfl_teams[0], "outcome": "win"}
        response = await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        assert response.status_code == 200
        
        result = response.json()
        assert result["team"] == nfl_teams[0]
        assert result["outcome"] == "win"
        assert result["week"] == 1
    
    @pytest.mark.asyncio
    async def test_record_invalid_outcome(self, client: AsyncClient, admin_token, nfl_teams):
        """Test recording invalid game outcome fails."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        result_data = {"team": nfl_teams[0], "outcome": "invalid"}
        response = await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        assert response.status_code == 400
        assert "Invalid outcome" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_process_week_results(self, client: AsyncClient, test_user_data, mock_profile_picture, admin_token, nfl_teams):
        """Test processing week results."""
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
        
        response = await client.post("/admin/process-week-results", headers=admin_headers)
        assert response.status_code == 200
        
        result = response.json()
        assert result["total_eliminated"] >= 1
        assert len(result["eliminated_players"]) >= 1
    
    @pytest.mark.asyncio
    async def test_manage_underdog_teams(self, client: AsyncClient, admin_token, nfl_teams):
        """Test managing underdog teams."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        underdog_data = {"teams": nfl_teams[:3]}
        response = await client.post("/admin/underdog-teams", json=underdog_data, headers=admin_headers)
        assert response.status_code == 200
        
        response = await client.get("/admin/underdog-teams/1")
        assert response.status_code == 200
        underdogs = response.json()
        assert len(underdogs) == 3
        assert all(team in nfl_teams[:3] for team in underdogs)
    
    @pytest.mark.asyncio
    async def test_reset_league(self, client: AsyncClient, test_user_data, mock_profile_picture, admin_token):
        """Test resetting entire league."""
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
        
        await client.post("/players", json={"entry_name": "Test Entry"}, headers=headers)
        
        response = await client.post("/admin/reset-league", headers=admin_headers)
        assert response.status_code == 200
        
        response = await client.get("/players/me", headers=headers)
        assert response.status_code == 404  # User not found
        
        response = await client.get("/admin/settings")
        settings = response.json()
        assert settings["current_week"] == 1
        assert settings["picks_locked"] == False
    
    @pytest.mark.asyncio
    async def test_non_admin_access_denied(self, client: AsyncClient, test_user_data, mock_profile_picture):
        """Test non-admin users cannot access admin endpoints."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        admin_endpoints = [
            ("/admin/advance-week", "POST"),
            ("/admin/lock-picks", "POST"),
            ("/admin/settings", "PUT"),
            ("/admin/record-result", "POST"),
            ("/admin/process-week-results", "POST"),
            ("/admin/reset-league", "POST")
        ]
        
        for endpoint, method in admin_endpoints:
            if method == "POST":
                response = await client.post(endpoint, json={}, headers=headers)
            else:
                response = await client.put(endpoint, json={}, headers=headers)
            assert response.status_code == 403
