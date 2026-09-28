# library/repository/app_users_roles_permissions_repo.py

from typing import List, Dict, Any
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from library.logger import logger
from library.models.app_users_permissions_model import AppUsersPermissionsModel
from library.models.app_users_roles_permissions_model import (
    AppUsersRolesPermissionsModel,
)


class AppUsersRolesPermissionsRepo:
    """Repository per la gestione delle associazioni tra Ruoli e Permessi."""

    def __init__(self, db_manager):
        self.db = db_manager

    def assign_permission_to_role(self, role_id: int, permission_id: int) -> bool:
        """Associa un singolo permesso a un ruolo (ignora se già esistente)."""
        try:
            with self.db.get_session() as session:
                stmt = (
                    pg_insert(AppUsersRolesPermissionsModel)
                    .values(role_id=role_id, permission_id=permission_id)
                    .on_conflict_do_nothing()
                )
                session.execute(stmt)
                return True
        except Exception as e:
            logger.error(
                f"AppUsersRolesPermissionsRepo: Errore associazione permesso {permission_id} a ruolo {role_id}: {e}"
            )
            return False

    def remove_permission_from_role(self, role_id: int, permission_id: int) -> bool:
        """Rimuove un permesso da un ruolo."""
        try:
            with self.db.get_session() as session:
                stmt = delete(AppUsersRolesPermissionsModel).where(
                    AppUsersRolesPermissionsModel.role_id == role_id,
                    AppUsersRolesPermissionsModel.permission_id == permission_id,
                )
                session.execute(stmt)
                return True
        except Exception as e:
            logger.error(
                f"AppUsersRolesPermissionsRepo: Errore rimozione permesso {permission_id} da ruolo {role_id}: {e}"
            )
            return False

    def get_permissions_by_role_id(self, role_id: int) -> List[Dict[str, Any]]:
        """Recupera tutti i permessi associati a uno specifico ruolo."""
        try:
            with self.db.get_session() as session:
                stmt = (
                    select(AppUsersPermissionsModel)
                    .join(
                        AppUsersRolesPermissionsModel,
                        AppUsersPermissionsModel.id
                        == AppUsersRolesPermissionsModel.permission_id,
                    )
                    .where(AppUsersRolesPermissionsModel.role_id == role_id)
                    .order_by(AppUsersPermissionsModel.id)
                )
                results = session.execute(stmt).scalars().all()
                return [
                    {
                        "id": perm.id,
                        "code": perm.code,
                        "description": perm.description,
                    }
                    for perm in results
                ]
        except Exception as e:
            logger.error(
                f"AppUsersRolesPermissionsRepo: Errore recupero permessi per ruolo ID {role_id}: {e}"
            )
            return []

    def get_permission_codes_by_role_id(self, role_id: int) -> List[str]:
        """Recupera l'elenco dei soli codici (stringhe) dei permessi associati a un ruolo."""
        try:
            with self.db.get_session() as session:
                stmt = (
                    select(AppUsersPermissionsModel.code)
                    .join(
                        AppUsersRolesPermissionsModel,
                        AppUsersPermissionsModel.id
                        == AppUsersRolesPermissionsModel.permission_id,
                    )
                    .where(AppUsersRolesPermissionsModel.role_id == role_id)
                )
                return list(session.execute(stmt).scalars().all())
        except Exception as e:
            logger.error(
                f"AppUsersRolesPermissionsRepo: Errore recupero codici permessi per ruolo ID {role_id}: {e}"
            )
            return []

    def sync_role_permissions(
        self, role_id: int, permission_ids: List[int]
    ) -> bool:
        """Sostituisce in blocco tutti i permessi di un ruolo con la nuova lista di permission_ids."""
        try:
            with self.db.get_session() as session:
                # 1. Rimuove le vecchie associazioni
                session.execute(
                    delete(AppUsersRolesPermissionsModel).where(
                        AppUsersRolesPermissionsModel.role_id == role_id
                    )
                )

                # 2. Inserisce le nuove se la lista non è vuota
                if permission_ids:
                    records = [
                        {"role_id": role_id, "permission_id": pid}
                        for pid in permission_ids
                    ]
                    session.execute(
                        pg_insert(AppUsersRolesPermissionsModel), records
                    )
                return True
        except Exception as e:
            logger.error(
                f"AppUsersRolesPermissionsRepo: Errore sincronizzazione permessi per ruolo ID {role_id}: {e}"
            )
            return False