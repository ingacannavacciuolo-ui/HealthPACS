# library/repository/sop_class_uid_repo.py

from typing import Optional, List, Dict, Any
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from library.logger import logger
from library.models import SopClassUidModel


class SopClassUidRepo:
    """Repository ORM per le operazioni CRUD sulla tabella public.sop_class_uid."""

    def __init__(self, db_manager):
        self.db = db_manager

    @staticmethod
    def _to_dict(obj: Optional[SopClassUidModel]) -> Optional[Dict[str, Any]]:
        """Converte l'istanza ORM in un dizionario Python per la compatibilità con i servizi esterni."""
        if obj is None:
            return None
        return {
            "id": obj.id,
            "uid": obj.uid,
            "uid_description": obj.uid_description,
            "service_type": obj.service_type,
        }

    # -------------------------------------------------------------------------
    # OPERAZIONI DI LETTURA (READ)
    # -------------------------------------------------------------------------

    def get_all(self) -> List[Dict[str, Any]]:
        """Recupera tutti i record delle SOP Class registrate."""
        try:
            with self.db.get_session() as session:
                stmt = select(SopClassUidModel).order_by(SopClassUidModel.id.asc())
                results = session.execute(stmt).scalars().all()
                return [self._to_dict(sop) for sop in results]
        except Exception as e:
            logger.error(f"SopClassUidRepo: Errore durante il recupero delle SOP Class: {e}")
            return []

    def get_all_uids(self) -> List[str]:
        """Recupera la lista semplice contenente solo gli UID (stringhe) delle SOP Class."""
        try:
            with self.db.get_session() as session:
                stmt = select(SopClassUidModel.uid).order_by(SopClassUidModel.id.asc())
                results = session.execute(stmt).scalars().all()
                return [uid for uid in results if uid]
        except Exception as e:
            logger.error(f"SopClassUidRepo: Errore durante il recupero della lista UID SOP Class: {e}")
            return []

    def get_by_id(self, sop_id: int) -> Optional[Dict[str, Any]]:
        """Recupera una SOP Class tramite ID primario."""
        try:
            with self.db.get_session() as session:
                sop = session.get(SopClassUidModel, sop_id)
                return self._to_dict(sop)
        except Exception as e:
            logger.error(f"SopClassUidRepo: Errore durante il recupero della SOP Class ID {sop_id}: {e}")
            return None

    def get_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """Recupera una SOP Class tramite la stringa UID DICOM (es. '1.2.840.10008.5.1.4.1.1.2')."""
        try:
            with self.db.get_session() as session:
                stmt = select(SopClassUidModel).where(SopClassUidModel.uid == uid.strip())
                sop = session.execute(stmt).scalar_one_or_none()
                return self._to_dict(sop)
        except Exception as e:
            logger.error(f"SopClassUidRepo: Errore durante il recupero della SOP Class UID '{uid}': {e}")
            return None

    # -------------------------------------------------------------------------
    # OPERAZIONI DI INSERIMENTO (INSERT)
    # -------------------------------------------------------------------------

    def create(
        self,
        uid: str,
        uid_description: Optional[str] = None,
        service_type: str = "STORAGE",
    ) -> Optional[int]:
        """Inserisce una nuova SOP Class UID.

        Se l'UID esiste già (ON CONFLICT DO NOTHING), restituisce None.
        """
        try:
            with self.db.get_session() as session:
                stmt = (
                    pg_insert(SopClassUidModel)
                    .values(
                        uid=uid.strip(),
                        uid_description=uid_description.strip() if uid_description else None,
                        service_type=service_type.strip(),
                    )
                    .on_conflict_do_nothing(index_elements=["uid"])
                    .returning(SopClassUidModel.id)
                )
                result = session.execute(stmt).scalar_one_or_none()
                return result
        except Exception as e:
            logger.error(f"SopClassUidRepo: Errore durante la creazione della SOP Class UID '{uid}': {e}")
            return None

    # -------------------------------------------------------------------------
    # OPERAZIONI DI AGGIORNAMENTO (UPDATE)
    # -------------------------------------------------------------------------

    def update(
        self,
        sop_id: int,
        uid: Optional[str] = None,
        uid_description: Optional[str] = None,
        service_type: Optional[str] = None,
    ) -> bool:
        """Aggiorna i campi di una specifica SOP Class UID."""
        try:
            with self.db.get_session() as session:
                sop = session.get(SopClassUidModel, sop_id)
                if not sop:
                    return False

                updated = False
                if uid is not None:
                    sop.uid = uid.strip()
                    updated = True
                if uid_description is not None:
                    sop.uid_description = uid_description.strip()
                    updated = True
                if service_type is not None:
                    sop.service_type = service_type.strip()
                    updated = True

                return updated
        except Exception as e:
            logger.error(f"SopClassUidRepo: Errore durante l'aggiornamento della SOP Class ID {sop_id}: {e}")
            return False