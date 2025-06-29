import pytest
from httpx import AsyncClient

class TestAdminEndpoints:
    """Test new admin functionality endpoints."""
    
    @pytest.mark.asyncio
    async def test_add_underdog_teams(self, client: AsyncClient, admin_token, nfl_teams):
        """Test adding underdog teams."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        teams_data = {"teams": nfl_teams[:4], "week": 1}
        response = await client.post("/admin/underdog-teams", json=teams_data, headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["teams"] == nfl_teams[:4]
        assert response.json()["week"] == 1
    
    @pytest.mark.asyncio
    async def test_get_underdog_teams(self, client: AsyncClient, admin_token, nfl_teams):
        """Test retrieving underdog teams."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        teams_data = {"teams": nfl_teams[:4], "week": 1}
        await client.post("/admin/underdog-teams", json=teams_data, headers=admin_headers)
        
        response = await client.get("/admin/underdog-teams/1")
        assert response.status_code == 200
        
        teams = response.json()
        assert len(teams) == 4
        assert all(team in nfl_teams[:4] for team in teams)
    
    @pytest.mark.asyncio
    async def test_eliminate_player(self, client: AsyncClient, test_user_data, mock_profile_picture, admin_token):
        """Test manually eliminating a player."""
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
        
        response = await client.post(f"/admin/eliminate-player?player_id={player_id}", headers=admin_headers)
        assert response.status_code == 200
        assert "Player Test Entry moved to redemption round" in response.json()["message"]
        
        response = await client.get("/players/me", headers=headers)
        player = response.json()[0]
        assert player["status"] == "redemption"
    
    @pytest.mark.asyncio
    async def test_get_all_users(self, client: AsyncClient, test_user_data, mock_profile_picture, admin_token):
        """Test retrieving all users."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        await client.post("/auth/register", data=data, files=files)
        
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.get("/admin/users", headers=admin_headers)
        assert response.status_code == 200
        
        users = response.json()
        assert len(users) >= 2  # admin + test user
        assert any(user["username"] == "admin" for user in users)
        assert any(user["username"] == test_user_data["username"] for user in users)
    
    @pytest.mark.asyncio
    async def test_update_user_role(self, client: AsyncClient, test_user_data, mock_profile_picture, admin_token):
        """Test updating user role."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        user_id = register_response.json()["user"]["id"]
        
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        role_data = {"user_id": user_id, "role": "admin"}
        response = await client.put("/admin/users/role", json=role_data, headers=admin_headers)
        assert response.status_code == 200
        assert "User testuser role updated to" in response.json()["message"]
    
    @pytest.mark.asyncio
    async def test_update_teams(self, client: AsyncClient, admin_token, nfl_teams):
        """Test updating team list."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        new_teams = nfl_teams[:10]  # Use subset for testing
        teams_data = {"teams": new_teams}
        response = await client.put("/admin/teams", json=teams_data, headers=admin_headers)
        assert response.status_code == 200
        assert "Teams updated successfully" in response.json()["message"]
        
        response = await client.get("/admin/teams", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["teams"] == new_teams
    
    @pytest.mark.asyncio
    async def test_reset_league(self, client: AsyncClient, test_user_data, mock_profile_picture, admin_token, nfl_teams):
        """Test resetting the entire league."""
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
        assert "League reset successfully" in response.json()["message"]
        
        response = await client.get("/players")
        assert response.status_code == 200
        assert len(response.json()) == 0
    
    @pytest.mark.asyncio
    async def test_non_admin_access_denied(self, client: AsyncClient, test_user_data, mock_profile_picture):
        """Test that non-admin users cannot access admin endpoints."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        endpoints = [
            ("/admin/underdog-teams?team=ARI&week=1", "post", None),
            ("/admin/eliminate-player?player_id=123", "post", None),
            ("/admin/users", "get", None),
            ("/admin/users/role", "put", {"user_id": "123", "role": "admin"}),
            ("/admin/teams", "put", {"teams": ["ARI"]}),
            ("/admin/reset-league", "post", None)
        ]
        
        for endpoint, method, data in endpoints:
            if method == "post":
                if data:
                    response = await client.post(endpoint, json=data, headers=headers)
                else:
                    response = await client.post(endpoint, headers=headers)
            elif method == "put":
                response = await client.put(endpoint, json=data, headers=headers)
            else:
                response = await client.get(endpoint, headers=headers)
            
            assert response.status_code == 403
            assert "Admin access required" in response.json()["detail"]
