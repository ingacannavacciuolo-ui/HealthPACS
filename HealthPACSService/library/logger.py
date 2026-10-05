import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from library.constant_health_pacs import APPLICATION_NAME, LOG_FILE_NAME

# 1. Vedere se la cartella 'log' esiste nella posizione ./log
LOG_DIR = Path('./log')

# 2. Se non esiste, vede nella posizione ../log
if not LOG_DIR.exists():
    LOG_DIR = Path('../log')

# 3. Se non esiste in nessuna delle due, solleva eccezione
if not LOG_DIR.exists():
    raise FileNotFoundError("Cartella 'log' non trovata né in './log' né in '../log'")

# Percorso di default del file di log
LOG_FILE = LOG_DIR / LOG_FILE_NAME

logger = logging.getLogger(APPLICATION_NAME)
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)

'''formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s:%(filename)s:%(lineno)d - %(message)s"
)'''

class CustomDicomLogFilter(logging.Filter):
    """
    Filtro per intercettare i log di pynetdicom e rinominare il logger
    da 'pynetdicom.xyz' ad un tag custom (es. HealthPACS.DICOM).
    """
    def filter(self, record: logging.LogRecord) -> bool:
        if record.name == "pynetdicom" or record.name.startswith("pynetdicom."):
            record.name = APPLICATION_NAME + ".DICOM"
        return True


def setup_logger_file(filename=LOG_FILE_NAME):
    """Cambia o imposta il file di log mantenendo la logica esatta"""
    log_path = LOG_DIR / filename

    for handler in list(logger.handlers):
        if isinstance(handler, RotatingFileHandler):
            logger.removeHandler(handler)
            handler.close()

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

# Istanza globale del filtro
dicom_log_filter = CustomDicomLogFilter()

def setup_pynetdicom_logging():
    """
    Configura il logger interno di pynetdicom indirizzandolo
    verso gli handler centralizzati dell'applicazione con il nome personalizzato.
    """
    pynetdicom_logger = logging.getLogger("pynetdicom")
    pynetdicom_logger.setLevel(logging.DEBUG)

    # Assicura che il filtro sia applicato anche al logger pynetdicom principale
    pynetdicom_logger.addFilter(dicom_log_filter)

    # Evita handler duplicati
    pynetdicom_logger.handlers.clear()

    # Aggancia gli handler del logger principale e applica il filtro direttamente ad essi
    for handler in logger.handlers:
        handler.addFilter(dicom_log_filter)  # <-- FONDAMENTALE: Intercetta il record prima che venga stampato
        pynetdicom_logger.addHandler(handler)

# Setup di default
if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
    setup_logger_file(LOG_FILE_NAME)

if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler) for h in logger.handlers):
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)