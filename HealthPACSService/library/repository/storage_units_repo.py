# library/repository/storage_units_repo.py

from typing import Optional, List, Dict, Any
from sqlalchemy import select
from library.logger import logger
from library.models.storage_unit_model import StorageUnitModel


class StorageUnitsRepo:
    """Repository ORM per le operazioni CRUD sulla tabella public.storage_units."""

    def __init__(self, db_manager):
        self.db = db_manager

    @staticmethod
    def _to_dict(obj: Optional[StorageUnitModel]) -> Optional[Dict[str, Any]]:
        """Mappa solo i campi reali definiti nel DB."""
        if obj is None:
            return None
        return {
            "id": obj.id,
            "drive_unit": obj.drive_unit,
            "enabled": obj.enabled,
            "limit_threshold_storage": obj.limit_threshold_storage,
            "alert_threshold_storage": obj.alert_threshold_storage,
        }

    # -------------------------------------------------------------------------
    # OPERAZIONI DI LETTURA (READ)
    # -------------------------------------------------------------------------

    def get_active_storage_units(self) -> List[Dict[str, Any]]:
        """Recupera tutte le unità di archiviazione abilitate (enabled = TRUE)."""
        try:
            with self.db.get_session() as session:
                stmt = (
                    select(StorageUnitModel)
                    .where(StorageUnitModel.enabled.is_(True))
                    .order_by(StorageUnitModel.id.asc())
                )
                results = session.execute(stmt).scalars().all()
                return [self._to_dict(unit) for unit in results]
        except Exception as e:
            logger.error(f"StorageUnitsRepo: Errore durante il recupero delle unità attive: {e}")
            return []

    def get_by_id(self, unit_id: int) -> Optional[Dict[str, Any]]:
        """Recupera una singola unità di archiviazione tramite ID."""
        try:
            with self.db.get_session() as session:
                unit = session.get(StorageUnitModel, unit_id)
                return self._to_dict(unit)
        except Exception as e:
            logger.error(f"StorageUnitsRepo: Errore durante il recupero dell'unità ID {unit_id}: {e}")
            return None

    # -------------------------------------------------------------------------
    # INSERIMENTO & MODIFICA (INSERT & UPDATE)
    # -------------------------------------------------------------------------

    def create(
        self,
        drive_unit: str,
        enabled: bool = True,
        limit_threshold_storage: int = 90,
        alert_threshold_storage: int = 85,
    ) -> Optional[int]:
        """Inserisce una nuova unità di archiviazione."""
        try:
            with self.db.get_session() as session:
                unit = StorageUnitModel(
                    drive_unit=drive_unit.strip(),
                    enabled=enabled,
                    limit_threshold_storage=limit_threshold_storage,
                    alert_threshold_storage=alert_threshold_storage,
                )
                session.add(unit)
                session.flush()
                return unit.id
        except Exception as e:
            logger.error(f"StorageUnitsRepo: Errore durante la creazione dell'unità: {e}")
            return None

    def update(
        self,
        unit_id: int,
        drive_unit: Optional[str] = None,
        enabled: Optional[bool] = None,
        limit_threshold_storage: Optional[int] = None,
        alert_threshold_storage: Optional[int] = None,
    ) -> bool:
        """Aggiorna i campi di una specifica unità di archiviazione."""
        try:
            with self.db.get_session() as session:
                unit = session.get(StorageUnitModel, unit_id)
                if not unit:
                    return False

                updated = False
                if drive_unit is not None:
                    unit.drive_unit = drive_unit.strip()
                    updated = True
                if enabled is not None:
                    unit.enabled = enabled
                    updated = True
                if limit_threshold_storage is not None:
                    unit.limit_threshold_storage = limit_threshold_storage
                    updated = True
                if alert_threshold_storage is not None:
                    unit.alert_threshold_storage = alert_threshold_storage
                    updated = True

                return updated
        except Exception as e:
            logger.error(f"StorageUnitsRepo: Errore durante l'aggiornamento dell'unità ID {unit_id}: {e}")
            return False