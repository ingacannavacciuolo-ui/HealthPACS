# library/models/dicom_equipment_model.py

from datetime import datetime
from typing import Optional
from sqlalchemy import String, BigInteger, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from library.models.base_model import Base
# Importiamo il modello padre per la digitazione e la relazione
from library.models.dicom_scu_model import DicomScuModel


class DicomEquipmentModel(Base):
    """Mappatura ORM della tabella public.dicom_equipment."""

    __tablename__ = "dicom_equipment"
    __table_args__ = {"schema": "public"}

    # id SERIAL / BIGSERIAL -> BigInteger primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # Foreign Key verso public.dicom_scu(id)
    scu_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, 
        ForeignKey("public.dicom_scu.id", ondelete="SET NULL"), 
        nullable=True,
        index=True  # Rispecchia l'indice idx_dicom_equipment_scu_id
    )

    # Campi stringa DICOM
    station_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    institution_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    manufacturer_model_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    device_serial_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    software_versions: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Timestamp gestiti con default e onupdate lato DB/SQLAlchemy
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), 
        server_default=func.current_timestamp(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), 
        server_default=func.current_timestamp(), 
        onupdate=func.current_timestamp(), 
        nullable=False
    )

    # Relazione ORM opzionale verso il modello DicomScuModel (se già esistente)
    scu: Mapped[Optional["DicomScuModel"]] = relationship("DicomScuModel")