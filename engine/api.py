from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
app = FastAPI(default_response_class=ORJSONResponse)
@app.get("/health")
async def health():
    return {"status":"ok"}
