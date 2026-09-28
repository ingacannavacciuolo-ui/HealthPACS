# library/repository/transfer_syntax_uid_repo.py

from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from library.logger import logger
from library.models.transfer_syntax_uid_model import TransferSyntaxUidModel


class TransferSyntaxUidRepo:
    """Repository ORM per le operazioni CRUD sulla tabella public.transfer_syntax_uid."""

    def __init__(self, db_manager):
        self.db = db_manager

    @staticmethod
    def _to_dict(obj: Optional[TransferSyntaxUidModel]) -> Optional[Dict[str, Any]]:
        """Converte l'istanza ORM in un dizionario Python per la compatibilità con i servizi esterni."""
        if obj is None:
            return None
        return {
            "id": obj.id,
            "uid": obj.uid,
            "uid_description": obj.uid_description,
        }

    # -------------------------------------------------------------------------
    # OPERAZIONI DI LETTURA (READ)
    # -------------------------------------------------------------------------

    def get_all(self) -> List[Dict[str, Any]]:
        """Recupera tutte le Transfer Syntax registrate nel database."""
        try:
            with self.db.get_session() as session:
                stmt = select(TransferSyntaxUidModel).order_by(TransferSyntaxUidModel.id.asc())
                results = session.execute(stmt).scalars().all()
                return [self._to_dict(ts) for ts in results]
        except Exception as e:
            logger.error(f"TransferSyntaxUidRepo: Errore durante il recupero delle Transfer Syntax: {e}")
            return []

    def get_by_id(self, ts_id: int) -> Optional[Dict[str, Any]]:
        """Recupera una Transfer Syntax tramite ID primario."""
        try:
            with self.db.get_session() as session:
                ts = session.get(TransferSyntaxUidModel, ts_id)
                return self._to_dict(ts)
        except Exception as e:
            logger.error(f"TransferSyntaxUidRepo: Errore durante il recupero ID {ts_id}: {e}")
            return None

    def get_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """Recupera una Transfer Syntax tramite la stringa UID DICOM (es. '1.2.840.10008.1.2.1')."""
        try:
            with self.db.get_session() as session:
                stmt = select(TransferSyntaxUidModel).where(TransferSyntaxUidModel.uid == uid.strip())
                ts = session.execute(stmt).scalar_one_or_none()
                return self._to_dict(ts)
        except Exception as e:
            logger.error(f"TransferSyntaxUidRepo: Errore durante il recupero UID '{uid}': {e}")
            return None

    # -------------------------------------------------------------------------
    # OPERAZIONI DI INSERIMENTO (INSERT)
    # -------------------------------------------------------------------------

    def create(self, uid: str, uid_description: str) -> Optional[int]:
        """Inserisce una nuova Transfer Syntax UID.
        
        Se l'UID esiste già (ON CONFLICT DO NOTHING), restituisce None.
        """
        try:
            with self.db.get_session() as session:
                stmt = (
                    pg_insert(TransferSyntaxUidModel)
                    .values(
                        uid=uid.strip(),
                        uid_description=uid_description.strip(),
                    )
                    .on_conflict_do_nothing(index_elements=["uid"])
                    .returning(TransferSyntaxUidModel.id)
                )
                result = session.execute(stmt).scalar_one_or_none()
                return result
        except Exception as e:
            logger.error(f"TransferSyntaxUidRepo: Errore durante la creazione della Transfer Syntax '{uid}': {e}")
            return None

    # -------------------------------------------------------------------------
    # OPERAZIONI DI AGGIORNAMENTO (UPDATE)
    # -------------------------------------------------------------------------

    def update(
        self,
        ts_id: int,
        uid: Optional[str] = None,
        uid_description: Optional[str] = None
    ) -> bool:
        """Aggiorna i campi di una specifica Transfer Syntax UID."""
        try:
            with self.db.get_session() as session:
                ts = session.get(TransferSyntaxUidModel, ts_id)
                if not ts:
                    return False

                updated = False
                if uid is not None:
                    ts.uid = uid.strip()
                    updated = True
                if uid_description is not None:
                    ts.uid_description = uid_description.strip()
                    updated = True

                return updated
        except Exception as e:
            logger.error(f"TransferSyntaxUidRepo: Errore durante l'aggiornamento della Transfer Syntax ID {ts_id}: {e}")
            return False