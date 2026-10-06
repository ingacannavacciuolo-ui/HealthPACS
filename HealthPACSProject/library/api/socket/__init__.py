from .dicom_studies_socket import router as studies_socket_router
from .web_router_socket import router as web_router_socket

__all__ = [
    "studies_socket_router",
    "web_router_socket",
]