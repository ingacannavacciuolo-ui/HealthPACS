import time
import socketio
import logging
from typing import Dict, Any
from library.logger import logger
from library.constant_health_pacs import (
    SERVICE_STATUS,
    WEB_SOCKET_NAMESPACE,
    SERVICE_STATUS_STATES,
    SOCKET_NAMESPACES,
    SOCKET_EVENTS,
)
from library.repository import AppSystemSettingsRepo


# 1. Server Socket.IO asincrono (compatibile ASGI)
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*"
)

# App ASGI esportata per il montaggio su FastAPI
sio_app = socketio.ASGIApp(sio)


# Stato globale in memoria per monitorare lo stato del Service
class ServiceStatusState:
    last_heartbeat: float = 0
    status: str = SERVICE_STATUS_STATES['OFFLINE']

status_state = ServiceStatusState()


class HealthPACSWebReceiverSocket(socketio.AsyncNamespace):
    """
    Namespace Socket.IO dedicato alla ricezione delle notifiche, 
    heartbeat e cambi di stato provenienti da HealthPACSService.
    """
    def __init__(self, db_manager):
        self.dbmanager = db_manager
        self.namespace = SOCKET_NAMESPACES["WEB"]
        super().__init__(self.namespace)

    '''def _load_namespace_from_db(self) -> str:
        """Carica il namespace dal DB usando AppSystemSettingsRepo."""
        if not self.dbmanager:
            logger.error("[WEB SOCKET] Impossibile accedere al DB: db_manager non disponibile.")
            return "/web"

        try:
            repo = AppSystemSettingsRepo(self.dbmanager)
            ns = repo.get_setting_value(WEB_SOCKET_NAMESPACE, default_value="/web")
            if not ns.startswith("/"):
                ns = f"/{ns}"
            logger.info(f"[WEB SOCKET] Namespace caricato da DB: {WEB_SOCKET_NAMESPACE} = '{ns}'")
            return ns
        except Exception as e:
            logger.error(f"[WEB SOCKET] Errore lettura namespace da DB, uso fallback '/web': {e}")
            return "/web"'''

    async def on_connect(self, sid, environ):
        # Log generico e corretto per chiunque si connetta (Browser o Service)
        logger.info(f"[WEB SOCKET RECEIVER] Nuova connessione socket client [sid: {sid}] sul namespace '{self.namespace}'")

        # Calcoliamo lo stato reale verificando se l'ultimo heartbeat del Service è recente
        now = time.time()
        timeout_threshold = 45  # Tolleranza su 3 cicli di heartbeat (15s * 3)

        # Se l'ultimo heartbeat è recente E lo stato salvato era ONLINE, inviamo ONLINE
        if status_state.last_heartbeat > 0 and (now - status_state.last_heartbeat) < timeout_threshold and status_state.status == SERVICE_STATUS_STATES['ONLINE']:
            current_status = SERVICE_STATUS_STATES['ONLINE']
            msg = "HealthPACSService è operativo"
        else:
            current_status = SERVICE_STATUS_STATES['OFFLINE']
            msg = "HealthPACSService non raggiungibile"
        
        # Risponde subito inviando lo stato REALE memorizzato nel server (es. OFFLINE se il service è giù)
        await self.emit(
            SOCKET_EVENTS["SERVICE_STATUS_UPDATE"],
            {
                "type": SERVICE_STATUS,
                "status": current_status,
                "message": msg
            },
            to=sid
        )

    async def on_message(self, sid, data: Dict[str, Any]):
        """
        Dispatcher principale: analizza il campo 'type' ed esegue l'handler dedicato.
        """
        if not isinstance(data, dict):
            logger.warning(f"[WEB SOCKET RECEIVER] Payload non valido ricevuto da [sid: {sid}]: {data}")
            return

        msg_type = data.get("type")
        logger.info(f"[WEB SOCKET RECEIVER] Notifica ricevuta [{msg_type}] da [sid: {sid}]")

        # Routing in base al tipo di notifica
        # Notifica la web che il sistema service è alive
        if msg_type == SERVICE_STATUS:
            await self._handle_service_status(data)

          

        else:
            logger.warning(f"[WEB SOCKET RECEIVER] Tipo notifica non gestito: '{msg_type}'")
            # Inoltro generico di fallback a eventuali client web connessi
            await self.emit("GENERIC_NOTIFICATION", data)

    
    '''elif msg_type == DICOM_JOB_STATUS:
                await self._handle_dicom_job_status(data)

            elif msg_type == STORAGE_ALERT:
                await self._handle_storage_alert(data)

            elif msg_type == WORKLIST_SYNC:
                await self._handle_worklist_sync(data)'''
    

    async def on_disconnect(self, sid):
        logger.warning(f"[WEB SOCKET RECEIVER] HealthPACSService disconnesso [sid: {sid}] dal namespace '{self.namespace}'")
        status_state.status = SERVICE_STATUS_STATES['OFFLINE']

        # Notifica la caduta della connessione del servizio ai client/browser
        await self.emit(
            SOCKET_EVENTS["SERVICE_STATUS_UPDATE"],
            {
                "type": SERVICE_STATUS,
                "status": SERVICE_STATUS_STATES['OFFLINE'],
                "message": "Connessione con HealthPACSService interrotta.",
                "timestamp": time.time(),
            }
        )

    # --- HANDLER DEDICATI PER TIPOLOGIA ---

    async def _handle_service_status(self, data: Dict[str, Any]):
        """Gestisce Heartbeat e stato operativo di HealthPACSService."""
        status_state.last_heartbeat = time.time()
        status_state.status = data.get("status", SERVICE_STATUS_STATES['OFFLINE'])

        logger.info(f"[STATUS HANDLER] Service status: {status_state.status} | Msg: {data.get('message')}")
       
        await self.emit(SOCKET_EVENTS["SERVICE_STATUS_UPDATE"], data)

    async def _handle_dicom_job_status(self, data: Dict[str, Any]):
        """Gestisce lo stato di elaborazione/ricezione/invio di uno studio DICOM."""
        study_instance_uid = data.get("study_uid")
        job_state = data.get("job_state")  # es. "PROCESSING", "COMPLETED", "FAILED"
        
        logger.info(f"[DICOM HANDLER] Studio UID {study_instance_uid} -> Stato: {job_state}")
        
        # Inoltra in broadcast l'aggiornamento alla Dashboard/Interfaccia Web
        await self.emit("DICOM_JOB_UPDATE", data)

    async def _handle_storage_alert(self, data: Dict[str, Any]):
        """Gestisce avvisi di spazio in esaurimento o errori sui dischi PACS."""
        severity = data.get("severity", "WARNING")
        free_gb = data.get("free_gb")

        logger.warning(f"[STORAGE ALERT] Livello: {severity} | Spazio residuo: {free_gb} GB")
        await self.emit("SYSTEM_ALERT", data)

    async def _handle_worklist_sync(self, data: Dict[str, Any]):
        """Gestisce notifiche di sincronizzazione Worklist Modality."""
        synced_items = data.get("synced_count", 0)
        logger.info(f"[WORKLIST HANDLER] Sincronizzati {synced_items} elementi Modality Worklist.")
        await self.emit("WORKLIST_UPDATE", data)


def init_socket_receiver(db_manager) -> HealthPACSWebReceiverSocket:
    """Inizializza e registra l'istanza del receiver Socket.IO."""
    receiver = HealthPACSWebReceiverSocket(db_manager)
    sio.register_namespace(receiver)
    return receiver