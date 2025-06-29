import pytest
from httpx import AsyncClient

class TestBuybacks:
    """Test buyback functionality with corrected pricing logic."""
    
    @pytest.mark.asyncio
    async def test_buyback_eliminated_player(self, client: AsyncClient, test_user_data, mock_profile_picture, admin_token, nfl_teams):
        """Test buyback for eliminated player with correct week-based pricing."""
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
        
        response = await client.get("/players/me", headers=headers)
        player = response.json()[0]
        assert player["status"] == "redemption"
        
        await client.post("/admin/advance-week", headers=admin_headers)
        
        buyback_data = {"week": 2}
        response = await client.post(f"/players/{player_id}/buyback", json=buyback_data, headers=headers)
        assert response.status_code == 200
        
        expected_cost = 2 * 3  # week 2 * buyback_multiplier (3) = $6
        assert response.json()["cost"] == expected_cost
        
        response = await client.get("/players/me", headers=headers)
        player = response.json()[0]
        assert player["status"] == "active"
        assert player["buybacks"] == 1
        assert player["financial_contribution"] == 35 + expected_cost  # entry fee + buyback
    
    @pytest.mark.asyncio
    async def test_buyback_pricing_different_weeks(self, client: AsyncClient, test_user_data, mock_profile_picture, admin_token, nfl_teams):
        """Test buyback pricing varies correctly by week."""
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
        
        for _ in range(4):
            await client.post("/admin/advance-week", headers=admin_headers)
        
        buyback_data = {"week": 5}
        response = await client.post(f"/players/{player_id}/buyback", json=buyback_data, headers=headers)
        assert response.status_code == 200
        
        expected_cost = 5 * 3  # week 5 * buyback_multiplier (3) = $15
        assert response.json()["cost"] == expected_cost
    
    @pytest.mark.asyncio
    async def test_buyback_active_player_fails(self, client: AsyncClient, test_user_data, mock_profile_picture):
        """Test buyback fails for active player."""
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
        
        buyback_data = {"week": 1}
        response = await client.post(f"/players/{player_id}/buyback", json=buyback_data, headers=headers)
        assert response.status_code == 400
        assert "must be eliminated or in redemption" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_undo_contribution(self, client: AsyncClient, test_user_data, mock_profile_picture):
        """Test undo contribution with correct week-based pricing."""
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
        
        initial_contribution = 35  # entry fee
        
        undo_data = {"week": 3}
        response = await client.post(f"/players/{player_id}/undo", json=undo_data, headers=headers)
        assert response.status_code == 200
        
        expected_cost = 3 * 3  # week 3 * buyback_multiplier (3) = $9
        assert response.json()["cost"] == expected_cost
        
        response = await client.get("/players/me", headers=headers)
        player = response.json()[0]
        assert player["financial_contribution"] == initial_contribution + expected_cost
    
    @pytest.mark.asyncio
    async def test_multiple_buybacks(self, client: AsyncClient, test_user_data, mock_profile_picture, admin_token, nfl_teams):
        """Test multiple buybacks with cumulative costs."""
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
        response = await client.post(f"/players/{player_id}/buyback", json=buyback_data, headers=headers)
        assert response.status_code == 200
        first_buyback_cost = 2 * 3  # $6
        
        pick_data = {"team": nfl_teams[1]}
        await client.post(f"/players/{player_id}/picks", json=pick_data, headers=headers)
        
        result_data = {"team": nfl_teams[1], "outcome": "loss"}
        await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        await client.post("/admin/process-week-results", headers=admin_headers)
        
        await client.post("/admin/advance-week", headers=admin_headers)
        
        buyback_data = {"week": 3}
        response = await client.post(f"/players/{player_id}/buyback", json=buyback_data, headers=headers)
        assert response.status_code == 200
        second_buyback_cost = 3 * 3  # $9
        
        response = await client.get("/players/me", headers=headers)
        player = response.json()[0]
        assert player["buybacks"] == 2
        expected_total = 35 + first_buyback_cost + second_buyback_cost  # $35 + $6 + $9 = $50
        assert player["financial_contribution"] == expected_total
    
    @pytest.mark.skip(reason="Buyback pricing logic was fixed - this test documents the old incorrect behavior")
    @pytest.mark.asyncio
    async def test_buyback_pricing_correction_needed(self, client: AsyncClient):
        """Test documenting the buyback pricing correction that was needed."""
        pass
