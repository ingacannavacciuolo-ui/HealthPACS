# library/api/web/dependencies.py

from typing import Dict, Any
from fastapi import Request, HTTPException, status, Depends
from library.services.auth_service import AuthService
from library.constant_health_pacs import (
    NOTIFY_ERROR,
)


def get_auth_service(request: Request) -> AuthService:
    """Istanzia AuthService utilizzando il DatabaseManager presente nello stato dell'app."""
    return AuthService(request.app.state.dbmanager)


async def get_current_user_session(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """
    Dipendenza FastAPI per proteggere le rotte web.
    
    Estrae il cookie 'session_token', ne esegue la validazione e il rinnovo 
    su app_users_sessions e restituisce i dettagli dell'utente con i permessi.
    """
    token = request.cookies.get("session_token")

    # Fallback per chiamate API con header Authorization: Bearer <token>
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

   # CASO 1: Token di sessione assente
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail= NOTIFY_ERROR["MISSING_TOKEN"]
        )

    # CASO 2: Token inviato ma sessione scaduta sul DB
    session_info = auth_service.validate_session(token)
    if not session_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=NOTIFY_ERROR["SESSION_EXPIRED"]
        )

    return session_info