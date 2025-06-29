import pytest
from httpx import AsyncClient

class TestRedemptionRounds:
    """Test redemption round functionality."""
    
    @pytest.mark.asyncio
    async def test_make_redemption_picks(self, client: AsyncClient, test_user_data, mock_profile_picture, admin_token, nfl_teams):
        """Test making redemption picks with underdog teams."""
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
        
        underdog_data = {"teams": nfl_teams[:4]}
        await client.post("/admin/underdog-teams", json=underdog_data, headers=admin_headers)
        
        redemption_data = {
            "teams": nfl_teams[1:3],  # Use different teams than the eliminated team
            "week": 2
        }
        response = await client.post(f"/players/{player_id}/redemption-picks", json=redemption_data, headers=headers)
        assert response.status_code == 200
        
        picks = response.json()
        assert len(picks) == 2
        assert all(pick["is_redemption"] for pick in picks)
        assert all(pick["is_underdog"] for pick in picks)
    
    @pytest.mark.asyncio
    async def test_redemption_picks_wrong_count(self, client: AsyncClient, test_user_data, mock_profile_picture, admin_token, nfl_teams):
        """Test redemption picks with wrong number of teams fails."""
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
        
        underdog_data = {"teams": nfl_teams[:4]}
        await client.post("/admin/underdog-teams", json=underdog_data, headers=admin_headers)
        
        redemption_data = {
            "teams": [nfl_teams[0]],  # Only 1 team instead of 2
            "week": 2
        }
        response = await client.post(f"/players/{player_id}/redemption-picks", json=redemption_data, headers=headers)
        assert response.status_code == 400
        assert "exactly 2 teams" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_redemption_picks_non_underdog_teams(self, client: AsyncClient, test_user_data, mock_profile_picture, admin_token, nfl_teams):
        """Test redemption picks with non-underdog teams fails."""
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
        
        underdog_data = {"teams": nfl_teams[:2]}
        await client.post("/admin/underdog-teams", json=underdog_data, headers=admin_headers)
        
        redemption_data = {
            "teams": nfl_teams[2:4],  # Non-underdog teams
            "week": 2
        }
        response = await client.post(f"/players/{player_id}/redemption-picks", json=redemption_data, headers=headers)
        assert response.status_code == 400
        assert "Invalid underdog team" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_redemption_picks_active_player(self, client: AsyncClient, test_user_data, mock_profile_picture, admin_token, nfl_teams):
        """Test redemption picks fail for active player."""
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
        
        underdog_data = {"teams": nfl_teams[:4]}
        await client.post("/admin/underdog-teams", json=underdog_data, headers=admin_headers)
        
        redemption_data = {
            "teams": nfl_teams[:2],
            "week": 1
        }
        response = await client.post(f"/players/{player_id}/redemption-picks", json=redemption_data, headers=headers)
        assert response.status_code == 400
        assert "redemption" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_redemption_success_returns_to_active(self, client: AsyncClient, test_user_data, mock_profile_picture, admin_token, nfl_teams):
        """Test successful redemption returns player to active status."""
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
        
        underdog_data = {"teams": nfl_teams[:4]}
        await client.post("/admin/underdog-teams", json=underdog_data, headers=admin_headers)
        
        redemption_data = {
            "teams": nfl_teams[1:3],  # Use different teams than the eliminated team
            "week": 2
        }
        await client.post(f"/players/{player_id}/redemption-picks", json=redemption_data, headers=headers)
        
        for team in nfl_teams[1:3]:  # Use same teams as redemption picks
            result_data = {"team": team, "outcome": "win"}
            await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        
        await client.post("/admin/process-week-results", headers=admin_headers)
        
        response = await client.get("/players/me", headers=headers)
        player = response.json()[0]
        assert player["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_redemption_failure_eliminates_player(self, client: AsyncClient, test_user_data, mock_profile_picture, admin_token, nfl_teams):
        """Test failed redemption eliminates player."""
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
        
        underdog_data = {"teams": nfl_teams[:4]}
        await client.post("/admin/underdog-teams", json=underdog_data, headers=admin_headers)
        
        redemption_data = {
            "teams": nfl_teams[1:3],  # Use different teams than the eliminated team
            "week": 2
        }
        await client.post(f"/players/{player_id}/redemption-picks", json=redemption_data, headers=headers)
        
        for team in nfl_teams[1:3]:  # Use same teams as redemption picks
            result_data = {"team": team, "outcome": "loss"}
            await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        
        await client.post("/admin/process-week-results", headers=admin_headers)
        
        response = await client.get("/players/me", headers=headers)
        player = response.json()[0]
        assert player["status"] == "eliminated"
