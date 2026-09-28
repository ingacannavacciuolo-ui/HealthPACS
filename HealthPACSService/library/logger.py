import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# 1. Vedere se la cartella 'log' esiste nella posizione ./log
LOG_DIR = Path('./log')

# 2. Se non esiste, vede nella posizione ../log
if not LOG_DIR.exists():
    LOG_DIR = Path('../log')

# 3. Se non esiste in nessuna delle due, solleva eccezione
if not LOG_DIR.exists():
    raise FileNotFoundError("Cartella 'log' non trovata né in './log' né in '../log'")

# Percorso di default del file di log
LOG_FILE = LOG_DIR / "healthpacs.log"

logger = logging.getLogger("HealthPACS")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)

'''formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s:%(filename)s:%(lineno)d - %(message)s"
)'''

def setup_logger_file(filename="healthpacs.log"):
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

# Setup di default
if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
    setup_logger_file("healthpacs.log")

if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler) for h in logger.handlers):
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)