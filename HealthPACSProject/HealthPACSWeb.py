import os
import sys
import signal
import threading
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from library.dbmanager import DatabaseManager
from library.logger import logger, setup_logger_file
from library.repository.container import RepositoryContainer
from library.api.web.pages_router import router as pages_router

shutdown_event = threading.Event()


def signal_handler(signum, frame):
    sig_name = signal.Signals(signum).name
    logger.info(f"[WEB] Ricevuto segnale di arresto ({sig_name}). Avvio shutdown...")
    shutdown_event.set()


def create_web_app(dbmanager: DatabaseManager, repos: RepositoryContainer) -> FastAPI:
    app = FastAPI(title="HealthPACS Web", version="1.0.0")

    # Iniezione riferimenti DB e Repository nello stato dell'applicazione
    app.state.dbmanager = dbmanager
    app.state.repos = repos

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

    # 3. Gestore WebSocket per la comunicazione in tempo reale dell'interfaccia web
    @app.websocket("/ws/web")
    async def websocket_web(websocket: WebSocket):
        await websocket.accept()
        logger.info("[WEB WS] Client connesso a HealthPACS Web")
        try:
            while True:
                data = await websocket.receive_text()
                await websocket.send_json({"status": "ok", "echo": data})
        except WebSocketDisconnect:
            logger.info("[WEB WS] Client disconnesso da HealthPACS Web")

    return app


def main():
    dbmanager = None
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        setup_logger_file("healthpacs_web.log")
        logger.info("Inizializzazione HealthPACS Web Server (FastAPI/Uvicorn)...")

        dbmanager = DatabaseManager()
        if not dbmanager.connect():
            logger.critical("Impossibile connettersi al DB per HealthPACS Web. Arresto.")
            return

        repos = RepositoryContainer(dbmanager)
        app = create_web_app(dbmanager, repos)

        host = "0.0.0.0"
        port = 5000

        config = uvicorn.Config(app=app, host=host, port=port, log_level="info")
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