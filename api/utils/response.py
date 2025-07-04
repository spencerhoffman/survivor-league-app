from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional

def success_response(data: Any = None, message: str = "Success") -> JSONResponse:
    response_data = {"success": True, "message": message}
    if data is not None:
        response_data["data"] = data
    return JSONResponse(response_data)

def error_response(message: str, status_code: int = 400, details: Optional[Dict] = None) -> JSONResponse:
    response_data = {"success": False, "message": message}
    if details:
        response_data["details"] = details
    return JSONResponse(response_data, status_code=status_code)
