# library/repository/app_users_sessions_repo.py

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import select, update
from library.logger import logger
from library.models import AppUsersSessionsModel


class AppUsersSessionsRepo:
    """Repository ORM per la gestione della tabella public.app_users_sessions."""

    def __init__(self, db_manager):
        self.db = db_manager

    def create_session(
        self,
        user_id: int,
        session_token: str,
        duration_minutes: int = 480,  # Default: 8 ore
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Optional[int]:
        """Crea una nuova sessione utente e restituisce l'ID generato."""
        try:
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(minutes=duration_minutes)

            with self.db.get_session() as session:
                new_session = AppUsersSessionsModel(
                    user_id=user_id,
                    session_token=session_token,
                    created_at=now,
                    last_activity=now,
                    expires_at=expires_at,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    is_active=True,
                )
                session.add(new_session)
                session.commit()
                return new_session.id
        except Exception as e:
            logger.error(
                f"AppUsersSessionsRepo: Errore creazione sessione per utente {user_id}: {e}"
            )
            return None

    def get_valid_session(
        self, session_token: str, touch_activity: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Recupera e verifica se un token di sessione è attivo e non scaduto.

        Se `touch_activity` è True, aggiorna la colonna `last_activity` per la sliding expiration.
        """
        try:
            now = datetime.now(timezone.utc)
            with self.db.get_session() as session:
                stmt = select(AppUsersSessionsModel).where(
                    AppUsersSessionsModel.session_token == session_token,
                    AppUsersSessionsModel.is_active == True,
                    AppUsersSessionsModel.expires_at > now,
                )
                sess = session.execute(stmt).scalar_one_or_none()
                if not sess:
                    return None

                if touch_activity:
                    sess.last_activity = now
                    session.commit()

                return {
                    "id": sess.id,
                    "user_id": sess.user_id,
                    "session_token": sess.session_token,
                    "expires_at": sess.expires_at,
                    "last_activity": sess.last_activity,
                }
        except Exception as e:
            logger.error(
                f"AppUsersSessionsRepo: Errore verifica token sessione: {e}"
            )
            return None

    def invalidate_session(self, session_token: str) -> bool:
        """Disattiva una sessione impostando is_active = False (utilizzato per il Logout)."""
        try:
            with self.db.get_session() as session:
                stmt = (
                    update(AppUsersSessionsModel)
                    .where(
                        AppUsersSessionsModel.session_token == session_token
                    )
                    .values(is_active=False)
                )
                session.execute(stmt)
                session.commit()
                return True
        except Exception as e:
            logger.error(
                f"AppUsersSessionsRepo: Errore invalidazione sessione: {e}"
            )
            return False

    def invalidate_all_user_sessions(self, user_id: int) -> bool:
        """Disattiva tutte le sessioni attive per un determinato utente (es. cambio password o blocco)."""
        try:
            with self.db.get_session() as session:
                stmt = (
                    update(AppUsersSessionsModel)
                    .where(
                        AppUsersSessionsModel.user_id == user_id,
                        AppUsersSessionsModel.is_active == True,
                    )
                    .values(is_active=False)
                )
                session.execute(stmt)
                session.commit()
                return True
        except Exception as e:
            logger.error(
                f"AppUsersSessionsRepo: Errore invalidazione sessioni utente {user_id}: {e}"
            )
            return False