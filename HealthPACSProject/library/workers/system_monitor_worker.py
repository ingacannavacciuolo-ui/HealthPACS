"""
Modulo per il monitoraggio continuativo delle risorse di sistema e il dispatching delle notifiche.

Il worker `system_monitor_worker` avvia due thread separati in background:
- Thread Heartbeat: Invia periodicamente lo stato ONLINE del servizio via socket.
- Thread Dispatcher: Polla il DB per recuperare e inviare le notifiche pendenti.
"""
import time
import logging
import threading
from typing import Any, Tuple, Dict
from library.constant_health_pacs import MSG_SERVICE_SOCKET_TYPE, SERVICE_STATUS_STATES, APPLICATION_NAME_SERVICE
from library.repository.app_notification_worker_repo import AppNotificationWorkerRepo

logger = logging.getLogger(__name__)


def _check_socket_connection(service_socket: Any) -> bool:
    """Utility per verificare lo stato di connessione del socket."""
    if hasattr(service_socket, "sio") and service_socket.sio:
        return getattr(service_socket.sio, "connected", False)
    elif hasattr(service_socket, "is_connected_event"):
        return service_socket.is_connected_event.is_set()
    return False


def _heartbeat_loop(
    service_socket: Any,
    shutdown_event: threading.Event,
    heartbeat_interval: int,
    retry_interval: int
):
    """Loop dedicato all'emissione periodica dell'Heartbeat."""
    logger.info(f"[HEARTBEAT THREAD] Avviato (Intervallo: {heartbeat_interval}s / Retry: {retry_interval}s)")

    while not shutdown_event.is_set():
        if _check_socket_connection(service_socket):
            try:
                service_socket.send_notification({
                    "msg_type": MSG_SERVICE_SOCKET_TYPE.MSG_SERVICE_STATUS,
                    "sender": APPLICATION_NAME_SERVICE,
                    "status": SERVICE_STATUS_STATES.ONLINE,
                    "message": APPLICATION_NAME_SERVICE + " is ALIVE",
                    "timestamp": time.time()
                })
            except Exception as e:
                logger.error(f"[HEARTBEAT THREAD] Errore nell'invio dell'heartbeat: {e}")
            
            wait_time = heartbeat_interval
        else:
            logger.debug(f"[HEARTBEAT THREAD] Socket disconnesso. Retry tra {retry_interval}s...")
            wait_time = retry_interval

        shutdown_event.wait(timeout=wait_time)

    logger.info("[HEARTBEAT THREAD] Arrestato.")


def _dispatcher_loop(
    service_socket: Any,
    dbmanager: Any,
    shutdown_event: threading.Event,
    dispatcher_interval: int,
    retry_interval: int
):
    """Loop dedicato al polling dal DB e invio notifiche pendenti."""
    logger.info(f"[DISPATCHER THREAD] Avviato (Intervallo: {dispatcher_interval}s / Retry: {retry_interval}s)")

    while not shutdown_event.is_set():
        if _check_socket_connection(service_socket):
            try:
                with dbmanager.get_session() as session:
                    repo = AppNotificationWorkerRepo(session)
                    pending_events = repo.get_pending_socket_notifications()

                    for event in pending_events:
                        logger.info(f"[DISPATCHER THREAD] Invio notifica socket per evento: '{event.notify_key}'")
                        
                        sent_success = service_socket.send_notification({
                            "sender": APPLICATION_NAME_SERVICE,
                            "msg_type": MSG_SERVICE_SOCKET_TYPE.MSG_SERVICE_SEVERITY,                                
                            "notify_key": event.notify_key,
                            "notify_type": event.notify_type,
                            "message": event.notify_description,
                            "permanent": event.permanent,
                            "severity": event.severity,
                            "is_active": True,
                            "timestamp": time.time()
                        })

                        if sent_success:
                            repo.mark_as_sent(event.id)

            except Exception as e:
                logger.error(f"[DISPATCHER THREAD] Errore durante il controllo notifiche DB: {e}", exc_info=True)

            wait_time = dispatcher_interval
        else:
            logger.debug(f"[DISPATCHER THREAD] Socket non connesso. Retry tra {retry_interval}s...")
            wait_time = retry_interval

        shutdown_event.wait(timeout=wait_time)

    logger.info("[DISPATCHER THREAD] Arrestato.")


def start_system_monitor_worker(
    service_socket: Any,
    dbmanager: Any,    
    shutdown_event: threading.Event,
    heartbeat_interval: int = 15,
    dispatcher_interval: int = 5,
    retry_interval: int = 5,
    **kwargs
) -> Tuple[threading.Thread, threading.Thread]:
    """
    Orchestratore che avvia i due thread separati in background per Heartbeat e Dispatcher Notifiche.
    
    Parametri personalizzabili:
    - heartbeat_interval: Frequenza di invio dello stato ALIVE (default: 15s)
    - dispatcher_interval: Frequenza di controllo notifiche a DB (default: 5s)
    - retry_interval: Frequenza di attesa se la socket risulta disconnessa (default: 5s)
    """
    # Fallback/Backward compatibility per argomenti passati col vecchio stile (es. 'interval' o 'normal_interval')
    hb_wait = kwargs.get("heartbeat_interval", heartbeat_interval)
    disp_wait = kwargs.get("dispatcher_interval", dispatcher_interval)
    fast_wait = kwargs.get("retry_interval", kwargs.get("fast_interval", retry_interval))

    # 1. Thread Heartbeat
    heartbeat_thread = threading.Thread(
        target=_heartbeat_loop,
        args=(service_socket, shutdown_event, hb_wait, fast_wait),
        name="HeartbeatThread",
        daemon=True
    )

    # 2. Thread Dispatcher Notifiche
    dispatcher_thread = threading.Thread(
        target=_dispatcher_loop,
        args=(service_socket, dbmanager, shutdown_event, disp_wait, fast_wait),
        name="NotificationDispatcherThread",
        daemon=True
    )

    heartbeat_thread.start()
    dispatcher_thread.start()

    logger.info("[SYSTEM MONITOR] Entrambi i thread (Heartbeat & Dispatcher) sono stati avviati con successo.")

    return heartbeat_thread, dispatcher_thread