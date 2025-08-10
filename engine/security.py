import os
from fastapi import Request, HTTPException

API_KEY = os.environ.get("AURORA_API_KEY", "").strip()

async def check(request: Request):
    # Allow local reverse proxy or local curl without a key
    if request.client and request.client.host in ("127.0.0.1","::1"):
        return
    if not API_KEY:
        raise HTTPException(status_code=503, detail="API not configured")
    if request.headers.get("x-api-key") != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
