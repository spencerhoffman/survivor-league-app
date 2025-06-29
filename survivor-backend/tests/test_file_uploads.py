import pytest
from httpx import AsyncClient
import io

class TestFileUploads:
    """Test file upload functionality."""
    
    @pytest.mark.asyncio
    async def test_serve_uploaded_file(self, client: AsyncClient, test_user_data, mock_profile_picture):
        """Test serving uploaded profile pictures."""
        files = {"profile_picture": ("test.jpg", mock_profile_picture, "image/jpeg")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        register_response = await client.post("/auth/register", data=data, files=files)
        user = register_response.json()["user"]
        
        if user.get("profile_picture_url"):
            filename = user["profile_picture_url"].split("/")[-1]
            response = await client.get(f"/uploads/{filename}")
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("image/")
    
    @pytest.mark.asyncio
    async def test_serve_nonexistent_file(self, client: AsyncClient):
        """Test serving nonexistent file returns 404."""
        response = await client.get("/uploads/nonexistent.jpg")
        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_profile_picture_validation(self, client: AsyncClient, test_user_data):
        """Test profile picture file type validation."""
        invalid_file = io.BytesIO(b"not an image")
        files = {"profile_picture": ("test.txt", invalid_file, "text/plain")}
        data = {
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        
        response = await client.post("/auth/register", data=data, files=files)
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_supported_image_types(self, client: AsyncClient, test_user_data):
        """Test various supported image file types."""
        supported_types = [
            ("test.jpg", "image/jpeg"),
            ("test.png", "image/png"),
            ("test.gif", "image/gif"),
            ("test.webp", "image/webp")
        ]
        
        for filename, content_type in supported_types:
            mock_file = io.BytesIO(b"fake image data")
            files = {"profile_picture": (filename, mock_file, content_type)}
            data = {
                "username": f"user_{filename.split('.')[1]}",
                "email": f"user_{filename.split('.')[1]}@test.com",
                "password": "password123"
            }
            
            response = await client.post("/auth/register", data=data, files=files)
            assert response.status_code == 200
            assert "profile_picture_url" in response.json()["user"]
