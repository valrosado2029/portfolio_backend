from fastapi import Header, HTTPException, status
from app.config import settings


async def require_api_key(x_api_key: str = Header(None)):
    if x_api_key != settings.backend_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return True
