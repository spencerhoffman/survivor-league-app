import pytest
from httpx import AsyncClient

class TestWeeklyPicks:
    """Test weekly pick functionality."""
    
    @pytest.mark.asyncio
    async def test_make_valid_pick(self, client: AsyncClient, test_user_data, mock_profile_picture, nfl_teams):
        """Test making a valid weekly pick."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        player_response = await client.post("/players", json={"entry_name": "Test Entry"}, headers=headers)
        player_id = player_response.json()["id"]
        
        pick_data = {"team": nfl_teams[0]}
        response = await client.post(f"/players/{player_id}/picks", json=pick_data, headers=headers)
        assert response.status_code == 200
        
        pick = response.json()
        assert pick["team"] == nfl_teams[0]
        assert pick["week"] == 1
        assert pick["is_redemption"] == False
    
    @pytest.mark.asyncio
    async def test_make_pick_invalid_team(self, client: AsyncClient, test_user_data, mock_profile_picture):
        """Test making pick with invalid team fails."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        player_response = await client.post("/players", json={"entry_name": "Test Entry"}, headers=headers)
        player_id = player_response.json()["id"]
        
        pick_data = {"team": "Invalid Team"}
        response = await client.post(f"/players/{player_id}/picks", json=pick_data, headers=headers)
        assert response.status_code == 400
        assert "Invalid team" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_duplicate_pick_same_week(self, client: AsyncClient, test_user_data, mock_profile_picture, nfl_teams):
        """Test making duplicate pick in same week fails."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        player_response = await client.post("/players", json={"entry_name": "Test Entry"}, headers=headers)
        player_id = player_response.json()["id"]
        
        pick_data = {"team": nfl_teams[0]}
        response1 = await client.post(f"/players/{player_id}/picks", json=pick_data, headers=headers)
        assert response1.status_code == 200
        
        response2 = await client.post(f"/players/{player_id}/picks", json=pick_data, headers=headers)
        assert response2.status_code == 400
        assert "Team already used" in response2.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_pick_when_locked(self, client: AsyncClient, test_user_data, mock_profile_picture, admin_token, nfl_teams):
        """Test making pick when picks are locked fails."""
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
        
        await client.post("/admin/lock-picks", headers=admin_headers)
        
        pick_data = {"team": nfl_teams[0]}
        response = await client.post(f"/players/{player_id}/picks", json=pick_data, headers=headers)
        assert response.status_code == 400
        assert "locked" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_update_pick(self, client: AsyncClient, test_user_data, mock_profile_picture, nfl_teams):
        """Test updating an existing pick."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        player_response = await client.post("/players", json={"entry_name": "Test Entry"}, headers=headers)
        player_id = player_response.json()["id"]
        
        pick_data = {"team": nfl_teams[0]}
        pick_response = await client.post(f"/players/{player_id}/picks", json=pick_data, headers=headers)
        pick_id = pick_response.json()["id"]
        
        update_data = {"team": nfl_teams[1], "is_underdog": False}
        response = await client.put(f"/players/{player_id}/picks/{pick_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        updated_pick = response.json()
        assert updated_pick["team"] == nfl_teams[1]
    
    @pytest.mark.asyncio
    async def test_delete_pick(self, client: AsyncClient, test_user_data, mock_profile_picture, nfl_teams):
        """Test deleting a pick."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        player_response = await client.post("/players", json={"entry_name": "Test Entry"}, headers=headers)
        player_id = player_response.json()["id"]
        
        pick_data = {"team": nfl_teams[0]}
        pick_response = await client.post(f"/players/{player_id}/picks", json=pick_data, headers=headers)
        pick_id = pick_response.json()["id"]
        
        response = await client.delete(f"/players/{player_id}/picks/{pick_id}", headers=headers)
        assert response.status_code == 200
        
        picks_response = await client.get(f"/players/{player_id}/picks/current-week", headers=headers)
        picks = picks_response.json()
        assert len(picks) == 0
    
    @pytest.mark.asyncio
    async def test_get_current_week_picks(self, client: AsyncClient, test_user_data, mock_profile_picture, nfl_teams):
        """Test retrieving current week picks."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        player_response = await client.post("/players", json={"entry_name": "Test Entry"}, headers=headers)
        player_id = player_response.json()["id"]
        
        pick_data = {"team": nfl_teams[0]}
        await client.post(f"/players/{player_id}/picks", json=pick_data, headers=headers)
        
        response = await client.get(f"/players/{player_id}/picks/current-week", headers=headers)
        assert response.status_code == 200
        
        picks = response.json()
        assert len(picks) == 1
        assert picks[0]["team"] == nfl_teams[0]
    
    @pytest.mark.asyncio
    async def test_get_locked_picks(self, client: AsyncClient, test_user_data, mock_profile_picture, admin_token, nfl_teams):
        """Test retrieving locked picks."""
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
        
        await client.post("/admin/lock-picks", headers=admin_headers)
        
        response = await client.get("/picks/locked")
        assert response.status_code == 200
        
        locked_picks = response.json()
        assert len(locked_picks) == 1
        assert locked_picks[0]["team"] == nfl_teams[0]
        assert locked_picks[0]["week"] == 1
