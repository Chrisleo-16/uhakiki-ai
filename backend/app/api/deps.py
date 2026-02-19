"""
FastAPI Dependencies
Contains common dependencies for API routes
"""

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Get the current authenticated user from JWT token
    Placeholder implementation - should be replaced with actual JWT validation
    """
    # TODO: Implement proper JWT validation
    # For now, return a mock user
    return {
        "id": "mock_user_id",
        "username": "mock_user",
        "email": "mock@example.com",
        "role": "user"
    }

async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get the current active user
    """
    if not current_user.get("active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
