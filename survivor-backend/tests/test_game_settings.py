import pytest
from httpx import AsyncClient

class TestGameSettings:
    """Test game settings and configuration."""
    
    @pytest.mark.asyncio
    async def test_get_game_settings(self, client: AsyncClient):
        """Test retrieving game settings."""
        response = await client.get("/admin/settings")
        assert response.status_code == 200
        
        settings = response.json()
        assert "current_week" in settings
        assert "entry_fee" in settings
        assert "buyback_multiplier" in settings
        assert "picks_locked" in settings
        assert settings["current_week"] == 1
        assert settings["entry_fee"] == 35
        assert settings["buyback_multiplier"] == 3
        assert settings["picks_locked"] == False
    
    @pytest.mark.asyncio
    async def test_update_game_settings(self, client: AsyncClient, admin_token):
        """Test updating game settings."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        update_data = {
            "entry_fee": 50,
            "buyback_multiplier": 5
        }
        response = await client.put("/admin/settings", json=update_data, headers=admin_headers)
        assert response.status_code == 200
        
        settings = response.json()
        assert settings["entry_fee"] == 50
        assert settings["buyback_multiplier"] == 5
    
    @pytest.mark.asyncio
    async def test_advance_week(self, client: AsyncClient, admin_token):
        """Test advancing to next week."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await client.post("/admin/advance-week", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["current_week"] == 2
        
        settings_response = await client.get("/admin/settings")
        settings = settings_response.json()
        assert settings["current_week"] == 2
        assert settings["picks_locked"] == False
    
    @pytest.mark.asyncio
    async def test_lock_unlock_picks(self, client: AsyncClient, admin_token):
        """Test locking and unlocking picks."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await client.post("/admin/lock-picks", headers=admin_headers)
        assert response.status_code == 200
        assert "Picks locked" in response.json()["message"]
        
        settings_response = await client.get("/admin/settings")
        settings = settings_response.json()
        assert settings["picks_locked"] == True
        
        response = await client.post("/admin/unlock-picks", headers=admin_headers)
        assert response.status_code == 200
        assert "Picks unlocked" in response.json()["message"]
        
        settings_response = await client.get("/admin/settings")
        settings = settings_response.json()
        assert settings["picks_locked"] == False
    
    @pytest.mark.asyncio
    async def test_non_admin_cannot_update_settings(self, client: AsyncClient, test_user_data, mock_profile_picture):
        """Test that non-admin users cannot update settings."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        update_data = {"entry_fee": 100}
        response = await client.put("/admin/settings", json=update_data, headers=headers)
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]
