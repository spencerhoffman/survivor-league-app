import pytest
from httpx import AsyncClient
import io

class TestAuthentication:
    """Test user authentication functionality."""
    
    @pytest.mark.asyncio
    async def test_register_user(self, client: AsyncClient, test_user_data, mock_profile_picture):
        """Test user registration with profile picture."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = await client.post("/auth/register", data=data, files=files)
        assert response.status_code == 200
        
        result = response.json()
        assert "token" in result
        assert result["user"]["username"] == test_user_data["username"]
        assert result["user"]["email"] == test_user_data["email"]
        assert "password" not in result["user"]
        assert "profile_picture_url" in result["user"]
    
    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient, test_user_data, mock_profile_picture):
        """Test registration with duplicate username fails."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        await client.post("/auth/register", data=data, files=files)
        
        response = await client.post("/auth/register", data=data, files=files)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_valid_credentials(self, client: AsyncClient, test_user_data, mock_profile_picture):
        """Test login with valid credentials."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        await client.post("/auth/register", data=data, files=files)
        
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        response = await client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "token" in result
        assert result["user"]["username"] == test_user_data["username"]
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient, test_user_data, mock_profile_picture):
        """Test login with invalid credentials fails."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        await client.post("/auth/register", data=data, files=files)
        
        login_data = {
            "username": test_user_data["username"],
            "password": "wrongpassword"
        }
        response = await client.post("/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent user fails."""
        login_data = {
            "username": "nonexistent",
            "password": "password"
        }
        response = await client.post("/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_reset_password(self, client: AsyncClient, test_user_data, mock_profile_picture):
        """Test password reset functionality."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        await client.post("/auth/register", data=data, files=files)
        
        reset_data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "new_password": "newpassword123"
        }
        response = await client.post("/auth/reset-password", json=reset_data)
        assert response.status_code == 200
        assert "Password reset successful" in response.json()["message"]
        
        login_data = {
            "username": test_user_data["username"],
            "password": "newpassword123"
        }
        response = await client.post("/auth/login", json=login_data)
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_reset_password_invalid_email(self, client: AsyncClient):
        """Test password reset with invalid email fails."""
        reset_data = {
            "username": "nonexistent",
            "email": "nonexistent@test.com",
            "new_password": "newpassword123"
        }
        response = await client.post("/auth/reset-password", json=reset_data)
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_without_token(self, client: AsyncClient):
        """Test accessing protected endpoint without token fails."""
        response = await client.get("/me")
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_with_token(self, client: AsyncClient, test_user_data, mock_profile_picture):
        """Test accessing protected endpoint with valid token."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        token = register_response.json()["token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/players/me", headers=headers)
        assert response.status_code == 200
