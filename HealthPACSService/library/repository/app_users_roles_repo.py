# library/repository/app_users_roles_repo.py

from typing import Optional, List, Dict, Any
from sqlalchemy import select, update, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from library.logger import logger
from library.models.app_users_roles_model import AppUsersRolesModel


class AppUsersRolesRepo:
    """Repository ORM per la gestione dei ruoli applicativi nella tabella public.app_users_roles."""

    def __init__(self, db_manager):
        self.db = db_manager

    @staticmethod
    def _to_dict(obj: Optional[AppUsersRolesModel]) -> Optional[Dict[str, Any]]:
        if obj is None:
            return None
        return {
            "id": obj.id,
            "name": obj.name,
            "description": obj.description,
            "can_delete_studies": obj.can_delete_studies,
        }

    def get_by_id(self, role_id: int) -> Optional[Dict[str, Any]]:
        """Recupera un ruolo tramite ID."""
        try:
            with self.db.get_session() as session:
                role = session.get(AppUsersRolesModel, role_id)
                return self._to_dict(role)
        except Exception as e:
            logger.error(f"AppUsersRolesRepo: Errore recupero ruolo ID {role_id}: {e}")
            return None

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Recupera un ruolo tramite il suo nome univoco (es. 'ADMIN')."""
        try:
            with self.db.get_session() as session:
                stmt = select(AppUsersRolesModel).where(
                    AppUsersRolesModel.name == name.strip().upper()
                )
                role = session.execute(stmt).scalar_one_or_none()
                return self._to_dict(role)
        except Exception as e:
            logger.error(f"AppUsersRolesRepo: Errore recupero ruolo '{name}': {e}")
            return None

    def get_all(self) -> List[Dict[str, Any]]:
        """Restituisce l'elenco di tutti i ruoli definiti a sistema."""
        try:
            with self.db.get_session() as session:
                stmt = select(AppUsersRolesModel).order_by(AppUsersRolesModel.id)
                roles = session.execute(stmt).scalars().all()
                return [self._to_dict(r) for r in roles]
        except Exception as e:
            logger.error(f"AppUsersRolesRepo: Errore recupero lista ruoli: {e}")
            return []

    def create(
        self, name: str, description: Optional[str] = None, can_delete_studies: bool = False
    ) -> Optional[int]:
        """Crea un nuovo ruolo nel database."""
        try:
            with self.db.get_session() as session:
                stmt = (
                    pg_insert(AppUsersRolesModel)
                    .values(
                        name=name.strip().upper(),
                        description=description.strip() if description else None,
                        can_delete_studies=can_delete_studies,
                    )
                    .on_conflict_do_nothing(index_elements=["name"])
                    .returning(AppUsersRolesModel.id)
                )
                return session.execute(stmt).scalar_one_or_none()
        except Exception as e:
            logger.error(f"AppUsersRolesRepo: Errore creazione ruolo '{name}': {e}")
            return None