# library/api/rest/dicom_studies_rest.py

from typing import List, Optional
from fastapi import APIRouter, Header, HTTPException, Depends, Query, Request
from library.services.dicom_studies_service import DicomStudiesService

router = APIRouter(prefix="/api/v1/studies", tags=["Studies REST"])


def extract_token(authorization: str = Header(...)) -> str:
    """Estrae il Bearer Token dall'header HTTP Authorization."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Header Authorization non valido. Usare 'Bearer <token>'",
        )
    return authorization.replace("Bearer ", "").strip()


def get_service(request: Request) -> DicomStudiesService:
    """Recupera il dbmanager salvato nell'app FastAPI e istanzia il servizio."""
    dbmanager = request.app.state.dbmanager
    return DicomStudiesService(db_manager=dbmanager)


@router.get("/{study_id}")
def get_study_by_id(
    study_id: int,
    token: str = Depends(extract_token),
    service: DicomStudiesService = Depends(get_service),
):
    """GET /api/v1/studies/{study_id} - Recupera uno studio tramite il suo ID primario."""
    try:
        study = service.get_study_by_id(session_token=token, study_id=study_id)
        if not study:
            raise HTTPException(
                status_code=404, detail=f"Studio con ID {study_id} non trovato."
            )
        return study
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/uid/{study_instance_uid}")
def get_study_by_uid(
    study_instance_uid: str,
    token: str = Depends(extract_token),
    service: DicomStudiesService = Depends(get_service),
):
    """GET /api/v1/studies/uid/{study_instance_uid} - Recupera uno studio tramite StudyInstanceUID."""
    try:
        study = service.get_study_by_uid(
            session_token=token, study_instance_uid=study_instance_uid
        )
        if not study:
            raise HTTPException(status_code=404, detail="Studio DICOM non trovato.")
        return study
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/equipment/{equipment_id}")
def list_studies_by_equipment(
    equipment_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    token: str = Depends(extract_token),
    service: DicomStudiesService = Depends(get_service),
):
    """GET /api/v1/studies/equipment/{equipment_id} - Elenca gli studi per macchinario DICOM."""
    try:
        studies = service.list_studies_by_equipment(
            session_token=token, equipment_id=equipment_id, limit=limit, offset=offset
        )
        total = service.count_studies_by_equipment(
            session_token=token, equipment_id=equipment_id
        )
        return {"total": total, "limit": limit, "offset": offset, "data": studies}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{study_id}")
def delete_study(
    study_id: int,
    token: str = Depends(extract_token),
    service: DicomStudiesService = Depends(get_service),
):
    """DELETE /api/v1/studies/{study_id} - Elimina uno studio dal sistema."""
    try:
        deleted = service.delete_study(session_token=token, study_id=study_id)
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Impossibile eliminare: studio ID {study_id} non trovato.",
            )
        return {
            "status": "success",
            "message": f"Studio {study_id} eliminato con successo.",
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))