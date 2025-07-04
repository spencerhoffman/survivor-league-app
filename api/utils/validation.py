from typing import List, Optional
from fastapi import HTTPException

def validate_week(week: int, current_week: int) -> None:
    if week < 1 or week > 18:
        raise HTTPException(status_code=400, detail="Week must be between 1 and 18")
    if week < current_week:
        raise HTTPException(status_code=400, detail="Cannot make picks for past weeks")

def validate_team(team: str, valid_teams: List[str]) -> None:
    if team not in valid_teams:
        raise HTTPException(status_code=400, detail=f"Invalid team: {team}")

def validate_player_ownership(player_user_id: str, current_user_id: str) -> None:
    if player_user_id != current_user_id:
        raise HTTPException(status_code=403, detail="You can only manage your own players")
