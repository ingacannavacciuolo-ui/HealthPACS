from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from library.logger import logger
from library.models import AppSystemSettingsModel


class AppSystemSettingsRepo:
    """Repository ORM per la gestione della tabella public.app_system_settings."""

    def __init__(self, db_manager):
        self.db = db_manager

    @staticmethod
    def _to_dict(obj: Optional[AppSystemSettingsModel]) -> Optional[Dict[str, Any]]:
        """Utility per convertire l'istanza del modello ORM in un dizionario."""
        if obj is None:
            return None
        return {
            "setting_key": obj.setting_key,
            "setting_value": obj.setting_value,
            "description": obj.description,
            "updated_at": obj.updated_at,
        }

    def get_setting_value(
        self, setting_key: str, default_value: Optional[str] = None
    ) -> Optional[str]:
        """Recupera direttamente il valore stringa (setting_value) di una configurazione."""
        key_clean = setting_key.strip()
        try:
            with self.db.get_session() as session:
                setting = session.get(AppSystemSettingsModel, key_clean)
                if setting and setting.setting_value is not None:
                    return setting.setting_value
        except Exception as e:
            logger.error(
                f"AppSystemSettingsRepo: Errore recupero valore per la chiave '{key_clean}': {e}"
            )

        return default_value

    def get_by_key(self, setting_key: str) -> Optional[Dict[str, Any]]:
        """Recupera il record completo di una configurazione data la sua chiave."""
        key_clean = setting_key.strip()
        try:
            with self.db.get_session() as session:
                setting = session.get(AppSystemSettingsModel, key_clean)
                return self._to_dict(setting)
        except Exception as e:
            logger.error(
                f"AppSystemSettingsRepo: Errore recupero record per la chiave '{key_clean}': {e}"
            )
            return None

    def get_all(self) -> List[Dict[str, Any]]:
        """Recupera la lista completa di tutte le configurazioni di sistema."""
        try:
            with self.db.get_session() as session:
                stmt = select(AppSystemSettingsModel).order_by(
                    AppSystemSettingsModel.setting_key
                )
                results = session.execute(stmt).scalars().all()
                return [self._to_dict(setting) for setting in results]
        except Exception as e:
            logger.error(
                f"AppSystemSettingsRepo: Errore recupero lista configurazioni: {e}"
            )
            return []

    def set_setting(
        self,
        setting_key: str,
        setting_value: str,
        description: Optional[str] = None,
    ) -> bool:
        """Inserisce o aggiorna (UPSERT su PostgreSQL) una configurazione di sistema."""
        key_clean = setting_key.strip()
        try:
            with self.db.get_session() as session:
                stmt = (
                    pg_insert(AppSystemSettingsModel)
                    .values(
                        setting_key=key_clean,
                        setting_value=setting_value,
                        description=description.strip() if description else None,
                    )
                    .on_conflict_do_update(
                        index_elements=["setting_key"],
                        set_={
                            "setting_value": setting_value,
                            "description": description.strip() if description else AppSystemSettingsModel.description,
                        },
                    )
                )
                session.execute(stmt)
                return True
        except Exception as e:
            logger.error(
                f"AppSystemSettingsRepo: Errore salvataggio configurazione '{key_clean}': {e}"
            )
            return False

    def delete(self, setting_key: str) -> bool:
        """Elimina una configurazione di sistema in base alla sua chiave."""
        key_clean = setting_key.strip()
        try:
            with self.db.get_session() as session:
                setting = session.get(AppSystemSettingsModel, key_clean)
                if setting:
                    session.delete(setting)
                    return True
                return False
        except Exception as e:
            logger.error(
                f"AppSystemSettingsRepo: Errore eliminazione configurazione '{key_clean}': {e}"
            )
            return False