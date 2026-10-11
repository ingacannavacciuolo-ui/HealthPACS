# library/socket/client_service_socket.py

import json
import time
import threading
from typing import Optional, Dict, Any
from queue import Queue, Empty
import socketio

from library.logger import logger
from library.repository import AppSystemSettingsRepo
from library.constant_health_pacs import (
    WEB_SOCKET_URL,
    SOCKET_NAMESPACES,
)


class HealthPACSServiceClientSocket:
    """
    Client Socket.IO per HealthPACSService.
    Gestisce la connessione automatica resiliente e l'invio non bloccante di notifiche verso HealthPACSWeb.
    """

    def __init__(self, db_manager, max_buffer_size: int = 100):
        self.dbmanager = db_manager
        self.web_ws_url: Optional[str] = None
        self.namespace: Optional[str] = None
        self.is_running = False

        # Evento thread-safe per sincronizzare l'heartbeat
        self.is_connected_event = threading.Event()

        self.sio = socketio.Client(
            reconnection=True,
            reconnection_attempts=0,   # Tenta all'infinito se cade dopo essersi connesso
            reconnection_delay=2,
            reconnection_delay_max=30,
            logger=False
        )

        self._message_queue: Queue = Queue(maxsize=max_buffer_size)

    def _setup_events(self):
        """Registrazione degli eventi Socket.IO specificando il namespace corretto."""

        @self.sio.event(namespace=self.namespace)
        def connect():
            logger.info("[SERVICE SOCKET] Connessione fissa stabilita con HealthPACSWeb!")
            self.is_connected_event.set()
            self._flush_buffer()

        @self.sio.event(namespace=self.namespace)
        def disconnect():
            logger.warning("[SERVICE SOCKET] Disconnesso da HealthPACSWeb. Riconnessione in background...")
            self.is_connected_event.clear()

        @self.sio.event(namespace=self.namespace)
        def connect_error(data):
            logger.error(f"[SERVICE SOCKET] Errore connessione: {data}")
            self.is_connected_event.clear()

    def load_config_from_db(self) -> bool:
        if not self.dbmanager:
            logger.error("[SERVICE SOCKET] Impossibile accedere al DB: db_manager non disponibile.")
            return False

        try:
            repo = AppSystemSettingsRepo(self.dbmanager)
            url_from_db = repo.get_setting_value(WEB_SOCKET_URL, default_value="http://localhost:5000")
            if url_from_db.startswith("ws://"):
                url_from_db = url_from_db.replace("ws://", "http://")
            elif url_from_db.startswith("wss://"):
                url_from_db = url_from_db.replace("wss://", "https://")

            self.web_ws_url = url_from_db
            logger.info(f"[SERVICE SOCKET] Impostazione caricata da DB: {WEB_SOCKET_URL} = '{self.web_ws_url}'")

            # 2. Caricamento Namespace dal DB
            self.namespace = SOCKET_NAMESPACES["WEB"]#repo.get_setting_value(WEB_SOCKET_NAMESPACE, default_value=DEFAULT_WEB_SOCKET_NAMESPACE)
            logger.info(f"[SERVICE SOCKET] Impostazione caricata da DB: {SOCKET_NAMESPACES["WEB"]} = '{self.namespace}'")

            # REGISTRIAMO GLI EVENTI ORA CHE IL NAMESPACE È NOTO!
            self._setup_events()

            return True
        except Exception as e:
            logger.error(f"[SERVICE SOCKET] Errore lettura impostazioni da DB: {e}")
            return False

    def start(self):
        """Metodo eseguito all'interno del Thread dedicato 'SocketClientThread'."""
        if self.is_running:
            logger.warning("[SERVICE SOCKET] Client già avviato.")
            return

        if not self.load_config_from_db():
            logger.error("[SERVICE SOCKET] Impossibile avviare: configurazione DB fallita.")
            return

        if not self.web_ws_url:
            logger.error("[SERVICE SOCKET] Impossibile avviare: WEB_SOCKET_URL non valido o assente.")
            return

        self.is_running = True
        self._connection_loop()

    def _connection_loop(self):
        """Loop in background eseguito sul thread dedicato per garantire il primo aggancio."""
        delay = 2
        max_delay = 30

        while self.is_running:
            if not self.sio.connected:
                self.is_connected_event.clear()
                try:
                    logger.info(f"[SERVICE SOCKET] Tentativo connessione a HealthPACSWeb ({self.web_ws_url})...")
                    self.sio.connect(
                        self.web_ws_url, 
                        namespaces=[self.namespace], 
                        wait_timeout=3
                    )
                    delay = 2  # Reset del delay
                except Exception:
                    logger.warning(f"[SERVICE SOCKET] Web Server non raggiungibile. Prossimo tentativo tra {delay}s...")
                    time.sleep(delay)
                    delay = min(delay * 1.5, max_delay)
            else:
                time.sleep(1)

    def send_notification(self, payload: Dict[str, Any]) -> bool:
        if not isinstance(payload, dict) or "type" not in payload:
            logger.error("[SERVICE SOCKET] Payload non valido: la chiave 'type' è obbligatoria.")
            return False

        if self.sio.connected:
            return self._send_raw(payload)
        else:
            try:
                self._message_queue.put_nowait(payload)
                logger.debug(f"[SERVICE SOCKET] Offline: Notifica '{payload['type']}' salvata in coda.")
                return True
            except Exception:
                logger.error("[SERVICE SOCKET] Coda offline piena! Notifica scartata.")
                return False

    def _send_raw(self, payload: Dict[str, Any]) -> bool:
        try:
            if self.sio.connected:
                self.sio.emit("message", payload, namespace=self.namespace)
                return True
        except Exception as e:
            logger.error(f"[SERVICE SOCKET] Errore di invio socket: {e}")
        return False

    def _flush_buffer(self):
        while self.sio.connected and not self._message_queue.empty():
            try:
                payload = self._message_queue.get_nowait()
                sent = self._send_raw(payload)
                if not sent:
                    self._message_queue.put(payload)
                    break
            except Empty:
                break

    def stop(self):
        logger.info("[SERVICE SOCKET] Arresto in corso...")
        self.is_running = False
        self.is_connected_event.clear()

        if self.sio.connected:
            try:
                self.sio.disconnect()
            except Exception:
                pass          

        logger.info("[SERVICE SOCKET] Client Socket arrestato.")