# CONSTANT INI FILE
#*********************************************

NAME_FILE_CONFIG  = 'healthpacsconfig.ini'


SECTION_DATABASE            = 'DATABASE'  

CONFIG_DATABASE_NAME            = 'dbname' 
CONFIG_DATABASE_HOST            = 'host' 
CONFIG_DATABASE_PORT            = 'portdb'
CONFIG_DATABASE_USER            = 'user' 
CONFIG_DATABASE_PASSWORD        = 'password'
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

SERVICE_STATUS = 'SERVICE_STATUS'
LOGIN_SESSION_TIMEOUT = 'LOGIN_SESSION_TIMEOUT'
LOGIN_UNAUTHORIZED = 'LOGIN_UNAUTHORIZED'
SERVICE_STATUS_UPDATE = 'service_status_update'

HEALT_PACS_WEB_URL_DEFAULT = "http://localhost:5000"


#COSTANTI DI STATO
#****************************************
SERVICE_STATUS_STATES = {
    "ONLINE": 'ONLINE',
    "OFFLINE": 'OFFLINE'
}

#COSTANTI SOCKET EVENTS
#********************************************
SOCKET_EVENTS = {
    "SERVICE_STATUS_UPDATE": "service_status_update",
    "SERVER_ALIVE": "server_alive"
}


#COSTANTI SYSTEM SETTING KEY
#*********************************************
SESSION_DURATION_MINUTES = 'SESSION_DURATION_MINUTES'
SERVICE_INTERNAL_AUTH_TOKEN = 'SERVICE_INTERNAL_AUTH_TOKEN'
WEB_SOCKET_URL = 'WEB_SOCKET_URL'
WEB_SOCKET_NAMESPACE = "WEB_SOCKET_NAMESPACE"
DEFAULT_WEB_SOCKET_NAMESPACE = "/web"


#COSTANTI NOTIFY KEY
#****************************************
NOTIFY_KEY = {
    "STORAGE_WARNING": "STORAGE_WARNING",
    "STORAGE_CRITICAL": "STORAGE_CRITICAL",
    "MEMORY_LIMIT_WARNING": "MEMORY_LIMIT_WARNING"
}

#COSTANTI NOTIFY TYPE
#****************************************
NOTIFY_TYPE = {
    "SYSTEM_ALERT": "SYSTEM_ALERT",
    "DICOM_JOB_STATUS": "DICOM_JOB_STATUS",
    "WORKLIST_SYNC": "WORKLIST_SYNC"
}

#COSTANTI SEVERITY
#************************************
SEVERITY = {
    "INFO": "INFO",
    "WARNING": "WARNING",
    "CRITICAL": "CRITICAL"
}

# COSTANTI NAMESPACE
#*****************************************
SOCKET_NAMESPACES = {
    "WEB": "/socket_web",
    "LOGIN": "/socket_login_web",
    "SISTEMA": "/socket_sistema_web",
    "WORKS_STUDIES": "/socket_worksstudies_web",
    "NODI_DICOM": "/socket_nodidicom_web",
    "SERVER_DICOM": "/socket_serverdicom_web",
    "LOG_SISTEMA": "/socket_log_sistema_web",
    "USERS": "/socket_users_web",
    "QUERY_STUDIES": "/socket_query_studies_web",
    "QUERY_FOLDER_STUDIES": "/socket_queryfolderstudies_web",
    "WORKS_STUDIES_FOLDER": "/socket_worksstudiesfolder_web"
}


#CONSTANTS DICOM
#*********************************************
HEALT_PACS_ID_APPLICATION = '1.1'

IMPLEMENTATION_CLASS_UID = "1.3.6.1.4.1.57025."+ HEALT_PACS_ID_APPLICATION  # OID univoco per HealthPACS
IMPLEMENTATION_VERSION_NAME = "HEALTH PACS 1.0"  # Max 16 caratteri

ECHO_CLASS = 'ECHO'  # Nome della SOP Class per l'echo dei messaggi DICOM
STORAGE_CLASS = 'STORAGE'  # Nome della SOP Class per lo storage dei file DICOM
FIND_CLASS = 'FIND'  # Nome della SOP Class per la ricerca dei file DICOM
MOVE_CLASS = 'MOVE'  # Nome della SOP Class per lo spostamento dei file DICOM
GET_CLASS = 'GET'  # Nome della SOP Class per il recupero dei file DICOM
WORKLIST_CLASS = 'WORKLIST'  # Nome della SOP Class per la gestione delle liste di lavoro
PRINT_CLASS = 'PRINT'  # Nome della SOP Class per la stampa dei file DICOM


