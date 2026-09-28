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


