# library/languages/i18n/__init__.py

import os
import sys
import json
import logging
from app.core.types import HEALTH_PACS_CONFIG

logger = logging.getLogger(__name__)

# Determinazione del percorso della cartella i18n (compatibile con PyInstaller e modalità sviluppo)
if getattr(sys, 'frozen', False):
    I18N_DIR = os.path.join(sys._MEIPASS, "library", "languages", "i18n")
else:
    I18N_DIR = os.path.dirname(os.path.abspath(__file__))

TRANSLATIONS = {}
DEFAULT_LANG = HEALTH_PACS_CONFIG.get_system_language()


def load_translations():
    """Scansiona la cartella i18n e carica dinamicamente tutti i file .json trovati."""
    global TRANSLATIONS
    TRANSLATIONS.clear()

    if not os.path.exists(I18N_DIR):
        logger.warning(f"[i18n] Cartella traduzioni non trovata in: {I18N_DIR}")
        return

    for file_name in os.listdir(I18N_DIR):
        if file_name.endswith(".json"):
            lang_code = os.path.splitext(file_name)[0].lower()
            file_path = os.path.join(I18N_DIR, file_name)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    TRANSLATIONS[lang_code] = json.load(f)
                logger.info(f"[i18n] Caricata lingua '{lang_code}' da {file_name}")
            except Exception as e:
                logger.error(f"[i18n] Errore caricamento {file_name}: {e}")


# Caricamento automatico all'importazione del modulo
load_translations()


def translate(key: str, lang: str = DEFAULT_LANG) -> str:
    """Restituisce il testo tradotto per la chiave fornita. Se non esiste, ritorna la chiave stessa."""
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS.get(DEFAULT_LANG, {}))
    return lang_dict.get(key, key)


# Alias breve ampiamente riconosciuto
_ = translate