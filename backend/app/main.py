from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Set, List, Dict
import json
import asyncio
import os
from app.schema import Health, TopTalker, AlertMsg, AuditItem, EventMsg, MitigationRequest
from app.watcher import EVEWatcher
from app.detector import DetectionEngine
from app.mitigator import Mitigator
from app.auth import LoginRequest, TokenResponse, authenticate, create_token, verify_token

app = FastAPI(title="Suricata Security System")

# WebSocket broadcaster
ws_clients: Set[WebSocket] = set()
watcher: EVEWatcher = None
detector: DetectionEngine = None
mitigator: Mitigator = None

async def broadcast(message: dict):
    for client in ws_clients.copy():
        try:
            await client.send_json(message)
        except:
            ws_clients.discard(client)

@app.get("/")
async def root():
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "frontend", "index.html")
    return FileResponse(frontend_path)

@app.get("/api/health", response_model=Health)
async def health():
    return {"status": "ok"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ws_clients.add(websocket)
    await websocket.send_json({"type": "connected", "message": "WebSocket connected"})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_clients.discard(websocket)

@app.get("/api/top-talkers", response_model=List[TopTalker])
async def get_top_talkers(window: str = "5m", metric: str = "pps", limit: int = 20):
    if detector:
        return detector.get_top_talkers(limit)
    return []

@app.get("/api/alerts", response_model=List[AlertMsg])
async def get_alerts(limit: int = 100):
    if detector:
        return detector.get_alerts(limit)
    return []

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    if authenticate(req.username, req.password):
        token = create_token(req.username)
        return {"access_token": token}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/api/mitigate/block")
async def block_ip(req: MitigationRequest, username: str = Depends(verify_token)):
    if mitigator:
        await mitigator.block_ip(req.ip, req.ttl, req.reason, actor=username)
        return {"status": "blocked", "ip": req.ip, "ttl": req.ttl}
    return {"status": "error", "message": "Mitigator not initialized"}

@app.post("/api/mitigate/unblock")
async def unblock_ip(ip: str, username: str = Depends(verify_token)):
    if mitigator:
        await mitigator.unblock_ip(ip, actor=username)
        return {"status": "unblocked", "ip": ip}
    return {"status": "error", "message": "Mitigator not initialized"}

@app.get("/api/mitigate/status")
async def mitigation_status(username: str = Depends(verify_token)) -> Dict:
    if mitigator:
        return mitigator.get_status()
    return {}

@app.get("/api/audit", response_model=List[AuditItem])
async def get_audit(limit: int = 100, username: str = Depends(verify_token)):
    if mitigator:
        return mitigator.get_audit_log(limit)
    return []

async def on_eve_event(obj: dict):
    """Callback for EVE JSON events - runs detection and broadcasts"""
    # Run detection
    alert = None
    if detector:
        alert = detector.on_event(obj)
    
    # Broadcast alert if generated
    if alert:
        await broadcast(alert.dict())
    else:
        # Broadcast event
        event = EventMsg(
            timestamp=obj.get("timestamp", ""),
            event_type=obj.get("event_type", "unknown"),
            src_ip=obj.get("src_ip"),
            dest_ip=obj.get("dest_ip"),
            proto=obj.get("proto"),
            raw=obj
        )
        await broadcast(event.dict())

@app.on_event("startup")
async def startup_event():
    global watcher, detector, mitigator
    detector = DetectionEngine()
    mitigator = Mitigator()
    watcher = EVEWatcher(on_event=on_eve_event)
    asyncio.create_task(watcher.start())

@app.on_event("shutdown")
async def shutdown_event():
    if watcher:
        watcher.stop()
