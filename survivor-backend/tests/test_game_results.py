import pytest
from httpx import AsyncClient

class TestGameResults:
    """Test game result recording and management."""
    
    @pytest.mark.asyncio
    async def test_record_win_result(self, client: AsyncClient, admin_token, nfl_teams):
        """Test recording a win result."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        result_data = {"team": nfl_teams[0], "outcome": "win"}
        response = await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        assert response.status_code == 200
        
        result = response.json()
        assert result["team"] == nfl_teams[0]
        assert result["outcome"] == "win"
        assert result["week"] == 1
    
    @pytest.mark.asyncio
    async def test_record_loss_result(self, client: AsyncClient, admin_token, nfl_teams):
        """Test recording a loss result."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        result_data = {"team": nfl_teams[0], "outcome": "loss"}
        response = await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        assert response.status_code == 200
        
        result = response.json()
        assert result["team"] == nfl_teams[0]
        assert result["outcome"] == "loss"
        assert result["week"] == 1
    
    @pytest.mark.asyncio
    async def test_record_bye_result(self, client: AsyncClient, admin_token, nfl_teams):
        """Test recording a bye week result."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        result_data = {"team": nfl_teams[0], "outcome": "bye"}
        response = await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        assert response.status_code == 200
        
        result = response.json()
        assert result["team"] == nfl_teams[0]
        assert result["outcome"] == "bye"
        assert result["week"] == 1
    
    @pytest.mark.asyncio
    async def test_record_invalid_team(self, client: AsyncClient, admin_token):
        """Test recording result for invalid team fails."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        result_data = {"team": "Invalid Team", "outcome": "win"}
        response = await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        assert response.status_code == 400
        assert "Invalid team" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_record_invalid_outcome(self, client: AsyncClient, admin_token, nfl_teams):
        """Test recording invalid outcome fails."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        result_data = {"team": nfl_teams[0], "outcome": "invalid"}
        response = await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        assert response.status_code == 400
        assert "Invalid outcome" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_overwrite_existing_result(self, client: AsyncClient, admin_token, nfl_teams):
        """Test overwriting existing game result."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        result_data = {"team": nfl_teams[0], "outcome": "win"}
        await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        
        result_data = {"team": nfl_teams[0], "outcome": "loss"}
        response = await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        assert response.status_code == 200
        
        result = response.json()
        assert result["outcome"] == "loss"
    
    @pytest.mark.asyncio
    async def test_get_week_results(self, client: AsyncClient, admin_token, nfl_teams):
        """Test retrieving results for specific week."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        for i, team in enumerate(nfl_teams[:3]):
            outcome = "win" if i % 2 == 0 else "loss"
            result_data = {"team": team, "outcome": outcome}
            await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        
        response = await client.get("/admin/game-results/1")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) == 3
        assert all(r["week"] == 1 for r in results)
    
    @pytest.mark.asyncio
    async def test_get_all_results(self, client: AsyncClient, admin_token, nfl_teams):
        """Test retrieving all game results."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        result_data = {"team": nfl_teams[0], "outcome": "win"}
        await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        
        await client.post("/admin/advance-week", headers=admin_headers)
        
        result_data = {"team": nfl_teams[1], "outcome": "loss"}
        await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        
        response = await client.get("/admin/game-results")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) == 2
        weeks = [r["week"] for r in results]
        assert 1 in weeks and 2 in weeks
    
    @pytest.mark.asyncio
    async def test_delete_game_result(self, client: AsyncClient, admin_token, nfl_teams):
        """Test deleting a game result."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        result_data = {"team": nfl_teams[0], "outcome": "win"}
        result_response = await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        result_id = result_response.json()["id"]
        
        response = await client.delete(f"/admin/game-results/{result_id}", headers=admin_headers)
        assert response.status_code == 200
        
        response = await client.get("/admin/game-results/1")
        results = response.json()
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_game_results_affect_player_elimination(self, client: AsyncClient, test_user_data, mock_profile_picture, admin_token, nfl_teams):
        """Test that game results properly affect player elimination."""
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
        assert player["eliminated_week"] == 1
    
    @pytest.mark.asyncio
    async def test_bye_week_handling(self, client: AsyncClient, test_user_data, mock_profile_picture, admin_token, nfl_teams):
        """Test bye week handling for players."""
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
        
        result_data = {"team": nfl_teams[0], "outcome": "bye"}
        await client.post("/admin/record-result", json=result_data, headers=admin_headers)
        
        await client.post("/admin/process-week-results", headers=admin_headers)
        
        response = await client.get("/players/me", headers=headers)
        player = response.json()[0]
        assert player["status"] == "active"  # Bye weeks don't eliminate players
