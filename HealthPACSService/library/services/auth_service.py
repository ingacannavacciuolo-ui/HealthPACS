# library/services/auth_service.py

import secrets
from typing import Optional, Dict, Any
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from library.logger import logger
from library.repository.app_users_repo import AppUsersRepo
from library.repository.app_users_sessions_repo import AppUsersSessionsRepo


class AuthService:
    """Servizio per la gestione di Login, Logout e Validazione Sessione/Permessi."""

    def __init__(self, db_manager):
        self.db = db_manager
        self.users_repo = AppUsersRepo(db_manager)
        self.sessions_repo = AppUsersSessionsRepo(db_manager)
        self.ph = PasswordHasher()

    def login(
        self,
        username: str,
        password_plain: str,
        duration_minutes: int = 480,  # 8 ore di validità predefinita
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Esegue il flusso di autenticazione completo:
        
        1. Cerca l'utente per username e ne verifica lo stato (is_active).
        2. Verifica l'hash Argon2id della password fornita.
        3. Calcola l'insieme dei permessi effettivi dell'utente (Ruolo + Overrides).
        4. Genera un token crittograficamente sicuro e registra la sessione a DB.
        """
        clean_username = username.strip()

        # 1. Recupera l'utente
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

        # 2. Verifica hash della password
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

        # 3. Generazione Token di Sessione Unico (64 caratteri esadecimali)
        session_token = secrets.token_hex(32)

        # 4. Registrazione della sessione sul database
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

        # 5. Calcolo permessi effettivi (Ruolo + Exceptions)
        permissions = self.users_repo.get_effective_permission_codes(user["id"])

        logger.info(
            f"AuthService: Login eseguito con successo. Utente: '{clean_username}' (ID: {user['id']})"
        )

        return {
            "session_token": session_token,
            "user_id": user["id"],
            "username": user["username"],
            "role_id": user["users_roles_id"],
            "permissions": list(permissions),
        }

    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Verifica se un token inviato è attivo e valido.
        
        Se la sessione è valida, aggiorna l'orario di ultima attività (sliding expiration)
        e restituisce il profilo utente aggiornato con i relativi permessi.
        """
        session_data = self.sessions_repo.get_valid_session(
            session_token, touch_activity=True
        )
        if not session_data:
            return None

        user_id = session_data["user_id"]
        permissions = self.users_repo.get_effective_permission_codes(user_id)

        return {
            "session_id": session_data["id"],
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": session_data["expires_at"],
            "permissions": set(permissions),
        }

    def has_permission(self, session_token: str, required_permission: str) -> bool:
        """Utility rapida per verificare se una determinata sessione possiede un permesso specifico."""
        session_info = self.validate_session(session_token)
        if not session_info:
            return False
        return required_permission in session_info["permissions"]

    def logout(self, session_token: str) -> bool:
        """Effettua il logout invalidando il token della sessione nel DB."""
        return self.sessions_repo.invalidate_session(session_token)

    def logout_all_sessions(self, user_id: int) -> bool:
        """Invalida tutte le sessioni attive di un determinato utente."""
        return self.sessions_repo.invalidate_all_user_sessions(user_id)