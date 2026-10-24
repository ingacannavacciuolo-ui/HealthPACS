import time
import socketio
from typing import Dict, Any
from app.core.logger import logger
from app.core.constants import (
    MSG_SERVICE_SOCKET_TYPE,
    SERVICE_STATUS_STATES,
    SOCKET_NAMESPACES,
    SOCKET_EVENTS,
    NOTIFY_KEY,    
    NOTIFY_SEVERITY,
    LANG_KEY,
    APPLICATION_NAME_SERVICE
)
from app.repository import AppNotificationWorkerRepo


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
    status: str = SERVICE_STATUS_STATES.OFFLINE

status_state = ServiceStatusState()


class HealthPACSWebReceiverSocket(socketio.AsyncNamespace):
    """
    Namespace Socket.IO dedicato alla ricezione delle notifiche, 
    heartbeat e cambi di stato provenienti da HealthPACSService.
    """
    def __init__(self, db_manager, lang: str = "it", fallback_lang: str = "en",):
        self.dbmanager = db_manager
        self.namespace = SOCKET_NAMESPACES.WEB
        self.service_sid = None  # Memorizza il SID di HealthPACSService
        self.lang = lang
        self.fallback_lang =fallback_lang
        super().__init__(self.namespace)

   

    async def on_connect(self, sid, environ):
        logger.info(f"[WEB SOCKET RECEIVER] Nuova connessione client [sid: {sid}]")
        
        # Verifichiamo se l'ultimo heartbeat è recente (es. ultimi 45 secondi)
        now = time.time()
        is_alive = (
            status_state.last_heartbeat > 0 
            and (now - status_state.last_heartbeat) < 45 
            and status_state.status == SERVICE_STATUS_STATES.ONLINE
        )
        
        current_status = SERVICE_STATUS_STATES.ONLINE if is_alive else SERVICE_STATUS_STATES.OFFLINE

        # Risponde SOLO al browser appena connesso con lo stato reale freschissimo
        await self.emit(
            SOCKET_EVENTS.SERVICE_STATUS_UPDATE,
            {
                "status": current_status,
                "message": LANG_KEY.SERVICE_STATUS_CURRENT_MSG
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
        msg_type = data.get("msg_type")
       

        # Se si tratta dello stato del servizio, lo gestiamo tramite il tipo
        if msg_type == MSG_SERVICE_SOCKET_TYPE.MSG_SERVICE_STATUS:
            await self._handle_service_status(data)
        # Se si tratta dello stato di severity, lo gestiamo tramite il tipo
        elif msg_type == MSG_SERVICE_SOCKET_TYPE.MSG_SERVICE_SEVERITY:
            await self._handle_service_severity(data)
           
        

    async def on_disconnect(self, sid):
        # SOLTANTO se a disconnettersi è il vero Service impostiamo OFFLINE e notifichiamo a tutti!
        if sid == self.service_sid:
            logger.warning(f"[WEB SOCKET RECEIVER] HealthPACSService disconnesso [sid: {sid}]")
            self.service_sid = None
            status_state.status = SERVICE_STATUS_STATES.OFFLINE

            await self.emit(
                SOCKET_EVENTS.SERVICE_STATUS_UPDATE,
                {
                    "msg_type": MSG_SERVICE_SOCKET_TYPE.MSG_SERVICE_STATUS,
                    "status": SERVICE_STATUS_STATES.OFFLINE,
                    "message": LANG_KEY.SERVICE_OFFLINE,
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
                    localized_msg = event.get_description(lang=self.lang, fallback_lang=self.fallback_lang)
                    alerts_data.append({
                        "sender": APPLICATION_NAME_SERVICE,
                        "msg_type": MSG_SERVICE_SOCKET_TYPE.MSG_SERVICE_SEVERITY,                        
                        "notify_key": event.notify_key,
                        "notify_type": event.notify_type,
                        "message":localized_msg,
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
        status_state.status = data.get("status", SERVICE_STATUS_STATES.OFFLINE)

        logger.info(f"[STATUS HANDLER] Service status: {status_state.status} | Msg: {data.get('message')}")
        # EMIT verso il client Web         
        await self.emit(SOCKET_EVENTS.SERVICE_STATUS_UPDATE, data)



    async def _handle_service_severity(self, data: Dict[str, Any]):
        severity = str(data.get("severity", "")).upper()
        if severity == NOTIFY_SEVERITY.CRITICAL:
                await self._handle_severity_critical(data)

        elif severity == NOTIFY_SEVERITY.WARNING:
            await self._handle_severity_warning(data)

        elif severity == NOTIFY_SEVERITY.INFO:
            await self._handle_severity_info(data)

        else:
            await self.emit(NOTIFY_SEVERITY.GENERIC, data)

        

    async def _handle_severity_critical(self, data: Dict[str, Any]):
        """Gestisce avvisi critici (CRITICAL)."""
        notify_key = data.get("notify_key", NOTIFY_KEY.UNKNOWN_KEY)
        message = data.get("message", LANG_KEY.NO_DETAILS_PROVIDED)

        logger.warning(f"[CRITICAL ALERT] Key: {notify_key} | Msg: {message}")

        # Emette sul canale socket dedicato 'CRITICAL'
        await self.emit(NOTIFY_SEVERITY.CRITICAL, data)



    async def _handle_severity_warning(self, data: Dict[str, Any]):
        """Gestisce avvisi di avvertimento (WARNING)."""
        notify_key = data.get("notify_key", NOTIFY_KEY.UNKNOWN_KEY)
        message = data.get("message", LANG_KEY.NO_DETAILS_PROVIDED)

        logger.warning(f"[WARNING ALERT] Key: {notify_key} | Msg: {message}")

        # Emette sul canale socket dedicato 'WARNING'
        await self.emit(NOTIFY_SEVERITY.WARNING, data)




    async def _handle_severity_info(self, data: Dict[str, Any]):
        """Gestisce avvisi informativi (INFO)."""
        notify_key = data.get("notify_key", NOTIFY_KEY.UNKNOWN_KEY)
        message = data.get("message", LANG_KEY.NO_DETAILS_PROVIDED)

        logger.info(f"[INFO ALERT] Key: {notify_key} | Msg: {message}")

        # Emette sul canale socket dedicato 'INFO'
        await self.emit(NOTIFY_SEVERITY.INFO, data)



def init_socket_receiver(
        db_manager,
        lang: str = "it",
        fallback_lang: str = "en",
    ) -> HealthPACSWebReceiverSocket:
    """Inizializza e registra l'istanza del receiver Socket.IO."""
    receiver = HealthPACSWebReceiverSocket(db_manager, lang, fallback_lang)
    sio.register_namespace(receiver)
    return receiver