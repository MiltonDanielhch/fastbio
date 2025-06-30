from fastapi import Header, HTTPException
from app.config import settings

def validate_api_key(api_key: str = Header(..., alias="X-API-Key")):
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return api_key