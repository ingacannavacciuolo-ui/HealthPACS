# library/repository/sessioni_web_repo.py

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from library.logger import logger
from library.models import SessioniWebModel


class SessioniWebRepo:
    """Repository ORM per la gestione delle sessioni attive e della loro scadenza scorrevole."""

    def __init__(self, db_manager):
        self.db = db_manager

    @staticmethod
    def _to_dict(obj: Optional[SessioniWebModel]) -> Optional[Dict[str, Any]]:
        if obj is None:
            return None
        return {
            "id": obj.id,
            "token_sessione": obj.token_sessione,
            "username": obj.username,
            "data_scadenza": obj.data_scadenza,
        }

    def create_session(self, token_sessione: str, username: str, duration_minutes: int = 30) -> Optional[int]:
        """Registra un nuovo token di sessione con una data di scadenza iniziale."""
        try:
            data_scadenza = datetime.now() + timedelta(minutes=duration_minutes)
            with self.db.get_session() as session:
                stmt = (
                    pg_insert(SessioniWebModel)
                    .values(
                        token_sessione=token_sessione.strip(),
                        username=username.strip().lower(),
                        data_scadenza=data_scadenza,
                    )
                    .on_conflict_do_nothing(index_elements=["token_sessione"])
                    .returning(SessioniWebModel.id)
                )
                return session.execute(stmt).scalar_one_or_none()
        except Exception as e:
            logger.error(f"SessioniWebRepo: Errore creazione sessione per '{username}': {e}")
            return None

    def validate_and_renew(self, token_sessione: str, duration_minutes: int = 30) -> Optional[Dict[str, Any]]:
        """Verifica se il token è valido e non scaduto.
        
        Se valido, allunga la data di scadenza (Sliding Expiration) di `duration_minutes`.
        """
        try:
            now = datetime.now()
            with self.db.get_session() as session:
                stmt = select(SessioniWebModel).where(
                    SessioniWebModel.token_sessione == token_sessione.strip(),
                    SessioniWebModel.data_scadenza > now,
                )
                sess_obj = session.execute(stmt).scalar_one_or_none()

                if not sess_obj:
                    return None  # Sessione non trovata o già scaduta

                # Rinnovo dinamico della scadenza (Sliding Window)
                sess_obj.data_scadenza = now + timedelta(minutes=duration_minutes)
                return self._to_dict(sess_obj)
        except Exception as e:
            logger.error(f"SessioniWebRepo: Errore validazione/rinnovo token '{token_sessione}': {e}")
            return None

    def delete_session(self, token_sessione: str) -> bool:
        """Elimina la sessione (es. al Logout dell'utente)."""
        try:
            with self.db.get_session() as session:
                stmt = delete(SessioniWebModel).where(
                    SessioniWebModel.token_sessione == token_sessione.strip()
                )
                res = session.execute(stmt)
                return res.rowcount > 0
        except Exception as e:
            logger.error(f"SessioniWebRepo: Errore cancellazione sessione '{token_sessione}': {e}")
            return False

    def clean_expired_sessions(self) -> int:
        """Pulisce dal database tutte le sessioni vecchie/scadute (da eseguire periodicamente)."""
        try:
            with self.db.get_session() as session:
                stmt = delete(SessioniWebModel).where(
                    SessioniWebModel.data_scadenza <= datetime.now()
                )
                res = session.execute(stmt)
                return res.rowcount
        except Exception as e:
            logger.error(f"SessioniWebRepo: Errore pulizia sessioni scadute: {e}")
            return 0