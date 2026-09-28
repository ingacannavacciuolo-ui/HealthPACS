import configparser
from pathlib import Path
from library.constant_health_pacs import *


class HEALT_PACS_CONFIG:
    
    _config = None
    CONFIG_HEALT_PACS_STORE = {}

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

        cls.CONFIG_HEALT_PACS_STORE[CONFIG_DATABASE_NAME] = fConfig[SECTION_DATABASE][CONFIG_DATABASE_NAME]
        cls.CONFIG_HEALT_PACS_STORE[CONFIG_DATABASE_HOST] = fConfig[SECTION_DATABASE][CONFIG_DATABASE_HOST]
        cls.CONFIG_HEALT_PACS_STORE[CONFIG_DATABASE_PORT] = fConfig[SECTION_DATABASE][CONFIG_DATABASE_PORT]
        cls.CONFIG_HEALT_PACS_STORE[CONFIG_DATABASE_USER] = fConfig[SECTION_DATABASE][CONFIG_DATABASE_USER]
        cls.CONFIG_HEALT_PACS_STORE[CONFIG_DATABASE_PASSWORD] = fConfig[SECTION_DATABASE][CONFIG_DATABASE_PASSWORD]
        
        cls._config = fConfig




    # DATABASE SECTION
    #---------------------------------------------------------------------
    @classmethod
    def get_database_name(cls):
        return cls.CONFIG_HEALT_PACS_STORE[CONFIG_DATABASE_NAME]

    @classmethod
    def get_database_host(cls):
        return cls.CONFIG_HEALT_PACS_STORE[CONFIG_DATABASE_HOST]

    @classmethod
    def get_database_port(cls):
        return cls.CONFIG_HEALT_PACS_STORE[CONFIG_DATABASE_PORT]

    @classmethod
    def get_database_user(cls):
        return cls.CONFIG_HEALT_PACS_STORE[CONFIG_DATABASE_USER]

    @classmethod
    def get_database_password(cls):
        return cls.CONFIG_HEALT_PACS_STORE[CONFIG_DATABASE_PASSWORD]


HEALT_PACS_CONFIG.load_once()  