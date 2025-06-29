import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient
from app.main import app

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def client():
    """Create test client for API testing."""
    from fastapi.testclient import TestClient
    from httpx import AsyncClient
    import httpx
    
    async with AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

@pytest.fixture
def admin_token():
    """Create admin token for testing admin endpoints."""
    from app.main import create_token, users_db
    admin_user_id = None
    for user_id, user in users_db.items():
        if hasattr(user, 'role') and user.role.value == 'admin':
            admin_user_id = user_id
            break
    if admin_user_id:
        return create_token(admin_user_id)
    else:
        return create_token("admin")

@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com", 
        "password": "testpass123"
    }

@pytest.fixture
def mock_profile_picture():
    """Create a mock profile picture file for testing."""
    import io
    return io.BytesIO(b"fake image data")

@pytest.fixture
def nfl_teams():
    """Standard NFL teams for testing (using 3-letter abbreviations)."""
    return [
        "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN",
        "DET", "GB", "HOU", "IND", "JAX", "KC", "LV", "LAC", "LAR", "MIA",
        "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SF", "SEA", "TB",
        "TEN", "WSH"
    ]

@pytest.fixture(autouse=True)
def reset_database():
    """Reset in-memory database before each test."""
    from app.main import users_db, players_db, picks_db, game_results_db, underdog_teams_db, game_settings
    
    users_db.clear()
    players_db.clear()
    picks_db.clear()
    game_results_db.clear()
    underdog_teams_db.clear()
    
    game_settings.current_week = 1
    game_settings.entry_fee = 35
    game_settings.buyback_multiplier = 3
    game_settings.picks_locked = False
    
    from app.main import hash_password, User, UserRole
    from datetime import datetime
    import uuid
    admin_id = str(uuid.uuid4())
    users_db[admin_id] = User(
        id=admin_id,
        username="admin",
        email="admin@test.com",
        password_hash=hash_password("admin123"),
        role=UserRole.ADMIN,
        created_at=datetime.utcnow()
    )
    
    yield
