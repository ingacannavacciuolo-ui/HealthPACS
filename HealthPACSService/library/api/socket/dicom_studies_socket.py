# library/api/socket/dicom_studies_socket.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from library.services.dicom_studies_service import DicomStudiesService
from library.logger import logger

router = APIRouter()


@router.websocket("/ws/studies")
async def studies_websocket_endpoint(
    websocket: WebSocket, service: DicomStudiesService = Depends()
):
    """Canale WebSocket per interazioni sul dominio DICOM Studies in tempo reale.
    
    Protocollo JSON atteso dal client:
    {
        "token": "session_token_utente",
        "action": "GET_BY_ID" | "GET_BY_UID" | "LIST_BY_EQUIPMENT" | "DELETE",
        "params": { ... }
    }
    """
    await websocket.accept()
    logger.info("WebSocket DicomStudies: Nuova connessione client stabilita.")

    try:
        while True:
            payload = await websocket.receive_json()
            token = payload.get("token")
            action = payload.get("action")
            params = payload.get("params", {})

            if not token:
                await websocket.send_json(
                    {
                        "status": "error",
                        "code": 401,
                        "message": "Token di sessione mancante.",
                    }
                )
                continue

            try:
                # Dispatching azioni al DicomStudiesService
                if action == "GET_BY_ID":
                    study_id = params.get("study_id")
                    result = service.get_study_by_id(
                        session_token=token, study_id=study_id
                    )
                    await websocket.send_json(
                        {"status": "success", "action": action, "data": result}
                    )

                elif action == "GET_BY_UID":
                    uid = params.get("study_instance_uid")
                    result = service.get_study_by_uid(
                        session_token=token, study_instance_uid=uid
                    )
                    await websocket.send_json(
                        {"status": "success", "action": action, "data": result}
                    )

                elif action == "LIST_BY_EQUIPMENT":
                    equipment_id = params.get("equipment_id")
                    limit = params.get("limit", 100)
                    offset = params.get("offset", 0)
                    studies = service.list_studies_by_equipment(
                        session_token=token, equipment_id=equipment_id, limit=limit, offset=offset
                    )
                    total = service.count_studies_by_equipment(
                        session_token=token, equipment_id=equipment_id
                    )
                    await websocket.send_json(
                        {
                            "status": "success",
                            "action": action,
                            "total": total,
                            "data": studies,
                        }
                    )

                elif action == "DELETE":
                    study_id = params.get("study_id")
                    success = service.delete_study(
                        session_token=token, study_id=study_id
                    )
                    await websocket.send_json(
                        {"status": "success", "action": action, "deleted": success}
                    )

                else:
                    await websocket.send_json(
                        {
                            "status": "error",
                            "code": 400,
                            "message": f"Azione '{action}' sconosciuta.",
                        }
                    )

            except PermissionError as pe:
                await websocket.send_json(
                    {"status": "error", "code": 403, "message": str(pe)}
                )

    except WebSocketDisconnect:
        logger.info("WebSocket DicomStudies: Client disconnesso.")