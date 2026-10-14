import os
import sys
import signal
import threading
import uvicorn
from fastapi import FastAPI,Request, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from library.dbmanager import DatabaseManager
from library.logger import HealthPACSLogger
from library.repository.container import RepositoryContainer
from library.api import pages_router, sio_app, init_socket_receiver
from library.constant_health_pacs import LOG_FILE_NAME_WEB, APPLICATION_NAME_WEB



# 1. Istanziazione isolata del logger per HealthPACSWeb
web_logger_instance = HealthPACSLogger(
    app_name=APPLICATION_NAME_WEB, 
    log_filename=LOG_FILE_NAME_WEB
)
logger = web_logger_instance.get_logger()


shutdown_event = threading.Event()


def signal_handler(signum, frame):
    sig_name = signal.Signals(signum).name
    logger.info(f"[WEB] Ricevuto segnale di arresto ({sig_name}). Avvio shutdown...")
    shutdown_event.set()


def create_web_app(dbmanager: DatabaseManager, repos: RepositoryContainer) -> FastAPI:
    app = FastAPI(title="HealthPACS Web", version="1.0.0")

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        # Se un'eccezione 401 viene sollevata navigando su una pagina HTML
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            return RedirectResponse(url="/?reason=session_expired", status_code=status.HTTP_302_FOUND)
        
        # Per tutti gli altri errori HTTP restituisce la gestione standard
        from fastapi.exception_handlers import http_exception_handler as default_handler
        return await default_handler(request, exc)

    # Iniezione riferimenti DB e Repository nello stato dell'applicazione
    app.state.dbmanager = dbmanager
    app.state.repos = repos

    # Inizializza il ricevitore Socket.IO della Web App
    init_socket_receiver(dbmanager)

    # 1. Configurazione della cartella STATIC per CSS, JS e risorse grafiche
    base_path = (
        getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        if getattr(sys, "frozen", False)
        else os.path.dirname(os.path.abspath(__file__))
    )
    static_dir = os.path.join(base_path, "static")

    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # 2. Registrazione del router per le pagine HTML (Login e Base)
    app.include_router(pages_router)

    #4. Monta l'app Socket.IO su FastAPI
    app.mount("/socket.io", sio_app)

    return app


def main():
    dbmanager = None
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:       
        logger.info("Inizializzazione HealthPACS Web Server (FastAPI/Uvicorn)...")

        dbmanager = DatabaseManager()
        if not dbmanager.connect():
            logger.critical("Impossibile connettersi al DB per HealthPACS Web. Arresto.")
            return

        repos = RepositoryContainer(dbmanager)
        app = create_web_app(dbmanager, repos)


        host = "0.0.0.0"
        port = 5000 # Deve caricarla da database

        config = uvicorn.Config(app=app, host=host, port=port, log_level=None) # il level_log deve caricarlo da datab
        server = uvicorn.Server(config)

        logger.info(f"Avvio HealthPACS Web Server su http://{host}:{port}")
        
        # Avvio del server Uvicorn
        server.run()

    except Exception as e:
        logger.exception(f"Errore critico durante l'esecuzione di HealthPACS Web: {e}")

    finally:
        if dbmanager:
            logger.info("Chiusura pool DB di HealthPACS Web Server...")
            dbmanager.disconnect()
        logger.info("HealthPACS Web Server arrestato correttamente.")


if __name__ == "__main__":
    main()