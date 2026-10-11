import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from library.constant_health_pacs import (
    APPLICATION_NAME, 
    APPLICATION_NAME_WEB, 
    APPLICATION_NAME_SERVICE, 
    LOG_FILE_NAME
)

# Individuazione cartella log
LOG_DIR = Path('./log')
if not LOG_DIR.exists():
    LOG_DIR = Path('../log')

if not LOG_DIR.exists():
    raise FileNotFoundError("Cartella 'log' non trovata né in './log' né in '../log'")



class HealthPACSLogger:
    """
    Classe incapsulata per la gestione isolata del logger.
    Ogni servizio (Web, Service, ecc.) crea la propria istanza separata.
    """
    def __init__(self, app_name: str, log_filename: str = LOG_FILE_NAME):
        self.app_name = app_name
        self.log_filename = log_filename
        self.log_path = LOG_DIR / log_filename

        # Istanza isolata basata sul nome specifico dell'applicazione
        self._logger = logging.getLogger(self.app_name)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

        self._formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
        )

        # Inizializza gli handler dedicati
        self._setup_handlers()

    def _setup_handlers(self):
        """Pulisce e assegna gli handler specifici per questo logger."""
        # Rimozione vecchi handler per evitare duplicazioni nell'istanza
        for handler in list(self._logger.handlers):
            self._logger.removeHandler(handler)
            handler.close()

        # Handler File
        file_handler = RotatingFileHandler(
            self.log_path,
            maxBytes=2_000_000,
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setFormatter(self._formatter)
        self._logger.addHandler(file_handler)

        # Handler Console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self._formatter)
        self._logger.addHandler(console_handler)

    def get_logger(self) -> logging.Logger:
        """Ritorna l'istanza di logging.Logger nativa configurata."""
        return self._logger
    
class DynamicLoggerProxy:
    """
    Proxy dinamico: quando un qualsiasi file fa 'logger.info(...)', 
    intercetta la chiamata e la gira al logger attivo nel processo corrente.
    """
    def _get_active_logger(self) -> logging.Logger:
        # Se siamo nel processo Web, usa il logger Web
        if APPLICATION_NAME_WEB in logging.Logger.manager.loggerDict:
            return logging.getLogger(APPLICATION_NAME_WEB)
        # Se siamo nel processo Service, usa il logger Service
        elif APPLICATION_NAME_SERVICE in logging.Logger.manager.loggerDict:
            return logging.getLogger(APPLICATION_NAME_SERVICE)
        # Fallback se non ancora inizializzati
        return logging.getLogger(APPLICATION_NAME)

    def __getattr__(self, name):
        # Inoltra le chiamate (.info, .warning, .error, ecc.) al logger del processo attivo
        return getattr(self._get_active_logger(), name)


# Esportiamo l'oggetto 'logger' come Proxy dinamico
logger = DynamicLoggerProxy()


def setup_pynetdicom_logging():
    """
    Collega il logger interno di pynetdicom all'istanza attiva di HealthPACSService.
    """
    pynetdicom_logger = logging.getLogger("pynetdicom")
    pynetdicom_logger.setLevel(logging.DEBUG)
    
    # Rimuove vecchi handler proprietari di pynetdicom per evitare conflitti o duplicati
    for handler in list(pynetdicom_logger.handlers):
        pynetdicom_logger.removeHandler(handler)
        handler.close()

    # Fa propagare i log direttamente verso il logger principale del processo Service
    pynetdicom_logger.propagate = True