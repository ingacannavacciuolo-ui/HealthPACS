# library/repository/app_users_repo.py

from typing import Optional, List, Dict, Any, Set
from sqlalchemy import select, update, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from library.logger import logger
from library.models.app_users_model import AppUsersModel
from library.models.app_users_roles_model import AppUsersRolesModel
from library.models.app_users_roles_permissions_model import AppUsersRolesPermissionsModel
from library.models.app_users_permissions_model import AppUsersPermissionsModel

class AppUsersRepo:
    """Repository ORM per la gestione degli utenti nella tabella public.app_users."""

    def __init__(self, db_manager):
        self.db = db_manager

    @staticmethod
    def _to_dict(obj: Optional[AppUsersModel]) -> Optional[Dict[str, Any]]:
        if obj is None:
            return None
        return {
            "id": obj.id,
            "username": obj.username,
            "password_hash": obj.password_hash,
            "first_name": obj.first_name,
            "last_name": obj.last_name,
            "email": obj.email,
            "is_active": obj.is_active,
            "users_roles_id": obj.users_roles_id,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
        }

    def get_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Recupera un utente dal suo ID."""
        try:
            with self.db.get_session() as session:
                user = session.get(AppUsersModel, user_id)
                return self._to_dict(user)
        except Exception as e:
            logger.error(f"AppUsersRepo: Errore recupero utente ID {user_id}: {e}")
            return None

    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Recupera un utente dal suo username univoco."""
        try:
            with self.db.get_session() as session:
                stmt = select(AppUsersModel).where(
                    AppUsersModel.username == username.strip().lower()
                )
                user = session.execute(stmt).scalar_one_or_none()
                return self._to_dict(user)
        except Exception as e:
            logger.error(f"AppUsersRepo: Errore recupero utente '{username}': {e}")
            return None

    def get_user_with_role(self, user_id: int) -> Optional[Dict[str, Any]]:
        """JOIN esplicita manuale per recuperare l'utente insieme alle informazioni sul suo ruolo."""
        try:
            with self.db.get_session() as session:
                stmt = (
                    select(AppUsersModel, AppUsersRolesModel)
                    .join(
                        AppUsersRolesModel,
                        AppUsersModel.users_roles_id == AppUsersRolesModel.id,
                    )
                    .where(AppUsersModel.id == user_id)
                )
                row = session.execute(stmt).first()
                if not row:
                    return None

                user_obj, role_obj = row
                user_dict = self._to_dict(user_obj)
                user_dict["role"] = {
                    "id": role_obj.id,
                    "name": role_obj.name,
                    "description": role_obj.description,
                }
                return user_dict
        except Exception as e:
            logger.error(
                f"AppUsersRepo: Errore JOIN utente/ruolo per utente ID {user_id}: {e}"
            )
            return None

    def create(
        self,
        username: str,
        password_hash: str,
        users_roles_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        is_active: bool = True,
    ) -> Optional[int]:
        """Registra un nuovo utente nel sistema."""
        try:
            with self.db.get_session() as session:
                stmt = (
                    pg_insert(AppUsersModel)
                    .values(
                        username=username.strip().lower(),
                        password_hash=password_hash,
                        users_roles_id=users_roles_id,
                        first_name=first_name.strip() if first_name else None,
                        last_name=last_name.strip() if last_name else None,
                        email=email.strip().lower() if email else None,
                        is_active=is_active,
                    )
                    .on_conflict_do_nothing(index_elements=["username"])
                    .returning(AppUsersModel.id)
                )
                return session.execute(stmt).scalar_one_or_none()
        except Exception as e:
            logger.error(f"AppUsersRepo: Errore creazione utente '{username}': {e}")
            return None
        
    def get_effective_permission_codes(self, user_id: int) -> Set[str]:
        """Recupera l'insieme dei codici di permesso associati al ruolo dell'utente.

        Esegue la JOIN tra:
        - public.app_users (per identificare il ruolo dell'utente)
        - public.app_users_roles_permissions (tabella ponte ruolo-permessi)
        - public.app_users_permissions (anagrafica dei permessi)
        """
        try:
            with self.db.get_session() as session:
                stmt = (
                    select(AppUsersPermissionsModel.code)
                    .join(
                        AppUsersRolesPermissionsModel,
                        AppUsersPermissionsModel.id
                        == AppUsersRolesPermissionsModel.permission_id,
                    )
                    .join(
                        AppUsersModel,
                        AppUsersModel.users_roles_id
                        == AppUsersRolesPermissionsModel.role_id,
                    )
                    .where(AppUsersModel.id == user_id)
                )
                
                permissions = session.execute(stmt).scalars().all()
                return set(permissions)
                
        except Exception as e:
            logger.error(
                f"AppUsersRepo: Errore recupero permessi per utente ID {user_id}: {e}"
            )
            return set()