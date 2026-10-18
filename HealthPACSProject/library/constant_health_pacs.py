from enum import Enum

# CONSTANT INI FILE
#*********************************************

NAME_FILE_CONFIG  = 'healthpacsconfig.ini'

SECTION_DATABASE            = 'DATABASE'  
CONFIG_DATABASE_NAME            = 'dbname' 
CONFIG_DATABASE_HOST            = 'host' 
CONFIG_DATABASE_PORT            = 'portdb'
CONFIG_DATABASE_USER            = 'user' 
CONFIG_DATABASE_PASSWORD        = 'password'


SECTION_SYSTEM                  = 'SYSTEM'
SYSTEM_LANGUAGE                 = 'language'
#*********************************************

#COSTANTI ARCHIVIAZIONE
#**********************************************
ROOT_STORAGE = 'ArchiveRoot'  # Nome radice archivio DICOM


#COSTANTI INTERNE
#**********************************************
APPLICATION_NAME = 'HealthPACS'
LOG_FILE_NAME = 'healtpacs.log'
LOG_FILE_NAME_SERVICE = 'healthpacs_service.log'  # Nome del file di log
LOG_FILE_NAME_WEB = 'healthpacs_web.log'  # Nome del file di log
APPLICATION_NAME_WEB = 'HealthPACSWeb'
APPLICATION_NAME_SERVICE = 'HealthPACSService'
HEALT_PACS_WEB_URL_DEFAULT = "http://localhost:7500"
HEALT_PACS_WEB_FIRST_PAGE_DEFAULT = "/querystudies"
#**********************************************




# COSTANTI SYSTEM SETTING KEY
# Sono costanti usate per la configurazione del 
# sistema e devono essere tutte upercase perché
# coincidenti con la tabella "app_system_setting"
#*********************************************
class SYSTEM_SETTING_KEY(str,Enum):
    SESSION_DURATION_MINUTES = 'SESSION_DURATION_MINUTES'
    SERVICE_INTERNAL_AUTH_TOKEN = 'SERVICE_INTERNAL_AUTH_TOKEN'
    WEB_SOCKET_URL = 'WEB_SOCKET_URL'
    WEB_FIRST_PAGE = 'WEB_FIRST_PAGE'
#WEB_SOCKET_NAMESPACE = "WEB_SOCKET_NAMESPACE"
#DEFAULT_WEB_SOCKET_NAMESPACE = "/web"


# COSTANTI MESSAGE SERVICE SOCKET
# Sono le costanti che indicano il tipo di messaggio
# che deve essere inviato a livello socket 
class MSG_SERVICE_SOCKET_TYPE(str, Enum):
    MSG_SERVICE_STATUS = 'service_status'
    MSG_SERVICE_SEVERITY = 'service_severity'

# COSTANTI DI STATO - Constanti usate per gestire
# lo stato di un oggetto o di un'attività
#*********************************************
class SERVICE_STATUS_STATES(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    READY = "ready"
    SCANNING = "scanning"
    COMPLETED = "completed"
    STANDBY = "standby"
    FAILED = "failed"

# COSTANTI DI STATO - Constanti usate per gestire
# lo stato di visualizzazione di un oggetto o di un'attività
class SERVICE_STATUS_STATES_VIEW(str,Enum):
    CONNECT = "connesso"
    DISCONNECT = "disconnesso"


#COSTANTI SOCKET EVENTS - Costanti gestiste
# nella connessione socket tra il client_service_socket
# ed il web_receiver_socket
#********************************************
class SOCKET_EVENTS(str, Enum):
    SERVICE_STATUS_UPDATE = "service_status_update"
    SERVER_ALIVE = "server_alive"


# COSTANTI NAMESPACE
#*****************************************
class SOCKET_NAMESPACES(str, Enum):
    WEB = "/socket_web"
    LOGIN = "/socket_login_web"
    SISTEMA = "/socket_sistema_web"
    WORKS_STUDIES = "/socket_worksstudies_web"
    NODI_DICOM = "/socket_nodidicom_web"
    SERVER_DICOM = "/socket_serverdicom_web"
    LOG_SISTEMA = "/socket_log_sistema_web"
    USERS = "/socket_users_web"
    QUERY_STUDIES = "/socket_query_studies_web"
    QUERY_FOLDER_STUDIES = "/socket_queryfolderstudies_web"
    WORKS_STUDIES_FOLDER = "/socket_worksstudiesfolder_web"



# COSTANTI NOTIFY KEY - USATE NELLA GESTIONE DELLE
# NOTIFICHE da HeakthPACSService ed HealtPacsWeb
# Sono le chiavi per gli alert che vengono sollevati
# presenti nella tabella "app_notification_worker"
# Sono uppercase, perché
# coincidenti con la tabella "app_notification_worker"
#****************************************
class NOTIFY_KEY(str,Enum):
    STORAGE_WARNING = "STORAGE_WARNING",
    STORAGE_CRITICAL = "STORAGE_CRITICAL",
    MEMORY_LIMIT_WARNING = "MEMORY_LIMIT_WARNING"
    SYSTEM_MAINTENANCE = "SYSTEM_MAINTENANCE"
    UNKNOWN_KEY = "UNKNOWN_KEY",
    


#COSTANTI NOTIFY TYPE - USATE NELLA GESTIONE DELLE
# NOTIFICHE da HeakthPACSService ed HealtPacsWeb
# Sono i tipi di notifiche per gli alert che 
# vengono sollevati - presenti nella tabella 
# "app_notification_worker"
# Sono uppercase, perché
# coincidenti con la tabella "app_notification_worker"
#****************************************
class NOTIFY_TYPE(str, Enum):
    SYSTEM_ALERT = "SYSTEM_ALERT"
    DICOM_JOB_STATUS = "DICOM_JOB_STATUS"
    WORKLIST_SYNC = "WORKLIST_SYNC"


#COSTANTI SEVERITY - USATE NELLA GESTIONE DELLE
# NOTIFICHE da HeakthPACSService ed HealtPacsWeb
# Indicano il tipo di severità degli alert che 
# vengono sollevati - presenti nella tabella 
# "app_notification_worker"
# Sono uppercase, perché
# coincidenti con la tabella "app_notification_worker"
#************************************
class NOTIFY_SEVERITY(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    GENERIC = "GENERIC"


# COSTANTI DI ERRORI - Costanti usate per la notifica
# di errori in fasi di sessione scaduta, token non
# presente ect.
#********************************************
class NOTIFY_ERROR(str, Enum):
    """Costanti per la gestione degli errori e notifiche di sessione/autenticazione."""
    MISSING_TOKEN = "missing_token"
    SESSION_EXPIRED = "session_expired"
    LOGIN_BAD_CREDENTIALS = "login_bad_credentials"
    LOGIN_UNAUTHORIZED = "login_unauthorized"
    SESSION_CREATE_ERROR = "sessione_create_error"


class LANG_KEY(str, Enum):
    APP_TITLE = "KEY_LANG_APP_TITLE"

    LOGIN_TITLE = "KEY_LANG_LOGIN_TITLE"
    LOGIN_HEADER = "KEY_LANG_LOGIN_HEADER"
    USERNAME_LABEL = "KEY_LANG_USERNAME_LABEL"
    PASSWORD_LABEL = "KEY_LANG_PASSWORD_LABEL"
    LOGIN_BUTTON = "KEY_LANG_LOGIN_BUTTON"
    ALERT_MISSING_TOKEN = "KEY_LANG_ALERT_MISSING_TOKEN"
    ALERT_SESSION_EXPIRED = "KEY_LANG_ALERT_SESSION_EXPIRED"
    ALERT_BAD_CREDENTIALS = "KEY_LANG_ALERT_BAD_CREDENTIALS"
    ALERT_UNAUTHORIZED = "KEY_LANG_ALERT_UNAUTHORIZED"

    STATUS_LABEL = "KEY_LANG_STATUS_LABEL"
    STATUS_CONNECTED = "KEY_LANG_STATUS_CONNECTED"
    STATUS_DISCONNECTED = "KEY_LANG_STATUS_DISCONNECTED"

    SERVICE_ALIVE = "KEY_LANG_SERVICE_ALIVE"
    SERVICE_OFFLINE = "KEY_LANG_SERVICE_OFFLINE"
    SERVICE_STATUS_CURRENT_MSG = "KEY_LANG_SERVICE_STATUS_CURRENT_MSG"
    NO_DETAILS_PROVIDED = "KEY_LANG_NO_DETAILS_PROVIDED"

    WELCOME_USER = "KEY_LANG_WELCOME_USER"
    LOGGED_USER = "KEY_LANG_LOGGED_USER"
    LOGOUT = "KEY_LANG_LOGOUT"
    LOAD_STUDIES = "KEY_LANG_LOAD_STUDIES"
    STUDIES_LOADED_SUCCESS = "KEY_LANG_STUDIES_LOADED_SUCCESS"
    SEARCH_COMPLETED = "KEY_LANG_SEARCH_COMPLETED"
    SERVER_CONNECTION_ERROR = "KEY_LANG_SERVER_CONNECTION_ERROR"

    LOGIN_CARD_HEADER = "KEY_LANG_LOGIN_CARD_HEADER"
    USERNAME_PLACEHOLDER = "KEY_LANG_USERNAME_PLACEHOLDER"
    PASSWORD_PLACEHOLDER = "KEY_LANG_PASSWORD_PLACEHOLDER"
    SHOW_HIDE_PASSWORD = "KEY_LANG_SHOW_HIDE_PASSWORD"
    FORGOT_PASSWORD = "KEY_LANG_FORGOT_PASSWORD"
    ALERT_CONTACT_ADMIN = "KEY_LANG_ALERT_CONTACT_ADMIN"


# Puoi anche creare una lista contenente tutte le classi Enum del progetto
ALL_ENUMS_CLASS = [
    LANG_KEY,
    SYSTEM_SETTING_KEY,
    MSG_SERVICE_SOCKET_TYPE,
    SOCKET_NAMESPACES,
    SOCKET_EVENTS,
    SERVICE_STATUS_STATES,  
    NOTIFY_ERROR,
    NOTIFY_KEY,
    NOTIFY_TYPE,
    NOTIFY_SEVERITY,
    SERVICE_STATUS_STATES_VIEW,
]

# Usiamo il dizionario {} con la coppia "NOME_VAR": Oggetto
ALL_ENUMS_DICT = {
        
}



#CONSTANTI AMBIENTE DICOM 
#*********************************************
HEALT_PACS_ID_APPLICATION = '1.1'

IMPLEMENTATION_CLASS_UID = "1.3.6.1.4.1.57025." + HEALT_PACS_ID_APPLICATION  # OID univoco per HealthPACS
IMPLEMENTATION_VERSION_NAME = "HEALTH PACS 1.0"  # Max 16 caratteri

ECHO_CLASS = 'ECHO'  # Nome della SOP Class per l'echo dei messaggi DICOM
STORAGE_CLASS = 'STORAGE'  # Nome della SOP Class per lo storage dei file DICOM
FIND_CLASS = 'FIND'  # Nome della SOP Class per la ricerca dei file DICOM
MOVE_CLASS = 'MOVE'  # Nome della SOP Class per lo spostamento dei file DICOM
GET_CLASS = 'GET'  # Nome della SOP Class per il recupero dei file DICOM
WORKLIST_CLASS = 'WORKLIST'  # Nome della SOP Class per la gestione delle liste di lavoro
PRINT_CLASS = 'PRINT'  # Nome della SOP Class per la stampa dei file DICOM


