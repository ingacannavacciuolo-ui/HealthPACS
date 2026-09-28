# library/repository/app_permissions_repo.py

from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from library.logger import logger
from library.models.app_users_permissions_model import AppUsersPermissionsModel


class AppPermissionsRepo:
    """Repository ORM per la gestione della tabella public.app_permissions."""

    def __init__(self, db_manager):
        self.db = db_manager

    @staticmethod
    def _to_dict(obj: Optional[AppUsersPermissionsModel]) -> Optional[Dict[str, Any]]:
        """Utility per convertire l'istanza del modello ORM in un dizionario."""
        if obj is None:
            return None
        return {
            "id": obj.id,
            "code": obj.code,
            "description": obj.description,
        }

    def get_by_id(self, permission_id: int) -> Optional[Dict[str, Any]]:
        """Recupera un permesso in base al suo ID univoco."""
        try:
            with self.db.get_session() as session:
                perm = session.get(AppUsersPermissionsModel, permission_id)
                return self._to_dict(perm)
        except Exception as e:
            logger.error(
                f"AppPermissionsRepo: Errore recupero permesso ID {permission_id}: {e}"
            )
            return None

    def get_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Recupera un permesso in base al suo codice univoco (es. 'study:read')."""
        try:
            with self.db.get_session() as session:
                stmt = select(AppUsersPermissionsModel).where(
                    AppUsersPermissionsModel.code == code.strip().lower()
                )
                perm = session.execute(stmt).scalar_one_or_none()
                return self._to_dict(perm)
        except Exception as e:
            logger.error(
                f"AppPermissionsRepo: Errore recupero permesso con codice '{code}': {e}"
            )
            return None

    def get_all(self) -> List[Dict[str, Any]]:
        """Recupera la lista completa di tutti i permessi censiti a sistema."""
        try:
            with self.db.get_session() as session:
                stmt = select(AppUsersPermissionsModel).order_by(AppUsersPermissionsModel.id)
                results = session.execute(stmt).scalars().all()
                return [self._to_dict(perm) for perm in results]
        except Exception as e:
            logger.error(
                f"AppPermissionsRepo: Errore recupero lista di tutti i permessi: {e}"
            )
            return []

    def create(self, code: str, description: Optional[str] = None) -> Optional[int]:
        """Crea un nuovo permesso a sistema.

        Restituisce l'ID del nuovo permesso creato, oppure None se esiste già un codice duplicato.
        """
        clean_code = code.strip().lower()
        try:
            with self.db.get_session() as session:
                stmt = (
                    pg_insert(AppUsersPermissionsModel)
                    .values(
                        code=clean_code,
                        description=description.strip() if description else None,
                    )
                    .on_conflict_do_nothing(index_elements=["code"])
                    .returning(AppUsersPermissionsModel.id)
                )
                new_id = session.execute(stmt).scalar_one_or_none()
                return new_id
        except Exception as e:
            logger.error(
                f"AppPermissionsRepo: Errore creazione permesso '{clean_code}': {e}"
            )
            return None