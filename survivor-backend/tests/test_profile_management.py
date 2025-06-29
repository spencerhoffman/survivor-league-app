import pytest
from httpx import AsyncClient
import io

class TestProfileManagement:
    """Test user profile management functionality."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_profile(self, client: AsyncClient, test_user_data, mock_profile_picture):
        """Test getting current user profile."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.get("/me", headers=headers)
        assert response.status_code == 200
        
        profile = response.json()
        assert profile["username"] == test_user_data["username"]
        assert profile["email"] == test_user_data["email"]
        assert "profile_picture_url" in profile
        assert "password_hash" not in profile
    
    @pytest.mark.asyncio
    async def test_update_profile(self, client: AsyncClient, test_user_data, mock_profile_picture):
        """Test updating user profile."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        update_data = {
            "username": "newusername",
            "email": "newemail@test.com"
        }
        response = await client.put("/me", json=update_data, headers=headers)
        assert response.status_code == 200
        
        result = response.json()
        assert "Profile updated successfully" in result["message"]
        assert result["user"]["username"] == "newusername"
        assert result["user"]["email"] == "newemail@test.com"
    
    @pytest.mark.asyncio
    async def test_update_profile_duplicate_username(self, client: AsyncClient, test_user_data, mock_profile_picture):
        """Test updating profile with duplicate username fails."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data1 = {
            "username": "user1",
            "email": "user1@test.com",
            "password": "password123"
        }
        data2 = {
            "username": "user2",
            "email": "user2@test.com",
            "password": "password123"
        }
        
        await client.post("/auth/register", data=data1, files=files)
        register_response = await client.post("/auth/register", data=data2, files=files)
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        update_data = {"username": "user1"}
        response = await client.put("/me", json=update_data, headers=headers)
        assert response.status_code == 400
        assert "Username already exists" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_update_password(self, client: AsyncClient, test_user_data, mock_profile_picture):
        """Test updating user password."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        password_data = {
            "current_password": test_user_data["password"],
            "new_password": "newpassword123"
        }
        response = await client.put("/me/password", json=password_data, headers=headers)
        assert response.status_code == 200
        assert "Password updated successfully" in response.json()["message"]
        
        login_data = {
            "username": test_user_data["username"],
            "password": "newpassword123"
        }
        response = await client.post("/auth/login", json=login_data)
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_update_password_wrong_current(self, client: AsyncClient, test_user_data, mock_profile_picture):
        """Test updating password with wrong current password fails."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword123"
        }
        response = await client.put("/me/password", json=password_data, headers=headers)
        assert response.status_code == 400
        assert "Current password is incorrect" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_update_profile_picture(self, client: AsyncClient, test_user_data, mock_profile_picture):
        """Test updating profile picture."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        new_picture = io.BytesIO(b"new fake image data")
        files = {"profile_picture": ("new_test.png", new_picture, "image/png")}
        response = await client.put("/me/profile-picture", files=files, headers=headers)
        assert response.status_code == 200
        
        result = response.json()
        assert "Profile picture updated successfully" in result["message"]
        assert "profile_picture_url" in result
    
    @pytest.mark.asyncio
    async def test_update_profile_picture_invalid_type(self, client: AsyncClient, test_user_data, mock_profile_picture):
        """Test updating profile picture with invalid file type fails."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        invalid_file = io.BytesIO(b"not an image")
        files = {"profile_picture": ("test.txt", invalid_file, "text/plain")}
        response = await client.put("/me/profile-picture", files=files, headers=headers)
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]
