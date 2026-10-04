from library.models import Base
import time
import threading
import uvicorn
from fastapi import FastAPI

from library.logger import logger, setup_logger_file
from library.dicom.dicom_server import DicomServer
from library.dbmanager import DatabaseManager
from library.repository.container import RepositoryContainer

# Import dei router di trasporto REST e WebSocket allegati
from library.api.rest.dicom_studies_rest import router as studies_rest_router
from library.api.socket.dicom_studies_socket import router as studies_socket_router
#from library.type_health_pacs import HEALT_PACS_CONFIG

# Instanziazione dell'applicazione FastAPI
app = FastAPI(
    title="HealthPACS VNA / DICOM Backend",
    version="1.0.0",
    description="Backend DICOM con supporto REST, WebSocket e C-STORE/C-FIND."
)

# Registrazione dei router
app.include_router(studies_rest_router)
app.include_router(studies_socket_router)


@app.get("/")
def health_check():
    return {"status": "online", "system": "HealthPACS Backend"}


def start_api_server(host: str = "0.0.0.0", port: int = 8000):
    """Avvia il server Uvicorn/FastAPI in background su un thread separato."""
    config = uvicorn.Config(app=app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    logger.info(f"API Server (REST/WebSocket) avviato su http://{host}:{port}")
    return server


def start_dicom_server(dbmanager,repos):
    try:
        # -------------------------------------------------------------
        # 2. ISTANZA  E AVVIO DICOM SERVER (SCP)
        # -------------------------------------------------------------
        logger.info("Avvio Server HealthPACS...") 
        
        dicom_server = DicomServer(            
            dbmanager= dbmanager,
            repos=repos
        )
        # Avvio diretto: block=False non blocca e gestisce i client in multithread nativo
        dicom_server.start()
        return dicom_server                

    except Exception as e:
        logger.error(f"Errore durante l'avvio del DICOM Server: {e}", exc_info=True)
        raise e


def main():
    dicom_server = None
    dbmanager = None
    
    try:            

        setup_logger_file("healthpacs.log")
        logger.info("Avvio di HealthPACS...")

        dbmanager = DatabaseManager()
        if not dbmanager.connect():
            logger.error("Impossibile connettersi al database. Arresto dell'applicazione.")
            return
        
        # <-- AGGIUNGI QUESTA RIGA PER INIZIALIZZARE IL REGISTRO MODELLI SUL DB -->
        Base.metadata.create_all(bind=dbmanager.engine)
        
        # Salviamo il dbmanager direttamente dentro l'app FastAPI
        app.state.dbmanager = dbmanager

        # 2. Caricamento automatico di TUTTI i repository (REPO) presenti nel folder
        repos = RepositoryContainer(dbmanager)        
                
        dicom_server = start_dicom_server(dbmanager, repos) 

        # 2. Avvio del Server Web (REST API / WebSocket)
        # Prendere la porta da file di configurazione o database.
        # start_api_server(host="0.0.0.0", port=8000)               

        logger.info("HealthPACS avviato con successo. In attesa di connessioni...")    
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        # Quando l'utente preme CTRL+C, entriamo qui
        logger.info("Rilevato CTRL+C. Avvio procedura di chiusura pulita...")

    except Exception as e:
        logger.exception(f"Errore critico all'avvio di HealthPACS: {e}")

    finally:
        
        # 5. BLOCCO FINALLY: garantisce la pulizia delle risorse in qualsiasi scenario
        if dicom_server:
            logger.info("Arresto del Server DICOM...")
            dicom_server.stop()

        if dbmanager:
            logger.info("Chiusura del Pool di Connessioni DB...")
            dbmanager.disconnect()

        logger.info("Applicazione chiusa correttamente.")


if __name__ == "__main__":
    main()