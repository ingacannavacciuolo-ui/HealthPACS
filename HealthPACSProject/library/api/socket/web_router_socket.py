from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from library.logger import logger

router = APIRouter(tags=["WebSockets"])

@router.websocket("/web")
async def websocket_web(websocket: WebSocket):
    await websocket.accept()
    logger.info("[WEB WS] Client connesso a HealthPACS Web")
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"status": "ok", "echo": data})
    except WebSocketDisconnect:
        logger.info("[WEB WS] Client disconnesso da HealthPACS Web")