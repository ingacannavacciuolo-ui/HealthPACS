# library/services/auth_service.py

import secrets
from typing import Optional, Dict, Any
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from library.logger import logger
from library.repository import AppUsersRepo
from library.repository import AppUsersSessionsRepo
from library.repository import AppSystemSettingsRepo


class AuthService:
    """Servizio per la gestione di Login, Logout e Validazione Sessione/Permessi."""

    def __init__(self, db_manager):
        self.db = db_manager
        self.users_repo = AppUsersRepo(db_manager)
        self.sessions_repo = AppUsersSessionsRepo(db_manager)
        self.settings_repo = AppSystemSettingsRepo(db_manager)
        self.ph = PasswordHasher()

    def _get_session_duration_minutes(self) -> int:
        """Legge la durata della sessione dal database (public.app_system_settings).

        Fallback a 30 minuti in caso di errore o valore mancante.
        """
        val_str = self.settings_repo.get_setting_value(
            "session_duration_minutes", default_value="480"
        )
        try:
            return int(val_str)
        except (ValueError, TypeError):
            logger.warning(
                f"AuthService: Valore non valido per 'session_duration_minutes' ('{val_str}'). Uso fallback a 30m."
            )
            return 30

    def login(
        self,
        username: str,
        password_plain: str,
        duration_minutes: Optional[int] = None, 
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Esegue il flusso di autenticazione completo:
        
        1. Cerca l'utente per username e ne verifica lo stato (is_active).
        2. Verifica l'hash Argon2id della password fornita.
        3. Genera un token crittograficamente sicuro di 64 caratteri esadecimali.
        4. Registra la sessione nella tabella app_users_sessions con IP e User-Agent.
        5. Calcola l'insieme dei permessi effettivi dell'utente (Ruolo + Overrides).
        """
        clean_username = username.strip()

        # 1. Recupera l'utente dal repository
        user = self.users_repo.get_by_username(clean_username)
        if not user:
            logger.warning(
                f"AuthService: Tentativo di login fallito. Utente non trovato: '{clean_username}'"
            )
            return None

        if not user.get("is_active", False):
            logger.warning(
                f"AuthService: Tentativo di login fallito. Utente disabilitato: '{clean_username}'"
            )
            return None

        # 2. Verifica hash della password con Argon2id
        try:
            self.ph.verify(user["password_hash"], password_plain)
        except (VerifyMismatchError, VerificationError):
            logger.warning(
                f"AuthService: Password errata per l'utente: '{clean_username}'"
            )
            return None
        except Exception as e:
            logger.error(
                f"AuthService: Errore durante la verifica password per '{clean_username}': {e}"
            )
            return None

        # 3. Determina la durata della sessione (da DB se non passata esplicitamente)
        if duration_minutes is None:
            duration_minutes = self._get_session_duration_minutes()
            
        # 4. Generazione Token di Sessione Unico (64 caratteri esadecimali)
        session_token = secrets.token_hex(32)

        # 4. Registrazione della sessione sulla tabella unificata app_users_sessions
        session_id = self.sessions_repo.create_session(
            user_id=user["id"],
            session_token=session_token,
            duration_minutes=duration_minutes,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if not session_id:
            logger.error(
                f"AuthService: Impossibile creare la sessione DB per utente '{clean_username}'"
            )
            return None

        # 5. Calcolo permessi effettivi (Ruolo + Eccezioni)
        permissions = self.users_repo.get_effective_permission_codes(user["id"])

        logger.info(
            f"AuthService: Login eseguito con successo. Utente: '{clean_username}' (ID: {user['id']})"
        )

        return {
            "session_token": session_token,
            "user_id": user["id"],
            "username": user["username"],
            "role_id": user.get("users_roles_id"),
            "permissions": list(permissions),
        }

    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Verifica se un token di sessione inviato è attivo e non scaduto.
        
        Se la sessione è valida, aggiorna l'orario di ultima attività e prologa
        la scadenza (Sliding Expiration), restituendo il profilo utente e i permessi.
        """
        if not session_token:
            return None

        # Recupera e aggiorna la sessione nel DB (touch_activity=True aggiorna last_activity ed expires_at)
        session_data = self.sessions_repo.get_valid_session(
            session_token, touch_activity=True
        )
        if not session_data:
            return None

        user_id = session_data["user_id"]
        
        # Recupera i dettagli dell'utente se non presenti nella sessione
        user = self.users_repo.get_by_id(user_id) if hasattr(self.users_repo, 'get_by_id') else None
        username = user["username"] if user else session_data.get("username", "")

        permissions = self.users_repo.get_effective_permission_codes(user_id)

        return {
            "session_id": session_data["id"],
            "user_id": user_id,
            "username": username,
            "session_token": session_token,
            "expires_at": session_data["expires_at"],
            "ip_address": session_data.get("ip_address"),
            "permissions": set(permissions),
        }

    def has_permission(self, session_token: str, required_permission: str) -> bool:
        """Utility rapida per verificare se una determinata sessione possiede un permesso specifico."""
        session_info = self.validate_session(session_token)
        if not session_info:
            return False
        return required_permission in session_info["permissions"]

    def logout(self, session_token: str) -> bool:
        """Effettua il logout invalidando il token della sessione sul DB (imposta is_active = False)."""
        if not session_token:
            return False
        return self.sessions_repo.invalidate_session(session_token)

    def logout_all_sessions(self, user_id: int) -> bool:
        """Invalida tutte le sessioni attive di un determinato utente."""
        return self.sessions_repo.invalidate_all_user_sessions(user_id)