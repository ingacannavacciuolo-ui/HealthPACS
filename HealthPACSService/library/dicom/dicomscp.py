

# dicomscp.py
from pydicom.uid import  ImplicitVRLittleEndian, ExplicitVRLittleEndian, ExplicitVRBigEndian
from pynetdicom.presentation import PresentationContext
from library.logger import logger


def handle_association_requested(event, repos):
    """
    Callback eseguita all'arrivo dell'associazione.
    Carica a runtime SOLO le SOP Class e Transfer Syntax abilitate per il client
    e traccia a log l'esito della negoziazione per ciascun contesto.
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

    # 4. Costruiamo dinamicamente i contesti supportati dall'SCP per questa specifica associazione
    dynamic_supported_contexts = []
    
    for sop_uid, ts_list in permissions.items():
        cx = PresentationContext()
        cx.abstract_syntax = sop_uid
        cx.transfer_syntax = ts_list
        dynamic_supported_contexts.append(cx)

    # Impostiamo i contesti supportati sull'acceptor dell'associazione corrente
    assoc.acceptor.supported_contexts = dynamic_supported_contexts

    # 5. LOG DETTAGLIATO E SICURO DELL'ESITO NEGOZIAZIONE
    # Confronta le richieste del client con i permessi autorizzati a DB
    for cx in requestor.requested_contexts:
        abstract_syntax = str(cx.abstract_syntax)
        context_id = cx.context_id

        # Controlla se la SOP Class è presente nei permessi DB per questo client
        if abstract_syntax in permissions:
            allowed_ts = permissions[abstract_syntax]
            # Trova la prima Transfer Syntax richiesta dal client e supportata dal DB
            matched_ts = [ts for ts in cx.transfer_syntax if str(ts) in allowed_ts]
            
            if matched_ts:
                logger.info(
                    f"[REQ] [ACCETTATO] ID: {context_id} | "
                    f"SOP Class: '{abstract_syntax}' | TS: {matched_ts[0]}"
                )
            else:
                logger.warning(
                    f"[REQ] [RIFIUTATO] ID: {context_id} | "
                    f"SOP Class: '{abstract_syntax}' | Motivo: Transfer Syntax non supportata"
                )
        else:
            logger.warning(
                f"[REQ] [RIFIUTATO] ID: {context_id} | "
                f"SOP Class: '{abstract_syntax}' | Motivo: SOP Class non autorizzata a DB"
            )

    logger.info(f"[REQ] Negoziazione completata per '{client_aet}'. Contesti autorizzati caricati: {len(dynamic_supported_contexts)}")



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

def handle_storage(event,repos):
    try:
        # Qui puoi implementare la logica per gestire lo storage dei file DICOM ricevuti
        # Ad esempio, puoi salvare il file in una directory specifica o inviarlo a un database
        logger.info(f"[STORAGE] Ricevuto file DICOM da {event.assoc.requestor.ae_title}")
        # Implementazione dello storage...
    except Exception as e:
        logger.error(f"Errore durante la gestione dello storage: {e}", exc_info=True)