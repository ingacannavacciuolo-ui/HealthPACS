import signal
import sys
import threading
import time
from typing import Optional

import uvicorn
from fastapi import FastAPI

# Import puliti tramite i package __init__.py organizzati precedentemente
from library.api import studies_rest_router, studies_socket_router
from library.dbmanager import DatabaseManager
from library.dicom import DicomServer
from library.logger import logger, setup_logger_file
from library.models import Base
from library.repository.container import RepositoryContainer

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


def main():
    dicom_server: Optional[DicomServer] = None
    dbmanager: Optional[DatabaseManager] = None
    api_server: Optional[uvicorn.Server] = None

    # Registrazione degli handler per i segnali di OS/sistema
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 1. Configurazione del Logger
        setup_logger_file("healthpacs.log")
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

        # 5. Avvio del Server DICOM (SCP)
        dicom_server = start_dicom_server(dbmanager, repos)

        # 6. Avvio opzionale dell'API REST / WebSocket
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