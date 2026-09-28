# library/repository/dicom_scp_repo.py

from typing import Optional, Dict, Any
from sqlalchemy import select
from library.logger import logger
from library.models.dicom_scp_model import DicomScpModel


class DicomScpRepo:
    """Repository per le operazioni CRUD sulla tabella public.dicom_scp (Configurazione Server SCP)."""

    def __init__(self, db_manager):
        self.db = db_manager

    @staticmethod
    def _to_dict(obj: Optional[DicomScpModel]) -> Optional[Dict[str, Any]]:
        """Utility per convertire un'istanza ORM in un dizionario compatibile con l'interfaccia esistente."""
        if obj is None:
            return None
        return {
            "id": obj.id,
            "ae_title": obj.ae_title,
            "porta_locale": obj.porta_locale,
            "max_len_pdu": obj.max_len_pdu,
            "network_timeout": obj.network_timeout,
            "acse_timeout": obj.acse_timeout,
            "dimse_timeout": obj.dimse_timeout,
        }

    # -------------------------------------------------------------------------
    # OPERAZIONI DI LETTURA (READ)
    # -------------------------------------------------------------------------

    def get_config_scp(self) -> Optional[Dict[str, Any]]:
        """Recupera la configurazione attiva del server DICOM SCP (primo record trovato)."""
        try:
            with self.db.get_session() as session:
                stmt = select(DicomScpModel).order_by(DicomScpModel.id.asc()).limit(1)
                result = session.execute(stmt).scalar_one_or_none()
                return self._to_dict(result)
        except Exception as e:
            logger.error(f"DicomScpRepo: Errore durante il recupero della configurazione SCP: {e}")
            return None

    def get_by_id(self, scp_id: int) -> Optional[Dict[str, Any]]:
        """Recupera una specifica configurazione SCP tramite ID primario."""
        try:
            with self.db.get_session() as session:
                result = session.get(DicomScpModel, scp_id)
                return self._to_dict(result)
        except Exception as e:
            logger.error(f"DicomScpRepo: Errore durante il recupero SCP con ID {scp_id}: {e}")
            return None

    # -------------------------------------------------------------------------
    # OPERAZIONI DI INSERIMENTO (INSERT)
    # -------------------------------------------------------------------------

    def create(
        self,
        ae_title: str,
        porta_locale: int,
        max_len_pdu: int = 16384,
        network_timeout: int = 30,
        acse_timeout: int = 30,
        dimse_timeout: int = 30
    ) -> Optional[int]:
        """Inserisce una nuova configurazione per il server SCP."""
        try:
            with self.db.get_session() as session:
                scp = DicomScpModel(
                    ae_title=ae_title.strip(),
                    porta_locale=porta_locale,
                    max_len_pdu=max_len_pdu,
                    network_timeout=network_timeout,
                    acse_timeout=acse_timeout,
                    dimse_timeout=dimse_timeout,
                )
                session.add(scp)
                session.flush()  # Assegna l'ID primario prima della chiusura della transazione
                return scp.id
        except Exception as e:
            logger.error(f"DicomScpRepo: Errore durante la creazione della configurazione SCP: {e}")
            return None

    # -------------------------------------------------------------------------
    # OPERAZIONI DI AGGIORNAMENTO (UPDATE)
    # -------------------------------------------------------------------------

    def update(
        self,
        scp_id: int,
        ae_title: Optional[str] = None,
        porta_locale: Optional[int] = None,
        max_len_pdu: Optional[int] = None,
        network_timeout: Optional[int] = None,
        acse_timeout: Optional[int] = None,
        dimse_timeout: Optional[int] = None
    ) -> bool:
        """Aggiorna i parametri della configurazione SCP specificata."""
        try:
            with self.db.get_session() as session:
                scp = session.get(DicomScpModel, scp_id)
                if not scp:
                    return False

                updated = False
                if ae_title is not None:
                    scp.ae_title = ae_title.strip()
                    updated = True
                if porta_locale is not None:
                    scp.porta_locale = porta_locale
                    updated = True
                if max_len_pdu is not None:
                    scp.max_len_pdu = max_len_pdu
                    updated = True
                if network_timeout is not None:
                    scp.network_timeout = network_timeout
                    updated = True
                if acse_timeout is not None:
                    scp.acse_timeout = acse_timeout
                    updated = True
                if dimse_timeout is not None:
                    scp.dimse_timeout = dimse_timeout
                    updated = True

                return updated
        except Exception as e:
            logger.error(f"DicomScpRepo: Errore durante l'aggiornamento SCP ID {scp_id}: {e}")
            return False