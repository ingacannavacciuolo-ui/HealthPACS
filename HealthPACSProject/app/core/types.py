import configparser
from pathlib import Path
from app.core.constants import *
#from app.repository import AppSystemSettingsRepo


class HEALTH_PACS_CONFIG:
    
    _config = None
    CONFIG_HEALTH_PACS_STORE = {}

    @classmethod
    def load_once(cls):
        if cls._config is not None:
            return

        # 1. Verifica la posizione ./config.ini
        path = Path('./' + NAME_FILE_CONFIG)
        
        # 2. Se non esiste, verifica la posizione ../config.ini
        if not path.exists():
            path = Path('../' + NAME_FILE_CONFIG)

        # 3. Se non esiste in nessuna delle due, solleva eccezione
        if not path.exists():
            raise FileNotFoundError(f"File di configurazione '{NAME_FILE_CONFIG}' non trovato né in './' né in '../'")

        # Carica il file
        fConfig = configparser.ConfigParser()
        fConfig.read(path, encoding='utf-8')

        # Popola il dizionario      
        cls.CONFIG_HEALTH_PACS_STORE[SYSTEM_LANGUAGE] = fConfig[SECTION_SYSTEM][SYSTEM_LANGUAGE]
        cls.CONFIG_HEALTH_PACS_STORE[SYSTEM_LOG_ENABLED] = fConfig[SECTION_SYSTEM][SYSTEM_LOG_ENABLED]
        cls.CONFIG_HEALTH_PACS_STORE[SYSTEM_LOG_LEVEL] = fConfig[SECTION_SYSTEM][SYSTEM_LOG_LEVEL]

        cls.CONFIG_HEALTH_PACS_STORE[CONFIG_DATABASE_NAME] = fConfig[SECTION_DATABASE][CONFIG_DATABASE_NAME]
        cls.CONFIG_HEALTH_PACS_STORE[CONFIG_DATABASE_HOST] = fConfig[SECTION_DATABASE][CONFIG_DATABASE_HOST]
        cls.CONFIG_HEALTH_PACS_STORE[CONFIG_DATABASE_PORT] = fConfig[SECTION_DATABASE][CONFIG_DATABASE_PORT]
        cls.CONFIG_HEALTH_PACS_STORE[CONFIG_DATABASE_USER] = fConfig[SECTION_DATABASE][CONFIG_DATABASE_USER]
        cls.CONFIG_HEALTH_PACS_STORE[CONFIG_DATABASE_PASSWORD] = fConfig[SECTION_DATABASE][CONFIG_DATABASE_PASSWORD]
        
        cls._config = fConfig        


    # SYSTEM SECTION
    #---------------------------------------------------------------------
    @classmethod
    def get_system_language(cls):
        return cls.CONFIG_HEALTH_PACS_STORE[SYSTEM_LANGUAGE]
    
    @classmethod
    def get_system_log_enabled(cls):
        # 1. Recupera il valore usando .get() per evitare KeyError se la chiave manca
        val = cls.CONFIG_HEALTH_PACS_STORE.get(SYSTEM_LOG_ENABLED, False)

        # 2. Gestione se è già un booleano
        if isinstance(val, bool):
            return val

        # 3. Gestione se è una stringa (es. "True", "true", "1", "yes", "DISABLE", ecc.)
        if isinstance(val, str):
            val_clean = val.strip().lower()
            if val_clean in ("true", "1", "yes", "on", "enable", "enabled"):
                return True
            if val_clean in ("false", "0", "no", "off", "disable", "disabled", "none"):
                return False

        # 4. Gestione se è un intero (es. 1 o 0)
        if isinstance(val, int):
            return bool(val)

        # Fallback di sicurezza in caso di None o tipi non previsti
        return False
    
    @classmethod
    def get_system_log_level(cls) -> str:
        # 1. Recupera il valore con .get() per evitare KeyError se la chiave manca
        val = cls.CONFIG_HEALTH_PACS_STORE.get(SYSTEM_LOG_LEVEL, "INFO")

        # 2. Se è None o non è una stringa/intero, fallback a "INFO"
        if val is None or not isinstance(val, (str, int)):
            return "INFO"

        # 3. Normalizzazione se stringa
        if isinstance(val, str):
            val_str = val.strip().upper()

            # Valori validi di logging Python
            valid_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
            if val_str in valid_levels:
                return val_str

            # Gestione valori espliciti di disattivazione
            if val_str in ("DISABLE", "OFF", "NONE", "FALSE"):
                return "DISABLE"

        # 4. Se intero (es. 10, 20, 30, 40, 50)
        if isinstance(val, int):
            level_map = {10: "DEBUG", 20: "INFO", 30: "WARNING", 40: "ERROR", 50: "CRITICAL"}
            return level_map.get(val, "INFO")

        # Fallback di sicurezza
        return "INFO"

    # DATABASE SECTION
    #---------------------------------------------------------------------
    @classmethod
    def get_database_name(cls):
        return cls.CONFIG_HEALTH_PACS_STORE[CONFIG_DATABASE_NAME]

    @classmethod
    def get_database_host(cls):
        return cls.CONFIG_HEALTH_PACS_STORE[CONFIG_DATABASE_HOST]

    @classmethod
    def get_database_port(cls):
        return cls.CONFIG_HEALTH_PACS_STORE[CONFIG_DATABASE_PORT]

    @classmethod
    def get_database_user(cls):
        return cls.CONFIG_HEALTH_PACS_STORE[CONFIG_DATABASE_USER]

    @classmethod
    def get_database_password(cls):
        return cls.CONFIG_HEALTH_PACS_STORE[CONFIG_DATABASE_PASSWORD]
    



HEALTH_PACS_CONFIG.load_once()  