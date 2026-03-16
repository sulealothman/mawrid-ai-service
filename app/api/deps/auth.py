from fastapi import Header, HTTPException
from app.core.config import settings


def verify_internal_api_key(x_internal_key: str = Header(...)):
    if x_internal_key != settings.INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")