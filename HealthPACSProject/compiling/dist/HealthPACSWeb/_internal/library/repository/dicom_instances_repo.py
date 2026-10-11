# library/repository/dicom_instances_repo.py

from typing import Optional, Dict, Any, List
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from library.models import DicomInstancesModel
from library.logger import logger


class DicomInstancesRepo:
    """
    Repository ORM per le operazioni CRUD sulla tabella public.dicom_instances.
    """

    def __init__(self, db_manager):
        self.db = db_manager

    @staticmethod
    def _to_dict(obj: Optional[DicomInstancesModel]) -> Optional[Dict[str, Any]]:
        """Converte l'istanza ORM in un dizionario Python."""
        if obj is None:
            return None
        return obj.to_dict()

    def get_by_sop_instance_uid(self, sop_instance_uid: str) -> Optional[Dict[str, Any]]:
        """Recupera un'istanza tramite il suo SOPInstanceUID."""
        try:
            with self.db.get_session() as session:
                stmt = select(DicomInstancesModel).where(
                    DicomInstancesModel.sop_instance_uid == sop_instance_uid.strip()
                )
                instance = session.execute(stmt).scalar_one_or_none()
                return self._to_dict(instance)
        except SQLAlchemyError as e:
            logger.error(f"[InstancesRepo] Errore get_by_sop_instance_uid ({sop_instance_uid}): {e}")
            return None

    def get_by_series_id(self, series_id: int) -> List[Dict[str, Any]]:
        """Recupera tutte le istanze appartenenti a una determinata serie."""
        try:
            with self.db.get_session() as session:
                stmt = select(DicomInstancesModel).where(
                    DicomInstancesModel.series_id == series_id
                )
                results = session.execute(stmt).scalars().all()
                return [self._to_dict(inst) for inst in results]
        except SQLAlchemyError as e:
            logger.error(f"[InstancesRepo] Errore get_by_series_id ({series_id}): {e}")
            return []

    def create_or_update(self, instance_data: Dict[str, Any]) -> Optional[int]:
        """
        Inserisce una nuova istanza DICOM o la aggiorna se il sop_instance_uid esiste già.
        
        :param instance_data: Dizionario contenente i campi dell'istanza
        :return: ID dell'istanza salvata o None in caso di errore
        """
        sop_instance_uid = instance_data.get("sop_instance_uid")
        if not sop_instance_uid:
            logger.error("[InstancesRepo] Impossibile creare/aggiornare l'istanza: 'sop_instance_uid' mancante.")
            return None

        try:
            with self.db.get_session() as session:
                stmt = select(DicomInstancesModel).where(
                    DicomInstancesModel.sop_instance_uid == sop_instance_uid.strip()
                )
                instance = session.execute(stmt).scalar_one_or_none()

                if instance:
                    # Aggiornamento dati esistenti
                    instance.series_id = instance_data.get("series_id", instance.series_id)
                    instance.sop_class_uid = instance_data.get("sop_class_uid", instance.sop_class_uid)
                    instance.instance_number = instance_data.get("instance_number", instance.instance_number)
                    instance.transfer_syntax_uid = instance_data.get("transfer_syntax_uid", instance.transfer_syntax_uid)
                    instance.file_path = instance_data.get("file_path", instance.file_path)
                    instance.file_size = instance_data.get("file_size", instance.file_size)
                    logger.info(f"[InstancesRepo] Aggiornata istanza esistente [ID: {instance.id}, SOP: {sop_instance_uid}]")
                else:
                    # Creazione nuova istanza
                    instance = DicomInstancesModel(
                        series_id=instance_data["series_id"],
                        sop_instance_uid=sop_instance_uid.strip(),
                        sop_class_uid=instance_data.get("sop_class_uid"),
                        instance_number=instance_data.get("instance_number"),
                        transfer_syntax_uid=instance_data.get("transfer_syntax_uid"),
                        file_path=instance_data["file_path"],
                        file_size=instance_data.get("file_size", 0)
                    )
                    session.add(instance)
                    logger.info(f"[InstancesRepo] Creata nuova istanza [SOP: {sop_instance_uid}]")

                session.commit()
                return instance.id

        except SQLAlchemyError as e:
            logger.error(f"[InstancesRepo] Errore salvataggio istanza ({sop_instance_uid}): {e}", exc_info=True)
            return None