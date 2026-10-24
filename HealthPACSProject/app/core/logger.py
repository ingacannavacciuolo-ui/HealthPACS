import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Union
from app.core.constants import (
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

''' LEVEL LOG
DEBUG (10)

INFO (20)

WARNING (30)

ERROR (40)

CRITICAL (50)'''

class SystemLogger:
    """
    Classe incapsulata per la gestione isolata del logger.
    Ogni servizio (Web, Service, ecc.) crea la propria istanza separata.
    """
    def __init__(self, 
                 app_name: str,
                 log_filename: str = LOG_FILE_NAME,
                 enabled: bool = True,
                 log_level: Union[str, int] = "INFO"
                 ):
        
        self.app_name = app_name
        self.log_filename = log_filename
        self.log_path = LOG_DIR / log_filename
        self.enabled = enabled
        self.log_level = self._parse_level(log_level)

        # Istanza isolata basata sul nome specifico dell'applicazione
        self._logger = logging.getLogger(self.app_name)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

        self._formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
        )
        
       # Applica subito la configurazione riutilizzando i metodi dedicati
        self.set_enabled(self.enabled)
        if self.enabled:
            self.set_level(self.log_level)

    def _parse_level(self, level: Union[str, int]) -> int:
        """Converte una stringa di livello (es. 'DEBUG', 'INFO') nel relativo livello di logging nativo."""
        if isinstance(level, str):
            return getattr(logging, level.upper(), logging.INFO)
        return level
    
    def _disable_logger(self):
        """Disabilita l'invio dei log rimuovendo gli handler e aggiungendo un NullHandler."""
        for handler in list(self._logger.handlers):
            self._logger.removeHandler(handler)
            handler.close()
        self._logger.addHandler(logging.NullHandler())

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

    def set_enabled(self, enabled: bool):
        """Consente di abilitare o disabilitare il logger a runtime."""
        self.enabled = enabled
        self._logger.disabled = not enabled
        if enabled:
            self._setup_handlers()
        else:
            self._disable_logger()

    def set_level(self, level: Union[str, int]):
        """Consente di cambiare il livello del log a runtime."""
        self.log_level = self._parse_level(level)
        self._logger.setLevel(self.log_level)
        if self.enabled:
            self._setup_handlers()

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


def setup_pynetdicom_logging(level: Union[str, int] = "DEBUG"):
    """
    Collega il logger interno di pynetdicom all'istanza attiva di HealthPACSService.
    """
    pynetdicom_logger = logging.getLogger("pynetdicom")
    parsed_level = getattr(logging, level.upper(), logging.DEBUG) if isinstance(level, str) else level
    pynetdicom_logger.setLevel(parsed_level)
    
    for handler in list(pynetdicom_logger.handlers):
        pynetdicom_logger.removeHandler(handler)
        handler.close()

    pynetdicom_logger.propagate = True