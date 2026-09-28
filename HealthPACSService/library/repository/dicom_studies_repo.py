# library/repository/dicom_studies_repo.py

from datetime import date, time
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, update, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from library.logger import logger
from library.models.dicom_studies_model import DicomStudiesModel


class DicomStudiesRepo:
    """Repository ORM per le operazioni CRUD e statistiche sulla tabella public.dicom_studies."""

    def __init__(self, db_manager):
        self.db = db_manager

    @staticmethod
    def _to_dict(obj: Optional[DicomStudiesModel]) -> Optional[Dict[str, Any]]:
        """Converte l'istanza ORM in un dizionario Python per la compatibilità con i servizi esistenti."""
        if obj is None:
            return None
        return {
            "id": obj.id,
            "dicom_equipment_id": obj.dicom_equipment_id,
            "patient_id": obj.patient_id,
            "patient_name": obj.patient_name,
            "patient_birth_date": obj.patient_birth_date,
            "patient_sex": obj.patient_sex,
            "study_instance_uid": obj.study_instance_uid,
            "study_date": obj.study_date,
            "study_time": obj.study_time,
            "accession_number": obj.accession_number,
            "study_description": obj.study_description,
            "referring_physician_name": obj.referring_physician_name,
            "modalities_in_study": obj.modalities_in_study,
            "study_size": obj.study_size,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
        }

    # -------------------------------------------------------------------------
    # OPERAZIONI DI LETTURA (READ & QUERY STATISTICHE)
    # -------------------------------------------------------------------------

    def get_by_id(self, study_id: int) -> Optional[Dict[str, Any]]:
        """Recupera uno studio tramite la sua chiave primaria ID."""
        try:
            with self.db.get_session() as session:
                study = session.get(DicomStudiesModel, study_id)
                return self._to_dict(study)
        except Exception as e:
            logger.error(f"DicomStudiesRepo: Errore recupero studio ID {study_id}: {e}")
            return None

    def get_by_study_instance_uid(self, study_instance_uid: str) -> Optional[Dict[str, Any]]:
        """Recupera uno studio tramite il suo Study Instance UID DICOM univoco."""
        try:
            with self.db.get_session() as session:
                stmt = select(DicomStudiesModel).where(
                    DicomStudiesModel.study_instance_uid == study_instance_uid.strip()
                )
                study = session.execute(stmt).scalar_one_or_none()
                return self._to_dict(study)
        except Exception as e:
            logger.error(
                f"DicomStudiesRepo: Errore recupero studio per UID '{study_instance_uid}': {e}"
            )
            return None

    def get_by_equipment_id(
        self, equipment_id: int, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Recupera la lista degli studi inviati da uno specifico Equipment con paginazione."""
        try:
            with self.db.get_session() as session:
                stmt = (
                    select(DicomStudiesModel)
                    .where(DicomStudiesModel.dicom_equipment_id == equipment_id)
                    .order_by(DicomStudiesModel.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
                results = session.execute(stmt).scalars().all()
                return [self._to_dict(study) for study in results]
        except Exception as e:
            logger.error(
                f"DicomStudiesRepo: Errore recupero studi per Equipment ID {equipment_id}: {e}"
            )
            return []

    def count_studies_by_equipment(self, equipment_id: int) -> int:
        """Ritorna il numero totale di studi associati a un determinato Equipment."""
        try:
            with self.db.get_session() as session:
                stmt = select(func.count(DicomStudiesModel.id)).where(
                    DicomStudiesModel.dicom_equipment_id == equipment_id
                )
                count = session.execute(stmt).scalar()
                return count if count is not None else 0
        except Exception as e:
            logger.error(
                f"DicomStudiesRepo: Errore conteggio studi per Equipment ID {equipment_id}: {e}"
            )
            return 0

    # -------------------------------------------------------------------------
    # OPERAZIONI DI INSERIMENTO (INSERT)
    # -------------------------------------------------------------------------

    def create(
        self,
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
        """Registra un nuovo studio DICOM.
        
        Sfrutta ON CONFLICT (study_instance_uid) DO NOTHING per prevenire duplicati.
        """
        try:
            with self.db.get_session() as session:
                stmt = (
                    pg_insert(DicomStudiesModel)
                    .values(
                        study_instance_uid=study_instance_uid.strip(),
                        dicom_equipment_id=dicom_equipment_id,
                        patient_id=patient_id.strip() if patient_id else None,
                        patient_name=patient_name.strip() if patient_name else None,
                        patient_birth_date=patient_birth_date,
                        patient_sex=patient_sex.strip() if patient_sex else None,
                        study_date=study_date,
                        study_time=study_time,
                        accession_number=accession_number.strip() if accession_number else None,
                        study_description=study_description.strip() if study_description else None,
                        referring_physician_name=(
                            referring_physician_name.strip() if referring_physician_name else None
                        ),
                        modalities_in_study=modalities_in_study.strip() if modalities_in_study else None,
                        study_size=study_size,
                    )
                    .on_conflict_do_nothing(index_elements=["study_instance_uid"])
                    .returning(DicomStudiesModel.id)
                )
                result = session.execute(stmt).scalar_one_or_none()
                return result
        except Exception as e:
            logger.error(
                f"DicomStudiesRepo: Errore creazione studio UID '{study_instance_uid}': {e}"
            )
            return None

    # -------------------------------------------------------------------------
    # OPERAZIONI DI AGGIORNAMENTO (UPDATE)
    # -------------------------------------------------------------------------

    def update_study_size(self, study_id: int, additional_bytes: int) -> bool:
        """Incrementa la dimensione in byte dello studio (es. dopo l'aggiunta di nuove istanze/serie)."""
        try:
            with self.db.get_session() as session:
                study = session.get(DicomStudiesModel, study_id)
                if not study:
                    return False

                study.study_size = (study.study_size or 0) + additional_bytes
                return True
        except Exception as e:
            logger.error(
                f"DicomStudiesRepo: Errore aggiornamento dimensione studio ID {study_id}: {e}"
            )
            return False

    # -------------------------------------------------------------------------
    # OPERAZIONI DI CANCELLAZIONE (DELETE)
    # -------------------------------------------------------------------------

    def delete_by_id(self, study_id: int) -> bool:
        """Rimuove uno studio dal database tramite ID."""
        try:
            with self.db.get_session() as session:
                stmt = delete(DicomStudiesModel).where(DicomStudiesModel.id == study_id)
                result = session.execute(stmt)
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"DicomStudiesRepo: Errore cancellazione studio ID {study_id}: {e}")
            return False