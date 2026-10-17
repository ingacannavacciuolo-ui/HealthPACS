from fastapi.templating import Jinja2Templates
from library.constant_health_pacs import (
    SOCKET_NAMESPACES, 
    SOCKET_EVENTS, 
    SERVICE_STATUS_STATES,
    NOTIFY_SEVERITY,
    NOTIFY_ERROR
)

def setup_template_globals(templates: Jinja2Templates) -> None:
    """Registra tutte le costanti globali disponibili per i template Jinja2."""
    templates.env.globals.update({
        "SOCKET_NAMESPACES": SOCKET_NAMESPACES,
        "SOCKET_EVENTS": SOCKET_EVENTS,
        "SERVICE_STATUS_STATES": SERVICE_STATUS_STATES,
        "NOTIFY_SEVERITY": NOTIFY_SEVERITY,
        "NOTIFY_ERROR": NOTIFY_ERROR,
    })