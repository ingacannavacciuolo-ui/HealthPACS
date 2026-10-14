import signal
import sys
import threading
import time
from typing import Optional

import uvicorn
from fastapi import FastAPI
import asyncio
# Import puliti tramite i package __init__.py organizzati precedentemente
from library.api import studies_rest_router, studies_socket_router
from library.dbmanager import DatabaseManager
from library.dicom import DicomServer
from library.logger import HealthPACSLogger
from library.models import Base
from library.repository.container import RepositoryContainer
from library.api.socket import HealthPACSServiceClientSocket
from library.constant_health_pacs import SERVICE_STATUS, SERVICE_STATUS_STATES, LOG_FILE_NAME_SERVICE, APPLICATION_NAME_SERVICE
from library.workers.system_monitor_worker import start_system_monitor_worker

# 1. Istanziazione isolata del logger per HealthPACSWeb
service_logger_instance = HealthPACSLogger(
    app_name=APPLICATION_NAME_SERVICE, 
    log_filename=LOG_FILE_NAME_SERVICE
)
logger = service_logger_instance.get_logger()

# Evento globale per la gestione dello shutdown controllato
shutdown_event = threading.Event()


def signal_handler(signum, frame):
    """Gestore dei segnali di terminazione di sistema (SIGINT, SIGTERM)."""
    sig_name = signal.Signals(signum).name
    logger.info(f"Ricevuto segnale di arresto ({sig_name}). Avvio shutdown controllato...")
    shutdown_event.set()


def create_fastapi_app(dbmanager: DatabaseManager, repos: RepositoryContainer) -> FastAPI:
    """Inizializza e configura l'istanza dell'applicazione FastAPI."""
    app = FastAPI(
        title="HealthPACS VNA / DICOM Backend",
        version="1.0.0",
        description="Backend DICOM con supporto REST, WebSocket e C-STORE/C-FIND."
    )

    # Iniezione delle dipendenze nello stato dell'applicazione
    app.state.dbmanager = dbmanager
    app.state.repos = repos

    # Registrazione dei router API e WebSocket
    app.include_router(studies_rest_router)
    app.include_router(studies_socket_router)

    @app.get("/", tags=["Health"])
    def health_check():
        return {"status": "online", "system": "HealthPACS Backend"}

    return app


def start_api_server(app: FastAPI, host: str = "0.0.0.0", port: int = 8000) -> uvicorn.Server:
    """Avvia il server Uvicorn/FastAPI in background su un thread separato."""
    config = uvicorn.Config(app=app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    logger.info(f"API Server (REST/WebSocket) avviato su http://{host}:{port}")
    return server


def start_dicom_server(dbmanager: DatabaseManager, repos: RepositoryContainer) -> DicomServer:
    """Istanzia e avvia il server DICOM (SCP)."""
    try:
        logger.info("Avvio Server DICOM HealthPACS...")
        dicom_server = DicomServer(dbmanager=dbmanager, repos=repos)
        dicom_server.start()
        return dicom_server
    except Exception as e:
        logger.error(f"Errore durante l'avvio del DICOM Server: {e}", exc_info=True)
        raise e
    
def start_service_socket_client(dbmanager: DatabaseManager) -> HealthPACSServiceClientSocket:
    """Istanziamento ed avvio del client socket in un thread dedicato in background."""
    logger.info("Avvio Client Socket Notifiche verso HealthPACSWeb...")
    
    client_socket = HealthPACSServiceClientSocket(db_manager=dbmanager)

    # Creazione ed avvio del thread sincrono dedicato
    socket_thread = threading.Thread(
        target=client_socket.start, 
        name="SocketClientThread", 
        daemon=True
    )
    socket_thread.start()

    return client_socket




def main():
    dicom_server: Optional[DicomServer] = None
    dbmanager: Optional[DatabaseManager] = None
    api_server: Optional[uvicorn.Server] = None

    # Registrazione degli handler per i segnali di OS/sistema
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 1. Configurazione del Logger        
        logger.info("Inizializzazione di HealthPACS Service...")

        # 2. Connessione e verifica Database
        dbmanager = DatabaseManager()
        if not dbmanager.connect():
            logger.critical("Impossibile connettersi al database. Arresto dell'applicazione.")
            return

        # 3. Inizializzazione della struttura tabelle / schema ORM
        Base.metadata.create_all(bind=dbmanager.engine)

        # 4. Inizializzazione del Container dei Repository
        repos = RepositoryContainer(dbmanager)

        # 5. Avvio del Client Socket per la connessione verso
        #    "web_receiver_socket" necessaria all'invio delle
        #    notifiche recuperate da "start_system_monitor_worker"
        service_socket = start_service_socket_client(dbmanager)

        # 6. Avvio del worker per il dispatching delle notifiche da DB.
        #    Recupera dalla tabella "app_notification_worker" le notifiche 
        #    con stato attivo e le manda al WEB tramite la connesione socket
        #    effettuata da "client_service_socket"
        #    Essendo legato allo shutdown_event, si chiude da solo alla chiusura
        #    del programma.
        start_system_monitor_worker(
            service_socket=service_socket,
            dbmanager=dbmanager,
            shutdown_event=shutdown_event,
            interval=10
        )

        # 7. Avvio del Server DICOM (SCP)
        dicom_server = start_dicom_server(dbmanager, repos)        

        # 8. Avvio opzionale dell'API REST / WebSocket
        app = create_fastapi_app(dbmanager, repos)
        api_server = start_api_server(app, host="0.0.0.0", port=8000)
                  

        logger.info("HealthPACS Service avviato con successo. In attesa di richieste...")

        # Attesa passiva guidata dall'evento di shutdown (evita il consumo CPU del loop di sleep)
        while not shutdown_event.is_set():
            shutdown_event.wait(timeout=1.0)

    except KeyboardInterrupt:
        logger.info("Rilevato CTRL+C. Chiusura in corso...")

    except Exception as e:
        logger.exception(f"Errore critico durante l'esecuzione di HealthPACS: {e}")

    finally:
        logger.info("Inizio procedura di Shutdown...")
        
            
       # 1. Se il socket è ancora attivo, notifichiamo lo stato OFFLINE alla Web App
        if service_socket:
            logger.info("Invio notifica di spegnimento a HealthPACSWeb...")
            service_socket.send_notification({
                "type": SERVICE_STATUS,
                "sender": "HealthPACSService",
                "status": ["OFFLINE"],
                "message": "HealthPACSService è in fase di spegnimento controllato."
            })        
            
            # Arrestiamo il client socket (che invierà la notifica e chiuderà la connessione)
            logger.info("Arresto del Client Socket Notifiche...")
            service_socket.stop()

        # Arresto del Server Web FastAPI/Uvicorn se attivo
        if api_server:
            logger.info("Arresto dell'API Server Web...")
            api_server.should_exit = True

        # Arresto del Server DICOM
        if dicom_server:
            logger.info("Arresto del DICOM Server...")
            dicom_server.stop()

        # Disconnessione e rilascio pool Database
        if dbmanager:
            logger.info("Chiusura del Pool di Connessioni DB...")
            dbmanager.disconnect()

        logger.info("HealthPACS Service arrestato correttamente.")


if __name__ == "__main__":
    main()