from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Header, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from datetime import datetime
import asyncio, json, os
from .settings import API_KEY, LOGS, STATE
from .trader import TRADER, WS_CLIENTS

app = FastAPI(title="Aurora API", version="0.2")
app.mount("/web", StaticFiles(directory=Path(__file__).resolve().parents[1]/"web", html=True), name="web")

def require_key(x_api_key: str | None = Header(default=None)):
    if x_api_key == API_KEY or os.getenv("AURORA_DEV_BYPASS","0") == "1":
        return True
    raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/health")
def health():
    return {"ok": True, "ts": datetime.utcnow().isoformat()+"Z"}

@app.get("/state", dependencies=[Depends(require_key)])
def state():
    if STATE.exists():
        return JSONResponse(json.loads(STATE.read_text()))
    return {"error":"no state"}

@app.get("/trades", dependencies=[Depends(require_key)])
def trades():
    p = LOGS/'trade_log.csv'
    return FileResponse(p) if p.exists() else JSONResponse({"rows":[]})

@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    WS_CLIENTS.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        WS_CLIENTS.discard(websocket)

@app.post("/tick/start", dependencies=[Depends(require_key)])
async def start():
    if not getattr(app.state, "task", None) or app.state.task.done():
        app.state.task = asyncio.create_task(TRADER.run())
        return {"started": True}
    return {"started": False, "note":"already running"}

@app.post("/tick/stop", dependencies=[Depends(require_key)])
async def stop():
    t = getattr(app.state, "task", None)
    if t and not t.done():
        t.cancel()
        try: await t
        except: pass
        return {"stopped": True}
    return {"stopped": False}
