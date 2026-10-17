# library/api/web/pages_router.py

import os
import sys
from typing import Optional
from fastapi import APIRouter, Request, Form, Response, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from library.constant_health_pacs import (
    NOTIFY_ERROR,
    )

from library.services.auth_service import AuthService
from library.api import get_auth_service, get_current_user_session, setup_template_globals

router = APIRouter(tags=["Web Pages"])

# Determinazione della cartella templates
if getattr(sys, 'frozen', False):
    # In modalità compilata (PyInstaller), la cartella templates si trova nella radice di sys._MEIPASS
    templates_dir = os.path.join(sys._MEIPASS, "templates")
else:
    # In modalità sviluppo (.py), risale da library/api/web fino alla radice del progetto
    base_path = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.abspath(os.path.join(base_path, "..", "..", "..", "templates"))

templates = Jinja2Templates(directory=templates_dir)
# Registrazione globale delle costanti per tutti i template HTML
setup_template_globals(templates)


 # 204 No Content: dice al browser che l'icona non c'è, senza generare errori 404
@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204) 


#Mostra la pagina di login. Se la sessione è già valida, reindirizza a /querystudies.    
@router.get("/",  response_class=HTMLResponse)
async def login_page(request: Request, 
                     reason: Optional[str] = None,
                     auth_service: AuthService = Depends(get_auth_service)):
    
    token = request.cookies.get("session_token")
    if token and auth_service.validate_session(token):
        return RedirectResponse(url="/querystudies", status_code=status.HTTP_302_FOUND)

    context = {"title": "HealthPACS Web - Login"}

   # Distinzione precisa tra Token Mancante e Sessione Scaduta
    if reason == NOTIFY_ERROR["MISSING_TOKEN"]:
        context["missing_token_alert"] = True
        context["missing_token_message"] = "Autenticazione richiesta. Effettuare il login per accedere."
    elif reason == NOTIFY_ERROR["SESSION_EXPIRED"]:
        context["session_expired_alert"] = True
        context["session_expired_message"] = "Sessione scaduta per inattività. Effettuare nuovamente il login."

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context=context
    )


@router.post("/login")
async def do_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    auth_service: AuthService = Depends(get_auth_service)
):
    client_ip = request.client.host if request.client else "0.0.0.0"
    user_agent = request.headers.get("User-Agent", "Web-Browser")

    # AuthService salverà i metadati su app_users_sessions
    auth_result, error_code = auth_service.login(
        username=username,
        password_plain=password,
        ip_address=client_ip,
        user_agent=user_agent
    )

    # CASO 1: Credenziali errate -> Errore rosso dentro la card di login
    if error_code == NOTIFY_ERROR["LOGIN_BAD_CREDENTIALS"]:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "title": "HealthPACS Web - Login",
                "bad_credential_alert": True,
                "bad_credential_message": "Credenziali non valide."
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # CASO 2: Utente disabilitato -> Scatena la card d'allerta arancione
    if error_code == NOTIFY_ERROR["LOGIN_UNAUTHORIZED"]:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "title": "HealthPACS Web - Login",
                "unauthorized_alert": True,
                "unauthorized_message": "Utente non autorizzato ad accedere al sistema."
            },
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    session_token = auth_result["session_token"]

    redirect_response = RedirectResponse(url="/querystudies", status_code=status.HTTP_303_SEE_OTHER)
    redirect_response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=False
    )
    return redirect_response


@router.get("/logout")
async def logout(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Invalida la sessione sul DB ed elimina il cookie dal client."""
    token = request.cookies.get("session_token")
    if token:
        auth_service.logout(token)

    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("session_token")
    return response


@router.get("/querystudies", response_class=HTMLResponse)
async def query_studies_page(
    request: Request,
    user: dict = Depends(get_current_user_session)
):
    return templates.TemplateResponse(
        request=request,
        name="querystudies.html",
        context={
            "user": user
        }
    )


@router.get("/api/v1/studies")
async def get_studies(user: dict = Depends(get_current_user_session)):
    # Se la sessione è valida torna i dati, altrimenti get_current_user_session lancia il 401 (detail="session_expired")
    return {"status": "ok", "data": []}