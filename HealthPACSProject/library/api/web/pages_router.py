# library/api/web/pages_router.py

import os
import sys
from fastapi import APIRouter, Request, Form, Response, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from library.services.auth_service import AuthService
from library.api.web.dependencies import get_auth_service

router = APIRouter(tags=["Web Pages"])

# Risale dal folder library/api/web fino alla radice per trovare templates/
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.abspath(os.path.join(base_path, "..", "..", "..", "templates"))
templates = Jinja2Templates(directory=templates_dir)


@router.get("/", response_class=HTMLResponse)
async def login_page(request: Request, auth_service: AuthService = Depends(get_auth_service)):
    """Mostra la pagina di login. Se la sessione è già valida, reindirizza alla home/login."""
    token = request.cookies.get("session_token")
    if token and auth_service.validate_session(token):
        # In futuro reindirizzerà alla pagina principale (es. /querystudies o /worksstudies)
        pass

    return templates.TemplateResponse("login.html", {"request": request, "title": "HealthPACS Web - Login"})


@router.post("/login")
async def do_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    auth_service: AuthService = Depends(get_auth_service)
):
    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("User-Agent", "Web-Browser")

    # AuthService salverà i metadati su app_users_sessions
    auth_result = auth_service.login(
        username=username,
        password_plain=password,
        ip_address=client_ip,
        user_agent=user_agent
    )

    if not auth_result:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Credenziali non valide."},
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    session_token = auth_result["session_token"]

    redirect_response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
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