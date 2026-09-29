# dicomserver.py
import time
from pathlib import Path
from pynetdicom import AE, evt
from pynetdicom.sop_class import Verification
from pydicom.uid import ImplicitVRLittleEndian, ExplicitVRLittleEndian, ExplicitVRBigEndian
from library.constant_health_pacs import IMPLEMENTATION_CLASS_UID, IMPLEMENTATION_VERSION_NAME, ROOT_STORAGE
from library.logger import logger
from library.dicom.dicomscp import (
    handle_echo,
    handle_storage,
    handle_association_requested,
    handle_association_accepted,
    handle_association_released,
    handle_association_aborted
)


class DicomServer:
    def __init__(self, dbmanager=None, repos=None):
        """
        Inizializza il server DICOM.
        
        :param dbmanager: Gestore della base di dati (facoltativo/legacy)
        :param repos: RepositoryContainer per l'accesso ai dati
        """
        self.dbmanager = dbmanager
        self.repos = repos
        self.server = None
        self.active_storage_units = []

        try:
            if self.repos and hasattr(self.repos, "dicomscprepo"):
                self.config_scp = self.repos.dicomscprepo.get_config_scp()
            else:
                raise RuntimeError("Nessun gestore/repository disponibile per il recupero di 'config_scp'.")

            if not self.config_scp:
                raise ValueError("Configurazione SCP (dicom_scp) vuota o non trovata nel database.")

            # Inizializzazione e verifica delle unità di archiviazione
            self._init_storage_units()

            # Configurazione del server DICOM (Application Entity e parametri di rete)
            self._setup_dicom_server()

            # Sintassi di Trasferimento di Default (Native / Uncompressed)
            self._setup_default_transfer_syntaxes()

            # Registrazione del solo contesto C-ECHO (Verification)
            self._setup_default_presentation_contexts()

            # Mappatura Handler Eventi
            self.handlers = [
                (evt.EVT_C_ECHO, handle_echo, [self.repos]),
                (evt.EVT_C_STORE, handle_storage, [self]),
                (evt.EVT_REQUESTED, handle_association_requested, [self.repos]),
                (evt.EVT_ACCEPTED, handle_association_accepted, [self.repos]),
                (evt.EVT_RELEASED, handle_association_released, [self.repos]),
                (evt.EVT_ABORTED, handle_association_aborted, [self.repos]),
            ]

        except Exception as e:
            logger.critical(f"DicomServer: Errore fatale durante l'inizializzazione: {e}", exc_info=True)
            self.stop()
            raise e

    def _init_storage_units(self):
        """
        Recupera le unità di archiviazione attive dal DB e verifica/crea
        la directory radice ROOT_STORAGE per ogni unità abilitata.
        """
        if not self.repos:
            raise RuntimeError("RepositoryContainer non fornito a DicomServer.")

        try:
            storage_repo = self.repos.storageunitsrepo
        except (AttributeError, KeyError) as e:
            raise RuntimeError(f"Impossibile accedere a 'storageunitsrepo' nel container dei repository: {e}")

        if not storage_repo:
            raise RuntimeError("'storageunitsrepo' non è disponibile o è impostato a None.")

        self.active_storage_units = storage_repo.get_active_storage_units()

        if not self.active_storage_units:
            raise RuntimeError("Nessuna unità di archiviazione attiva trovata nel database. Impossibile proseguire.")

        for unit in self.active_storage_units:
            drive = unit.get("drive_unit", "").strip()

            if not drive:
                logger.warning(f"DicomServer: Unità storage ID {unit.get('id')} ha un drive_unit vuoto, ignorata.")
                continue

            target_dir = Path(drive) / ROOT_STORAGE

            try:
                if not target_dir.exists():
                    target_dir.mkdir(parents=True, exist_ok=True)
                    logger.info(f"DicomServer: Creata nuova cartella di archiviazione: {target_dir}")
                else:
                    logger.info(f"DicomServer: Cartella di archiviazione esistente verificata: {target_dir}")
            except Exception as e:
                raise OSError(f"Impossibile creare/verificare la cartella di archiviazione '{target_dir}': {e}")

    def _setup_dicom_server(self):
        """
        Configura il server DICOM con i parametri specificati.
        """
        ae_title = self.config_scp.get("ae_title")
        if not ae_title:
            raise ValueError("AE Title non specificato nella configurazione SCP.")

        self.ae = AE(ae_title=ae_title)

        # --- IMPOSTAZIONE IMPLEMENTATION DATA ---
        self.ae.implementation_class_uid = IMPLEMENTATION_CLASS_UID
        self.ae.implementation_version_name = IMPLEMENTATION_VERSION_NAME

        # Timeouts e dimensioni PDU
        self.ae.maximum_pdu_size = int(self.config_scp.get("max_len_pdu", 16384))
        self.ae.network_timeout = int(self.config_scp.get("network_timeout", 60))
        self.ae.acse_timeout = int(self.config_scp.get("acse_timeout", 30))
        self.ae.dimse_timeout = int(self.config_scp.get("dimse_timeout", 30))
        
        self.ip = "0.0.0.0"
        self.port = int(self.config_scp.get("porta_locale", 104))

    def _setup_default_transfer_syntaxes(self):
        """
        Configura le sintassi di trasferimento supportate dal server.
        """
        self.default_transfer_syntaxes = [
            ExplicitVRLittleEndian,
            ImplicitVRLittleEndian,
            ExplicitVRBigEndian,
        ]

    def _setup_default_presentation_contexts(self):
        """
        Registra ESCLUSIVAMENTE la SOP Class di Verification (C-ECHO)
        con le Transfer Syntax di default.
        """
        self.ae.add_supported_context(Verification, self.default_transfer_syntaxes)

    def start(self):
        """
        Avvia il server DICOM in modalità non-bloccante (multithread nativo).
        Se l'avvio fallisce (es. porta occupata), blocca il server ed evidenzia l'errore.
        """
        try:
            logger.info(f"Avvio DICOM Server '{self.ae.ae_title}' su {self.ip}:{self.port}...")

            # block=False attiva la gestione multiconnessione su thread separati
            self.server = self.ae.start_server(
                (self.ip, self.port),
                block=False,
                evt_handlers=self.handlers
            )

            if self.server is None:
                raise RuntimeError(f"Impossibile avviare il socket di ascolto sulla porta {self.port}.")

            logger.info(f"DICOM Server '{self.ae.ae_title}' pronto e in ascolto su porta {self.port}.")

        except Exception as e:
            logger.critical(f"DicomServer: Errore fatale durante l'avvio su porta {self.port}: {e}", exc_info=True)
            self.stop()
            raise e

    def stop(self):
        """Arresta il server e libera le risorse e la porta."""
        if self.server:
            try:
                logger.info("Arresto del DICOM Server...")
                self.server.shutdown()
                logger.info("DICOM Server arrestato con successo.")
            except Exception as e:
                logger.error(f"Errore durante lo spegnimento del DICOM Server: {e}")
            finally:
                self.server = None