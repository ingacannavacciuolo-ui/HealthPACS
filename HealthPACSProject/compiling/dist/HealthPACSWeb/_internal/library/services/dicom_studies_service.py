# library/services/dicom_studies_service.py

from datetime import date, time
from typing import Optional, List, Dict, Any
from library.logger import logger
from library.repository.dicom_studies_repo import DicomStudiesRepo
from library.services.auth_service import AuthService


class DicomStudiesService:
    """Service Layer per la gestione del dominio DICOM Studies con enforcement RBAC."""

    def __init__(self, db_manager):
        self.db = db_manager
        self.auth_service = AuthService(db_manager)
        self.repo = DicomStudiesRepo(db_manager)

    # -------------------------------------------------------------------------
    # OPERAZIONI DI LETTURA (Richiedono 'study:read')
    # -------------------------------------------------------------------------

    def get_study_by_id(self, session_token: str, study_id: int) -> Optional[Dict[str, Any]]:
        """Recupera uno studio tramite ID previa verifica del permesso 'study:read'."""
        if not self.auth_service.has_permission(session_token, "study:read"):
            logger.warning(
                f"DicomStudiesService: Accesso negato 'study:read' per token {session_token[:8]}..."
            )
            raise PermissionError("Accesso Negato: Permesso 'study:read' mancante.")

        return self.repo.get_by_id(study_id)

    def get_study_by_uid(
        self, session_token: str, study_instance_uid: str
    ) -> Optional[Dict[str, Any]]:
        """Recupera uno studio tramite Study Instance UID previa verifica del permesso 'study:read'."""
        if not self.auth_service.has_permission(session_token, "study:read"):
            logger.warning(
                f"DicomStudiesService: Accesso negato 'study:read' per token {session_token[:8]}..."
            )
            raise PermissionError("Accesso Negato: Permesso 'study:read' mancante.")

        return self.repo.get_by_study_instance_uid(study_instance_uid)

    def list_studies_by_equipment(
        self, session_token: str, equipment_id: int, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Elenca gli studi associati a un apparecchio DICOM previa verifica del permesso 'study:read'."""
        if not self.auth_service.has_permission(session_token, "study:read"):
            logger.warning(
                f"DicomStudiesService: Accesso negato 'study:read' per token {session_token[:8]}..."
            )
            raise PermissionError("Accesso Negato: Permesso 'study:read' mancante.")

        return self.repo.get_by_equipment_id(equipment_id, limit=limit, offset=offset)

    def count_studies_by_equipment(self, session_token: str, equipment_id: int) -> int:
        """Conteggia il numero totale di studi per apparecchio previa verifica del permesso 'study:read'."""
        if not self.auth_service.has_permission(session_token, "study:read"):
            logger.warning(
                f"DicomStudiesService: Accesso negato 'study:read' per token {session_token[:8]}..."
            )
            raise PermissionError("Accesso Negato: Permesso 'study:read' mancante.")

        return self.repo.count_studies_by_equipment(equipment_id)

    # -------------------------------------------------------------------------
    # OPERAZIONI DI SCRITTURA / INGESTION (Richiedono 'study:write')
    # -------------------------------------------------------------------------

    def register_study(
        self,
        session_token: str,
        study_instance_uid: str,
        dicom_equipment_id: Optional[int] = None,
        patient_id: Optional[str] = None,
        patient_name: Optional[str] = None,
        patient_birth_date: Optional[date] = None,
        patient_sex: Optional[str] = None,
        study_date: Optional[date] = None,
        study_time: Optional[time] = None,
        accession_number: Optional[str] = None,
        study_description: Optional[str] = None,
        referring_physician_name: Optional[str] = None,
        modalities_in_study: Optional[str] = None,
        study_size: int = 0,
    ) -> Optional[int]:
        """Crea un nuovo record di studio DICOM previa verifica del permesso 'study:write'."""
        if not self.auth_service.has_permission(session_token, "study:write"):
            logger.warning(
                f"DicomStudiesService: Accesso negato 'study:write' per token {session_token[:8]}..."
            )
            raise PermissionError("Accesso Negato: Permesso 'study:write' mancante.")

        return self.repo.create(
            study_instance_uid=study_instance_uid,
            dicom_equipment_id=dicom_equipment_id,
            patient_id=patient_id,
            patient_name=patient_name,
            patient_birth_date=patient_birth_date,
            patient_sex=patient_sex,
            study_date=study_date,
            study_time=study_time,
            accession_number=accession_number,
            study_description=study_description,
            referring_physician_name=referring_physician_name,
            modalities_in_study=modalities_in_study,
            study_size=study_size,
        )

    def increment_study_size(
        self, session_token: str, study_id: int, additional_bytes: int
    ) -> bool:
        """Incrementa la dimensione totale dello studio previa verifica del permesso 'study:write'."""
        if not self.auth_service.has_permission(session_token, "study:write"):
            logger.warning(
                f"DicomStudiesService: Accesso negato 'study:write' per token {session_token[:8]}..."
            )
            raise PermissionError("Accesso Negato: Permesso 'study:write' mancante.")

        return self.repo.update_study_size(study_id=study_id, additional_bytes=additional_bytes)

    # -------------------------------------------------------------------------
    # OPERAZIONI DI ELIMINAZIONE / DELETE (Richiedono 'study:purge')
    # -------------------------------------------------------------------------

    def delete_study(self, session_token: str, study_id: int) -> bool:
        """Elimina uno studio dal sistema tramite ID previa verifica del permesso 'study:purge'."""
        if not self.auth_service.has_permission(session_token, "study:purge"):
            logger.warning(
                f"DicomStudiesService: Accesso negato 'study:purge' per token {session_token[:8]}..."
            )
            raise PermissionError("Accesso Negato: Permesso 'study:purge' (eliminazione) mancante.")

        return self.repo.delete_by_id(study_id)

    def purge_study(self, session_token: str, study_id: int) -> bool:
        """Alias per delete_study per retrocompatibilità."""
        return self.delete_study(session_token=session_token, study_id=study_id)