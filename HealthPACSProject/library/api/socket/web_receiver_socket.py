import time
import socketio
import logging
from typing import Dict, Any
from library.logger import logger
from library.constant_health_pacs import (
    SERVICE_STATUS,
    SERVICE_STATUS_STATES,
    SOCKET_NAMESPACES,
    SOCKET_EVENTS,
    NOTIFY_KEY,
    NOTIFY_TYPE,
    SEVERITY,
    APPLICATION_NAME_SERVICE
)
from library.repository import AppNotificationWorkerRepo


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
        self.service_sid = None  # Memorizza il SID di HealthPACSService
        super().__init__(self.namespace)

   

    async def on_connect(self, sid, environ):
        logger.info(f"[WEB SOCKET RECEIVER] Nuova connessione client [sid: {sid}]")
        
        # Verifichiamo se l'ultimo heartbeat è recente (es. ultimi 45 secondi)
        now = time.time()
        is_alive = (
            status_state.last_heartbeat > 0 
            and (now - status_state.last_heartbeat) < 45 
            and status_state.status == SERVICE_STATUS_STATES['ONLINE']
        )
        
        current_status = SERVICE_STATUS_STATES['ONLINE'] if is_alive else SERVICE_STATUS_STATES['OFFLINE']

        # Risponde SOLO al browser appena connesso con lo stato reale freschissimo
        await self.emit(
            SOCKET_EVENTS["SERVICE_STATUS_UPDATE"],
            {
                "status": current_status,
                "message": "Stato corrente del servizio PACS"
            },
            to=sid
        )


    async def on_message(self, sid, data: Dict[str, Any]):
        if not isinstance(data, dict):
            return
        
        # Registra il SID solo se il mittente è il servizio backend
        if data.get("sender") != APPLICATION_NAME_SERVICE:
            return

        self.service_sid = sid
        msg_type = data.get("type")
        severity = str(data.get("severity", "")).upper()

        # Se si tratta dello stato del servizio, lo gestiamo tramite il tipo
        if msg_type == SERVICE_STATUS:
            await self._handle_service_status(data)

        # Routing basato interamente sulla SEVERITY
        elif severity == SEVERITY["CRITICAL"]:
            await self._handle_severity_critical(data)

        elif severity == SEVERITY["WARNING"]:
            await self._handle_severity_warning(data)

        elif severity == SEVERITY["INFO"]:
            await self._handle_severity_info(data)

        else:
            await self.emit("GENERIC_NOTIFICATION", data)
        

    async def on_disconnect(self, sid):
        # SOLTANTO se a disconnettersi è il vero Service impostiamo OFFLINE e notifichiamo a tutti!
        if sid == self.service_sid:
            logger.warning(f"[WEB SOCKET RECEIVER] HealthPACSService disconnesso [sid: {sid}]")
            self.service_sid = None
            status_state.status = SERVICE_STATUS_STATES['OFFLINE']

            await self.emit(
                SOCKET_EVENTS["SERVICE_STATUS_UPDATE"],
                {
                    "type": SERVICE_STATUS,
                    "status": SERVICE_STATUS_STATES['OFFLINE'],
                    "message": "Connessione con HealthPACSService interrotta.",
                    "timestamp": time.time(),
                }
            )
        else:
            # Se è la disconnessione di un browser (F5/Refresh), ignoriamo silenziosamente
            logger.info(f"[WEB SOCKET RECEIVER] Browser disconnesso [sid: {sid}] (nessun impatto sullo stato)")

   
    # Recupera tutti gli alert attivi per mandarli al browser
    async def on_get_active_alerts(self, sid):
        """
        Invocato quando un browser (incluso F5/refresh) richiede la lista 
        delle allerte attualmente attive nel DB.
        """
        logger.info(f"[WEB SOCKET RECEIVER] Richiesta allerte attive dal client [sid: {sid}]")
        try:
            with self.dbmanager.get_session() as session:
                # Usa il repository per recuperare le allerte con is_active = True
                repo = AppNotificationWorkerRepo(session)
                active_events = repo.get_active_notifications()  # o repo.get_all_active_notifications()

                alerts_data = []
                for event in active_events:
                    alerts_data.append({
                        "sender": APPLICATION_NAME_SERVICE,
                        "type": event.notify_type,
                        "notify_key": event.notify_key,
                        "message": event.notify_description,
                        "permanent": event.permanent,
                        "severity": event.severity,
                        "is_active": True,
                        "timestamp": time.time()
                    })

                # Invia la lista ESCLUSIVAMENTE al client richiedente (sid)
                await self.emit("active_alerts_list", alerts_data, to=sid)
                logger.info(f"[WEB SOCKET RECEIVER] Inviate {len(alerts_data)} allerte attive al client [sid: {sid}]")

        except Exception as e:
            logger.error(f"[WEB SOCKET RECEIVER] Errore durante il recupero delle allerte attive per sid {sid}: {e}", exc_info=True)
   
   
    # --- HANDLER DEDICATI PER TIPOLOGIA ---

    async def _handle_service_status(self, data: Dict[str, Any]):
        """Gestisce Heartbeat e stato operativo di HealthPACSService."""
        status_state.last_heartbeat = time.time()
        status_state.status = data.get("status", SERVICE_STATUS_STATES['OFFLINE'])

        logger.info(f"[STATUS HANDLER] Service status: {status_state.status} | Msg: {data.get('message')}")
        # EMIT verso il client Web (es. sul namespace LOGIN o SISTEMA)
        await sio.emit(
            SOCKET_EVENTS["SERVICE_STATUS_UPDATE"], 
            {
                'status': status_state.status,
                'message': data.get('message', '')
            }, 
            namespace=self.namespace  # oppure SISTEMA
        )
        await self.emit(SOCKET_EVENTS["SERVICE_STATUS_UPDATE"], data)

        

    async def _handle_severity_critical(self, data: Dict[str, Any]):
        """Gestisce avvisi critici (CRITICAL)."""
        notify_key = data.get("notify_key", "UNKNOWN_KEY")
        message = data.get("message", "Nessun dettaglio fornito")

        logger.warning(f"[CRITICAL ALERT] Key: {notify_key} | Msg: {message}")

        # Emette sul canale socket dedicato 'CRITICAL'
        await self.emit(SEVERITY["CRITICAL"], data)



    async def _handle_severity_warning(self, data: Dict[str, Any]):
        """Gestisce avvisi di avvertimento (WARNING)."""
        notify_key = data.get("notify_key", "UNKNOWN_KEY")
        message = data.get("message", "Nessun dettaglio fornito")

        logger.warning(f"[WARNING ALERT] Key: {notify_key} | Msg: {message}")

        # Emette sul canale socket dedicato 'WARNING'
        await self.emit(SEVERITY["WARNING"], data)




    async def _handle_severity_info(self, data: Dict[str, Any]):
        """Gestisce avvisi informativi (INFO)."""
        notify_key = data.get("notify_key", "UNKNOWN_KEY")
        message = data.get("message", "Nessun dettaglio fornito")

        logger.info(f"[INFO ALERT] Key: {notify_key} | Msg: {message}")

        # Emette sul canale socket dedicato 'INFO'
        await self.emit(SEVERITY["INFO"], data)




    '''async def _handle_severity_warning(self, data: Dict[str, Any]):
        """Gestisce avvisi di avvertimento (WARNING)."""
        notify_type = data.get("type", "UNKNOWN_TYPE")
        notify_key = data.get("notify_key", "UNKNOWN_KEY")
        severity = data.get("severity", "WARNING")
        message = data.get("message", "Nessun dettaglio fornito")
        permanent = data.get("permanent", False)
        is_active = data.get("is_active", True)

        logger.warning(
            f"[WARNING ALERT] [{notify_type}] Key: {notify_key} | Severity: {severity} | "
            f"Permanent: {permanent} | Active: {is_active} | Msg: {message}"
        )

        # Invia il payload completo via socket ai client connessi
        await self.emit("SYSTEM_ALERT", data)


    async def _handle_severity_info(self, data: Dict[str, Any]):
        """Gestisce avvisi informativi (INFO)."""
        notify_type = data.get("type", "UNKNOWN_TYPE")
        notify_key = data.get("notify_key", "UNKNOWN_KEY")
        severity = data.get("severity", "INFO")
        message = data.get("message", "Nessun dettaglio fornito")
        permanent = data.get("permanent", False)
        is_active = data.get("is_active", True)

        logger.info(
            f"[INFO ALERT] [{notify_type}] Key: {notify_key} | Severity: {severity} | "
            f"Permanent: {permanent} | Active: {is_active} | Msg: {message}"
        )

        # Invia il payload completo via socket ai client connessi
        await self.emit("SYSTEM_ALERT", data)

    async def _handle_dicom_job_status(self, data: Dict[str, Any]):
        """Gestisce lo stato di elaborazione/ricezione/invio di uno studio DICOM."""
        study_instance_uid = data.get("study_uid")
        job_state = data.get("job_state")  # es. "PROCESSING", "COMPLETED", "FAILED"
        
        logger.info(f"[DICOM HANDLER] Studio UID {study_instance_uid} -> Stato: {job_state}")
        
        # Inoltra in broadcast l'aggiornamento alla Dashboard/Interfaccia Web
        await self.emit("DICOM_JOB_UPDATE", data)



    async def _handle_sistem_alert(self, data: Dict[str, Any]):
        """Gestisce avvisi di spazio in esaurimento o errori sui dischi PACS."""
        notify_type = data.get("type", NOTIFY_TYPE["SYSTEM_ALERT"])
        notify_key = data.get("notify_key", "UNKNOWN_KEY")
        severity = data.get("severity", "WARNING")
        message = data.get("message", "Nessun dettaglio fornito")
        permanent = data.get("permanent", False)
        is_active = data.get("is_active", True)

        logger.warning(
            f"[{notify_type}] Key: {notify_key} | Severity: {severity} | "
            f"Permanent: {permanent} | Active: {is_active} | Msg: {message}"
        )

        # Invia il payload completo via socket ai client connessi
        await self.emit(notify_type, data)




    async def _handle_worklist_sync(self, data: Dict[str, Any]):
        """Gestisce notifiche di sincronizzazione Worklist Modality."""
        synced_items = data.get("synced_count", 0)
        logger.info(f"[WORKLIST HANDLER] Sincronizzati {synced_items} elementi Modality Worklist.")
        await self.emit("WORKLIST_UPDATE", data)'''





def init_socket_receiver(db_manager) -> HealthPACSWebReceiverSocket:
    """Inizializza e registra l'istanza del receiver Socket.IO."""
    receiver = HealthPACSWebReceiverSocket(db_manager)
    sio.register_namespace(receiver)
    return receiver