import pytest
from httpx import AsyncClient

class TestPlayerManagement:
    """Test player creation and management functionality."""
    
    @pytest.mark.asyncio
    async def test_create_player(self, client: AsyncClient, test_user_data, mock_profile_picture):
        """Test creating a new player entry."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        player_data = {"entry_name": "My First Entry"}
        response = await client.post("/players", json=player_data, headers=headers)
        assert response.status_code == 200
        
        player = response.json()
        assert player["entry_name"] == "My First Entry"
        assert player["status"] == "active"
        assert player["eliminated_week"] is None
        assert player["redemption_visits"] == 0
        assert player["buybacks"] == 0
        assert player["financial_contribution"] == 35  # entry fee
    
    @pytest.mark.asyncio
    async def test_create_multiple_players(self, client: AsyncClient, test_user_data, mock_profile_picture):
        """Test creating multiple player entries for same user."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        player1_data = {"entry_name": "Entry 1"}
        player2_data = {"entry_name": "Entry 2"}
        
        response1 = await client.post("/players", json=player1_data, headers=headers)
        response2 = await client.post("/players", json=player2_data, headers=headers)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        player1 = response1.json()
        player2 = response2.json()
        
        assert player1["entry_name"] == "Entry 1"
        assert player2["entry_name"] == "Entry 2"
        assert player1["id"] != player2["id"]
    
    @pytest.mark.asyncio
    async def test_get_all_players(self, client: AsyncClient, test_user_data, mock_profile_picture):
        """Test retrieving all players."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        await client.post("/players", json={"entry_name": "Entry 1"}, headers=headers)
        await client.post("/players", json={"entry_name": "Entry 2"}, headers=headers)
        
        response = await client.get("/players")
        assert response.status_code == 200
        
        players = response.json()
        assert len(players) == 2
        assert any(p["entry_name"] == "Entry 1" for p in players)
        assert any(p["entry_name"] == "Entry 2" for p in players)
    
    @pytest.mark.asyncio
    async def test_player_status_transitions(self, client: AsyncClient, test_user_data, mock_profile_picture, admin_token, nfl_teams):
        """Test player status transitions through game flow."""
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
        
        response = await client.get("/players/me", headers=headers)
        player = response.json()[0]
        assert player["status"] == "active"
        
        pick_data = {"team": nfl_teams[0]}
        await client.post(f"/players/{player_id}/picks", json=pick_data, headers=headers)
        
        result_data = {"team": nfl_teams[0], "outcome": "loss"}
        await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        await client.post("/admin/process-week-results", headers=admin_headers)
        
        response = await client.get("/players/me", headers=headers)
        player = response.json()[0]
        assert player["status"] == "redemption"
        assert player["eliminated_week"] == 1
        assert player["redemption_visits"] == 1
    
    @pytest.mark.asyncio
    async def test_player_elimination_from_redemption(self, client: AsyncClient, test_user_data, mock_profile_picture, admin_token, nfl_teams):
        """Test player elimination from redemption round."""
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
            "teams": nfl_teams[1:3],  # Use different teams than the one that eliminated the player
            "week": 2
        }
        await client.post(f"/players/{player_id}/redemption-picks", json=redemption_data, headers=headers)
        
        for team in nfl_teams[1:3]:  # Record losses for the redemption teams
            result_data = {"team": team, "outcome": "loss"}
            await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        
        await client.post("/admin/process-week-results", headers=admin_headers)
        
        response = await client.get("/players/me", headers=headers)
        player = response.json()[0]
        assert player["status"] == "eliminated"
        assert player["eliminated_week"] == 2
