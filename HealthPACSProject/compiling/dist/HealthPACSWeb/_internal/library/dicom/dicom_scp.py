

# dicomscp.py
from pydicom.uid import  ImplicitVRLittleEndian, ExplicitVRLittleEndian, ExplicitVRBigEndian
from pynetdicom.presentation import PresentationContext
from library.logger import logger
from library.constant_health_pacs import ROOT_STORAGE
from library.dicom.dicom_utility import *
from library.utility_health_pacs import build_storage_path, ensure_directory_exists, get_file_size_bytes


def handle_association_requested(event, repos):
    """
    Callback eseguita all'arrivo dell'associazione.
    Carica a runtime SOLO le SOP Class e Transfer Syntax abilitate per il client.
    """
    assoc = event.assoc
    requestor = assoc.requestor

    # 1. Pulizia AE Title client
    client_aet = requestor.primitive.calling_ae_title
    if isinstance(client_aet, bytes):
        client_aet = client_aet.decode('utf-8').strip()
    else:
        client_aet = str(client_aet).strip()
        
    client_ip = requestor.address
    logger.info(f"[REQ] Richiesta associazione da AE Title: '{client_aet}' [{client_ip}]")

    # 2. Controllo autorizzazione base IP/AET
    if not repos.dicomscurepo.is_scu_authorized(client_aet, client_ip):
        logger.warning(f"[REQ] Client '{client_aet}' [{client_ip}] NON AUTORIZZATO. Rifiuto connessione.")
        assoc.abort()
        return

    # 3. Recupera dal DB SOLO le SOP Class e Transfer Syntax consentite per QUESTO client
    permissions = repos.scusoptransfersyntaxrepo.get_client_permissions(client_aet)  # Ritorna {sop_uid: [ts_uid1, ts_uid2]}
    if not permissions:
        logger.warning(f"[REQ] Nessuna SOP Class abilitata a DB per il client '{client_aet}'. Rifiuto connessione.")
        assoc.abort()
        return

    # 4. IMPOSTIAMO LE SINTASSI ACCETTATE DALL'ACCEPTOR SULLA SESSIONE CORRENTE
    # Invece di creare oggetti privi di Context ID, associamo gli Abstract Syntaxes 
    # e restringiamo l'acceptor unicamente a quello che c'è nel DB.
    
    # Dichiara all'acceptor quali SOP Class (Abstract Syntaxes) sono valide per questo client
    assoc.acceptor.abstract_syntaxes = list(permissions.keys())
    
    # Costruiamo la lista di PresentationContext validi copiantoli dai requested_contexts 
    # ma mantenendo gli ID e applicando i soli permessi del DB
    dynamic_supported_contexts = []
    
    for req_cx in requestor.requested_contexts:
        sop_uid = str(req_cx.abstract_syntax)
        
        if sop_uid in permissions:
            allowed_ts = [str(ts) for ts in permissions[sop_uid]]
            # Trova la Transfer Syntax concordata
            matched_ts = [ts for ts in req_cx.transfer_syntax if str(ts) in allowed_ts]
            
            if matched_ts:
                # Manteniamo il Context ID originale del client!
                cx = PresentationContext()
                cx.context_id = req_cx.context_id
                cx.abstract_syntax = sop_uid
                cx.transfer_syntax = matched_ts
                dynamic_supported_contexts.append(cx)

    # Ora l'acceptor ha la lista con i Context ID corretti e le sole Transfer Syntax lette dal DB
    assoc.acceptor.supported_contexts = dynamic_supported_contexts

    # 5. LOG DETTAGLIATO
    accepted_count = len(dynamic_supported_contexts)
    for cx in requestor.requested_contexts:
        abstract_syntax = str(cx.abstract_syntax)
        if abstract_syntax in permissions:
            logger.info(f"[REQ] [ACCETTATO] ID: {cx.context_id} | SOP Class: '{abstract_syntax}'")
        else:
            logger.warning(f"[REQ] [RIFIUTATO] ID: {cx.context_id} | SOP Class: '{abstract_syntax}' | Motivo: Non abilitato a DB")

    logger.info(f"[REQ] Negoziazione completata per '{client_aet}'. Contesti autorizzati caricati: {accepted_count}/{len(requestor.requested_contexts)}")

def handle_association_accepted(event,repos):
    """Notifica quando un'associazione viene stabilita con successo."""
    try:
        client_aet = event.assoc.requestor.ae_title
        client_ip = event.assoc.requestor.address

        pdu_client = event.assoc.requestor.maximum_length  # Limite dichiarato dal Client
        pdu_server = event.assoc.acceptor.maximum_length   # Limite del nostro Server

        # Se il client dichiara 0 (illimitato) o un valore maggiore del nostro server,
        # usiamo il limite del server. Altrimenti usiamo il limite del client.
        if pdu_client == 0 or pdu_client > pdu_server:
            pdu_in_uscita = pdu_server
        else:
            pdu_in_uscita = pdu_client

        # Applichiamo la dimensione PDU alla connessione per tutti gli invii futuri
        event.assoc.maximum_pdu_size = pdu_in_uscita
        logger.info(f"[ASSOC] Max PDU Size negoziata: {pdu_in_uscita} bytes")
        logger.info(f"[ASSOC] Connessione accettata da: {client_aet} [{client_ip}]")
    
    except Exception as e:
        logger.error(f"Errore durante la gestione dell'associazione accettata: {e}", exc_info=True)


def handle_association_released(event,repos):
    """Notifica quando un'associazione viene rilasciata regolarmente."""
    client_aet = event.assoc.requestor.ae_title
    logger.info(f"[ASSOC] Connessione rilasciata da: {client_aet}")


def handle_association_aborted(event,repos):
    """Notifica quando un'associazione viene interrotta in modo anomalo."""
    assoc = event.assoc
    
    # Pulizia AE Title client
    client_aet = assoc.requestor.ae_title
    if isinstance(client_aet, bytes):
        client_aet = client_aet.decode('utf-8').strip()
    else:
        client_aet = str(client_aet).strip() if client_aet else "Sconosciuto"

    # Mappe descrittive standard DICOM per l'Abort
    source_map = {
        0: "DICOM UL service-user (Applicazione)",
        2: "DICOM UL service-provider (Livello di rete/trasporto)"
    }
    
    reason_map = {
        0: "Nessun motivo specificato",
        1: "PDU non riconosciuta (Unrecognized PDU)",
        2: "PDU non attesa nello stato attuale (Unexpected PDU)",
        4: "Parametro PDU non riconosciuto (Unrecognized PDU parameter)",
        5: "Parametro PDU inatteso (Unexpected PDU parameter)",
        6: "Parametro PDU non valido (Invalid PDU parameter)"
    }

    # Estrazione dell'errore dalla PDU A-ABORT (se disponibile)
    abort_info = "Motivo non specificato (interruzione improvvisa della socket)"
    
    # Verifichiamo se nell'evento ACSE è presente la PDU di abort
    if hasattr(assoc, 'acse') and hasattr(assoc.acse, 'pdu') and assoc.acse.pdu:
        pdu = assoc.acse.pdu
        # Verifica che sia effettivamente un pacchetto A-ABORT (Tipo 0x07)
        if getattr(pdu, 'pdu_type', None) == 0x07:
            src_val = getattr(pdu, 'abort_source', None)
            rsn_val = getattr(pdu, 'reason_diagnostic', None)
            
            src_str = source_map.get(src_val, f"Sorgente sconosciuta ({src_val})")
            rsn_str = reason_map.get(rsn_val, f"Codice errore ({rsn_val})")
            
            abort_info = f"Origine: '{src_str}' | Dettaglio: '{rsn_str}'"

    logger.warning(f"[ASSOC] Connessione ABORTITA da: '{client_aet}' [{assoc.requestor.address}] | Errore: {abort_info}")


def handle_echo(event,repos):
    """
    Handler per il servizio C-ECHO (Verification SOP Class).
    
    Viene invocato automaticamente ogni volta che un client remoto invia un C-ECHO.
    
    :param event: Oggetto Event fornito da pynetdicom
    :return: Status code DICOM (0x0000 = Success)
    """
    requesting_ae = event.assoc.requestor.ae_title
    requesting_ip = event.assoc.requestor.address
    
    logger.info(f"[C-ECHO] Ricevuta richiesta di Verification da AET: {requesting_ae} ({requesting_ip})")
    
    
    # 0x0000 indica 'Success' nel protocollo DICOM
    return 0x0000

def handle_storage(event, server):
    try:
        # Recuperiamo il dataset inviato dallo SCU
        ds = event.dataset
        ds.file_meta = event.file_meta

        if not server.active_storage_units:
            logger.error("C-STORE: Nessuna unità di archiviazione attiva disponibile.")
            return 0xC000  # Processing Failure

        active_unit = server.active_storage_units[0]
        drive = active_unit.get("drive_unit", "").strip()

        # Estrazione UID fondamentali
        study_uid = getattr(ds, "StudyInstanceUID", None)
        series_uid = getattr(ds, "SeriesInstanceUID", None)
        sop_uid = getattr(ds, "SOPInstanceUID", None)

        if not all([study_uid, series_uid, sop_uid]):
            logger.error("C-STORE: DataSet privo di uno o più UID obbligatori (Study/Series/SOP).")
            return 0xC000  # Tag DICOM obbligatori mancanti

        # -------------------------------------------------------------
        # 0. LIVELLO EQUIPMENT (Check-or-Create)
        # -------------------------------------------------------------
        station_name = str(getattr(ds, "StationName", "")).strip() or None
        manufacturer = str(getattr(ds, "Manufacturer", "")).strip() or None
        institution_name = str(getattr(ds, "InstitutionName", "")).strip() or None
        manufacturer_model_name = str(getattr(ds, "ManufacturerModelName", "")).strip() or None
        device_serial_number = str(getattr(ds, "DeviceSerialNumber", "")).strip() or None
        software_versions = str(getattr(ds, "SoftwareVersions", "")).strip() or None

        equipment_repo = server.repos.dicomequipmentrepo 

        existing_equipment = equipment_repo.find_matching_equipment(
            station_name=station_name,
            manufacturer=manufacturer,
            device_serial_number=device_serial_number
        )

        if not existing_equipment:
            equipment_id = equipment_repo.create(
                station_name=station_name,
                manufacturer=manufacturer,
                institution_name=institution_name,
                manufacturer_model_name=manufacturer_model_name,
                device_serial_number=device_serial_number,
                software_versions=software_versions
            )
        else:
            equipment_id = existing_equipment.get("id")

        # -------------------------------------------------------------
        # 1. LIVELLO STUDIO (public.dicom_studies)
        # -------------------------------------------------------------       

        study_repo = server.repos.dicomstudiesrepo
        existing_study = study_repo.get_by_study_instance_uid(study_uid)

        # -------------------------------------------------------------
        # 1. LIVELLO STUDIO (public.dicom_studies)
        # -------------------------------------------------------------
        if not existing_study:
            study_id = study_repo.create(
                study_instance_uid=study_uid,
                patient_id=clean_dicom_str(getattr(ds, "PatientID", None)),
                patient_name=clean_dicom_str(getattr(ds, "PatientName", None)),
                patient_birth_date=parse_dicom_date(getattr(ds, "PatientBirthDate", None)),
                patient_sex=clean_dicom_str(getattr(ds, "PatientSex", None)),
                study_date=parse_dicom_date(getattr(ds, "StudyDate", None)),
                study_time=parse_dicom_time(getattr(ds, "StudyTime", None)),
                accession_number=clean_dicom_str(getattr(ds, "AccessionNumber", None)),
                study_description=clean_dicom_str(getattr(ds, "StudyDescription", None)),
                referring_physician_name=clean_dicom_str(getattr(ds, "ReferringPhysicianName", None)),
                modalities_in_study=clean_dicom_str(getattr(ds, "Modality", None)),
                study_size=0,
                dicom_equipment_id=equipment_id
            )

            # 2. Controllo esito inserimento DB
            if not study_id:
                logger.error(f"C-STORE: Impossibile registrare lo studio {study_uid} a DB.")
                return 0xC000

            # 3. Creazione directory studio con utility centralizzata
            study_dir = build_storage_path(drive, ROOT_STORAGE, study_uid)
            logger.info(f"C-STORE: Creato nuovo studio [ID: {study_id}, UID: {study_uid}] - Path: {study_dir}")

        else:
            study_id = existing_study.get("id")
            # Garantisce che study_dir sia sempre valorizzato e presente su disco anche se lo studio esisteva già
            study_dir = build_storage_path(drive, ROOT_STORAGE, study_uid)

        # -------------------------------------------------------------
        # 2. LIVELLO SERIE (public.dicom_series)
        # -------------------------------------------------------------
        series_repo = server.repos.dicomseriesrepo
        existing_series = series_repo.get_by_series_instance_uid(series_uid)

        if not existing_series:
            # 1. Inserimento a DB
            series_id = series_repo.create(
                study_id=study_id,
                series_instance_uid=series_uid,
                series_number=getattr(ds, "SeriesNumber", None),
                modality=clean_dicom_str(getattr(ds, "Modality", None)),
                series_description=clean_dicom_str(getattr(ds, "SeriesDescription", None)),
                body_part_examined=clean_dicom_str(getattr(ds, "BodyPartExamined", None)),
                patient_position=clean_dicom_str(getattr(ds, "PatientPosition", None)),
                series_date=parse_dicom_date(getattr(ds, "SeriesDate", None)),
                series_time=parse_dicom_time(getattr(ds, "SeriesTime", None)),
            )

            # 2. Verifica esito scrittura DB
            if not series_id:
                logger.error(f"C-STORE: Impossibile registrare la serie {series_uid} a DB.")
                return 0xC000

            # 3. Creazione directory della Serie tramite utility
            series_dir = ensure_directory_exists(study_dir / series_uid)
            logger.info(f"C-STORE: Creata nuova serie [ID: {series_id}, UID: {series_uid}] - Path: {series_dir}")

        else:
            series_id = existing_series.get("id")
            # Garantisce l'esistenza della directory della serie e la sua assegnazione
            series_dir = ensure_directory_exists(study_dir / series_uid)

        # -------------------------------------------------------------
        # 3. LIVELLO ISTANZA (public.dicom_instances e Scrittura File)
        # -------------------------------------------------------------
        file_path = series_dir / f"{sop_uid}.dcm"

        # 1. Scrittura del file .dcm su filesystem
        ds.save_as(file_path, write_like_original=False)

        # 2. Estrazione dimensione file salvato in bytes
        file_size_bytes = get_file_size_bytes(file_path)

        # 3. Estrazione metadati dell'istanza
        sop_class_uid = str(getattr(ds.file_meta, "MediaStorageSOPClassUID", getattr(ds, "SOPClassUID", "")))
        transfer_syntax_uid = str(getattr(ds.file_meta, "TransferSyntaxUID", ""))
        
        instance_number_raw = getattr(ds, "InstanceNumber", None)
        try:
            instance_number = int(instance_number_raw) if instance_number_raw is not None else None
        except (ValueError, TypeError):
            instance_number = None

        # 4. Registrazione / Aggiornamento Istanza nel DB
        instance_repo = server.repos.dicominstancesrepo
        
        instance_data = {
            "series_id": series_id,
            "sop_instance_uid": sop_uid,
            "sop_class_uid": sop_class_uid,
            "instance_number": instance_number,
            "transfer_syntax_uid": transfer_syntax_uid,
            "file_path": str(file_path),
            "file_size": file_size_bytes
        }

        instance_id = instance_repo.create_or_update(instance_data)

        if not instance_id:
            logger.error(f"C-STORE: Impossibile registrare l'istanza {sop_uid} a DB.")
            return 0xC000  # Processing Failure

        # 5. Aggiornamento dimensione totale dello studio (incrementale)
        if hasattr(study_repo, "update_study_size"):
            study_repo.update_study_size(study_id, file_size_bytes)

        logger.info(
            f"C-STORE: Salvata Istanza [ID: {instance_id}, SOP: {sop_uid}] | "
            f"Dim: {file_size_bytes} B | Path: {file_path}"
        )

        return 0x0000  # Success
    except Exception as e:
        logger.error(f"Errore durante la gestione dello storage: {e}", exc_info=True)
        return 0xC000  # Processing Failure