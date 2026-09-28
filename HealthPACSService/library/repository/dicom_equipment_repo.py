# library/repository/dicom_equipment_repo.py

from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_
from library.logger import logger
from library.models.dicom_equipment_model import DicomEquipmentModel

class DicomEquipmentRepo:
    """Repository per le operazioni CRUD sulla tabella public.dicom_equipment."""

    def __init__(self, db_manager):
        self.db = db_manager

    @staticmethod
    def _to_dict(obj: Optional[DicomEquipmentModel]) -> Optional[Dict[str, Any]]:
        """Converte l'istanza ORM in un dizionario Python per la compatibilità con i servizi esterni."""
        if obj is None:
            return None
        return {
            "id": obj.id,
            "scu_id": obj.scu_id,
            "station_name": obj.station_name,
            "manufacturer": obj.manufacturer,
            "institution_name": obj.institution_name,
            "manufacturer_model_name": obj.manufacturer_model_name,
            "device_serial_number": obj.device_serial_number,
            "software_versions": obj.software_versions,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
        }

    # -------------------------------------------------------------------------
    # OPERAZIONI DI LETTURA (READ)
    # -------------------------------------------------------------------------

    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Recupera tutti i record di apparecchiature con paginazione."""
        try:
            with self.db.get_session() as session:
                stmt = (
                    select(DicomEquipmentModel)
                    .order_by(DicomEquipmentModel.id.desc())
                    .limit(limit)
                    .offset(offset)
                )
                results = session.execute(stmt).scalars().all()
                return [self._to_dict(eq) for eq in results]
        except Exception as e:
            logger.error(f"DicomEquipmentRepo: Errore durante il recupero delle apparecchiature: {e}")
            return []

    def get_by_id(self, equipment_id: int) -> Optional[Dict[str, Any]]:
        """Recupera una specifica apparecchiatura tramite il suo ID primario."""
        try:
            with self.db.get_session() as session:
                equipment = session.get(DicomEquipmentModel, equipment_id)
                return self._to_dict(equipment)
        except Exception as e:
            logger.error(f"DicomEquipmentRepo: Errore durante il recupero dell'equipment ID {equipment_id}: {e}")
            return None

    def get_by_scu_id(self, scu_id: int) -> List[Dict[str, Any]]:
        """Recupera tutte le apparecchiature collegate a un determinato client SCU."""
        try:
            with self.db.get_session() as session:
                stmt = (
                    select(DicomEquipmentModel)
                    .where(DicomEquipmentModel.scu_id == scu_id)
                    .order_by(DicomEquipmentModel.id.asc())
                )
                results = session.execute(stmt).scalars().all()
                return [self._to_dict(eq) for eq in results]
        except Exception as e:
            logger.error(f"DicomEquipmentRepo: Errore durante il recupero equipment per SCU ID {scu_id}: {e}")
            return []

    def find_matching_equipment(
        self,
        station_name: Optional[str] = None,
        manufacturer: Optional[str] = None,
        device_serial_number: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Cerca un record equipment che corrisponda esattamente alle specifiche hardware DICOM."""
        conditions = []

        if station_name:
            conditions.append(DicomEquipmentModel.station_name == station_name.strip())
        if manufacturer:
            conditions.append(DicomEquipmentModel.manufacturer == manufacturer.strip())
        if device_serial_number:
            conditions.append(DicomEquipmentModel.device_serial_number == device_serial_number.strip())

        if not conditions:
            return None

        try:
            with self.db.get_session() as session:
                stmt = (
                    select(DicomEquipmentModel)
                    .where(and_(*conditions))
                    .limit(1)
                )
                equipment = session.execute(stmt).scalar_one_or_none()
                return self._to_dict(equipment)
        except Exception as e:
            logger.error(f"DicomEquipmentRepo: Errore durante la ricerca equipment personalizzata: {e}")
            return None

    # -------------------------------------------------------------------------
    # OPERAZIONI DI INSERIMENTO (INSERT)
    # -------------------------------------------------------------------------

    def create(
        self,
        scu_id: Optional[int] = None,
        station_name: Optional[str] = None,
        manufacturer: Optional[str] = None,
        institution_name: Optional[str] = None,
        manufacturer_model_name: Optional[str] = None,
        device_serial_number: Optional[str] = None,
        software_versions: Optional[str] = None,
    ) -> Optional[int]:
        """Inserisce un nuovo record di apparecchiatura DICOM."""
        try:
            with self.db.get_session() as session:
                equipment = DicomEquipmentModel(
                    scu_id=scu_id,
                    station_name=station_name.strip() if station_name else None,
                    manufacturer=manufacturer.strip() if manufacturer else None,
                    institution_name=institution_name.strip() if institution_name else None,
                    manufacturer_model_name=manufacturer_model_name.strip() if manufacturer_model_name else None,
                    device_serial_number=device_serial_number.strip() if device_serial_number else None,
                    software_versions=software_versions.strip() if software_versions else None,
                )
                session.add(equipment)
                session.flush()
                return equipment.id
        except Exception as e:
            logger.error(f"DicomEquipmentRepo: Errore durante la creazione dell'equipment: {e}")
            return None

    # -------------------------------------------------------------------------
    # OPERAZIONI DI AGGIORNAMENTO (UPDATE)
    # -------------------------------------------------------------------------

    def update(
        self,
        equipment_id: int,
        scu_id: Optional[int] = None,
        station_name: Optional[str] = None,
        manufacturer: Optional[str] = None,
        institution_name: Optional[str] = None,
        manufacturer_model_name: Optional[str] = None,
        device_serial_number: Optional[str] = None,
        software_versions: Optional[str] = None,
    ) -> bool:
        """Aggiorna i campi di una specifica apparecchiatura."""
        try:
            with self.db.get_session() as session:
                equipment = session.get(DicomEquipmentModel, equipment_id)
                if not equipment:
                    return False

                updated = False
                if scu_id is not None:
                    equipment.scu_id = scu_id
                    updated = True
                if station_name is not None:
                    equipment.station_name = station_name.strip()
                    updated = True
                if manufacturer is not None:
                    equipment.manufacturer = manufacturer.strip()
                    updated = True
                if institution_name is not None:
                    equipment.institution_name = institution_name.strip()
                    updated = True
                if manufacturer_model_name is not None:
                    equipment.manufacturer_model_name = manufacturer_model_name.strip()
                    updated = True
                if device_serial_number is not None:
                    equipment.device_serial_number = device_serial_number.strip()
                    updated = True
                if software_versions is not None:
                    equipment.software_versions = software_versions.strip()
                    updated = True

                # Il campo 'updated_at' si aggiorna in automatico lato DB/ORM grazie a onupdate
                return updated
        except Exception as e:
            logger.error(f"DicomEquipmentRepo: Errore durante l'aggiornamento dell'equipment ID {equipment_id}: {e}")
            return False