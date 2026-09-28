import time
from library.logger import logger, setup_logger_file
from library.dicom.dicomserver import DicomServer
from library.dbmanager import DatabaseManager
from library.repository.container import RepositoryContainer
#from library.type_health_pacs import HEALT_PACS_CONFIG

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
        
        # 2. Caricamento automatico di TUTTI i repository presenti nel folder
        repos = RepositoryContainer(dbmanager)        
                
        dicom_server = start_dicom_server(dbmanager, repos)                

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