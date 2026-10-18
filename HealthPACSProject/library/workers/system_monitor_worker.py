"""
Modulo per il monitoraggio continuativo delle risorse di sistema.

Il worker `system_monitor_worker` opera in background e si occupa di:
- Raccogliere e tracciare metriche hardware/sistema in tempo reale (CPU, RAM, 
  disco, rete, processi).
- Registrare i log di performance ed evidenziare eventuali anomalie o utilizzi critici.
- Inviare o salvare i dati aggregati per la visualizzazione in dashboard o dashboard alert.
"""
"""Module for continuous system resource monitoring.

The `system_monitor_worker` background worker performs the following tasks:
- Collects and tracks real-time hardware and system metrics (CPU, RAM,
  disk, network, processes).
- Logs performance metrics and flags anomalies or critical utilization levels.
- Sends or saves aggregated data for display in dashboards or alert systems.
"""
import time
import logging
import threading
from typing import Any
from library.constant_health_pacs import MSG_SERVICE_SOCKET_TYPE, SERVICE_STATUS_STATES, APPLICATION_NAME_SERVICE
from library.repository.app_notification_worker_repo import AppNotificationWorkerRepo
logger = logging.getLogger(__name__)


def start_system_monitor_worker(
    service_socket: Any,
    dbmanager: Any,
    repo_container: Any,
    shutdown_event: threading.Event,
    interval: int = 10,
    fast_interval: int = 5,
    normal_interval: int = 15,
    **kwargs
) -> threading.Thread:
    """
    Worker centralizzato eseguito in background per Heartbeat e Notifiche DB.
    Accetta 'interval', 'fast_interval', 'normal_interval' o kwargs generici per massima flessibilità.
    """
    # Se viene passato solo 'interval', lo usiamo sia per retry che per regime
    fast_wait = kwargs.get("fast_interval", interval or fast_interval)
    normal_wait = kwargs.get("normal_interval", interval or normal_interval)

    def monitor_loop():
        logger.info(f"[SYSTEM MONITOR] Worker avviato (Intervallo: {fast_wait}s retry / {normal_wait}s regime)")

        while not shutdown_event.is_set():
            # Verifichiamo la connessione reale del Socket Client
            is_connected = False
            if hasattr(service_socket, "sio") and service_socket.sio:
                is_connected = getattr(service_socket.sio, "connected", False)
            elif hasattr(service_socket, "is_connected_event"):
                is_connected = service_socket.is_connected_event.is_set()

            if is_connected:
                # 1. EMISSIONE HEARTBEAT
                service_socket.send_notification({
                    "msg_type": MSG_SERVICE_SOCKET_TYPE.MSG_SERVICE_STATUS,
                    "sender": APPLICATION_NAME_SERVICE,
                    "status": SERVICE_STATUS_STATES.ONLINE,
                    "message": APPLICATION_NAME_SERVICE + " is ALIVE",
                    "timestamp": time.time()
                })

                # 2. DISPATCHER NOTIFICHE DA DB (is_active=True, is_sent=False)
                try:
                    with dbmanager.get_session() as session:
                        repo = AppNotificationWorkerRepo(session)
                        pending_events = repo.get_pending_socket_notifications()

                        for event in pending_events:
                            logger.info(f"[SYSTEM MONITOR] Invio notifica socket per evento: '{event.notify_key}'")
                            
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
                                repo_container.appnotificationworkerrepo.mark_as_sent(event.id)

                except Exception as e:
                    logger.error(f"[SYSTEM MONITOR] Errore durante il controllo notifiche DB: {e}", exc_info=True)

                current_wait = normal_wait
            else:
                logger.debug(f"[SYSTEM MONITOR] Socket non connesso. Prossimo tentativo tra {fast_wait}s...")
                current_wait = fast_wait

            # Attesa non bloccante
            shutdown_event.wait(timeout=current_wait)

        logger.info("[SYSTEM MONITOR] Worker arrestato.")

    thread = threading.Thread(target=monitor_loop, name="SystemMonitorThread", daemon=True)
    thread.start()
    return thread