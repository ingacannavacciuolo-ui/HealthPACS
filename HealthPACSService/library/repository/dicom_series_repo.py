from datetime import date, time
from typing import Optional, List, Dict, Any
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from library.logger import logger
from library.models import DicomSeriesModel


class DicomSeriesRepo:
    """Repository ORM per le operazioni CRUD sulla tabella public.dicom_series."""

    def __init__(self, db_manager):
        self.db = db_manager

    @staticmethod
    def _to_dict(obj: Optional[DicomSeriesModel]) -> Optional[Dict[str, Any]]:
        """Converte l'istanza ORM in un dizionario Python per isolare il layer dati."""
        if obj is None:
            return None
        return {
            "id": obj.id,
            "study_id": obj.study_id,
            "series_instance_uid": obj.series_instance_uid,
            "series_number": obj.series_number,
            "modality": obj.modality,
            "series_description": obj.series_description,
            "body_part_examined": obj.body_part_examined,
            "patient_position": obj.patient_position,
            "series_date": obj.series_date,
            "series_time": obj.series_time,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
        }

    # -------------------------------------------------------------------------
    # OPERAZIONI DI LETTURA (READ)
    # -------------------------------------------------------------------------

    def get_by_id(self, series_id: int) -> Optional[Dict[str, Any]]:
        """Recupera una serie tramite la sua chiave primaria ID."""
        try:
            with self.db.get_session() as session:
                series = session.get(DicomSeriesModel, series_id)
                return self._to_dict(series)
        except Exception as e:
            logger.error(f"DicomSeriesRepo: Errore recupero serie ID {series_id}: {e}")
            return None

    def get_by_series_instance_uid(self, series_instance_uid: str) -> Optional[Dict[str, Any]]:
        """Recupera una serie tramite il suo Series Instance UID."""
        try:
            with self.db.get_session() as session:
                stmt = select(DicomSeriesModel).where(
                    DicomSeriesModel.series_instance_uid == series_instance_uid.strip()
                )
                series = session.execute(stmt).scalar_one_or_none()
                return self._to_dict(series)
        except Exception as e:
            logger.error(
                f"DicomSeriesRepo: Errore recupero serie per UID '{series_instance_uid}': {e}"
            )
            return None

    def get_by_study_id(self, study_id: int) -> List[Dict[str, Any]]:
        """Recupera la lista delle serie ordinate per numero di serie associate a uno Studio."""
        try:
            with self.db.get_session() as session:
                stmt = (
                    select(DicomSeriesModel)
                    .where(DicomSeriesModel.study_id == study_id)
                    .order_by(DicomSeriesModel.series_number.asc().nulls_last())
                )
                results = session.execute(stmt).scalars().all()
                return [self._to_dict(s) for s in results]
        except Exception as e:
            logger.error(
                f"DicomSeriesRepo: Errore recupero serie per Study ID {study_id}: {e}"
            )
            return []

    # -------------------------------------------------------------------------
    # OPERAZIONI DI INSERIMENTO (INSERT)
    # -------------------------------------------------------------------------

    def create(
        self,
        study_id: int,
        series_instance_uid: str,
        series_number: Optional[int] = None,
        modality: Optional[str] = None,
        series_description: Optional[str] = None,
        body_part_examined: Optional[str] = None,
        patient_position: Optional[str] = None,
        series_date: Optional[date] = None,
        series_time: Optional[time] = None,
    ) -> Optional[int]:
        """Registra una nuova serie DICOM.
        
        Garantisce l'idempotenza tramite ON CONFLICT (series_instance_uid) DO NOTHING.
        """
        try:
            with self.db.get_session() as session:
                stmt = (
                    pg_insert(DicomSeriesModel)
                    .values(
                        study_id=study_id,
                        series_instance_uid=series_instance_uid.strip(),
                        series_number=series_number,
                        modality=modality.strip() if modality else None,
                        series_description=(
                            series_description.strip() if series_description else None
                        ),
                        body_part_examined=(
                            body_part_examined.strip() if body_part_examined else None
                        ),
                        patient_position=(
                            patient_position.strip() if patient_position else None
                        ),
                        series_date=series_date,
                        series_time=series_time,
                    )
                    .on_conflict_do_nothing(index_elements=["series_instance_uid"])
                    .returning(DicomSeriesModel.id)
                )
                result = session.execute(stmt).scalar_one_or_none()
                return result
        except Exception as e:
            logger.error(
                f"DicomSeriesRepo: Errore creazione serie UID '{series_instance_uid}': {e}"
            )
            return None

    # -------------------------------------------------------------------------
    # OPERAZIONI DI CANCELLAZIONE (DELETE)
    # -------------------------------------------------------------------------

    def delete_by_id(self, series_id: int) -> bool:
        """Rimuove una serie dal database tramite ID."""
        try:
            with self.db.get_session() as session:
                stmt = delete(DicomSeriesModel).where(DicomSeriesModel.id == series_id)
                result = session.execute(stmt)
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"DicomSeriesRepo: Errore cancellazione serie ID {series_id}: {e}")
            return False