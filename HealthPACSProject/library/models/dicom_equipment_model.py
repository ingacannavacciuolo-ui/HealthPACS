# library/models/dicom_equipment_model.py

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, BigInteger, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from library.models.base_model import Base

if TYPE_CHECKING:
    from library.models.dicom_scu_model import DicomScuModel
    from library.models.dicom_studies_model import DicomStudiesModel


class DicomEquipmentModel(Base):
    """Mappatura ORM della tabella public.dicom_equipment."""

    __tablename__ = "dicom_equipment"
    __table_args__ = {"schema": "public"}

    # Chiave Primaria (BIGSERIAL)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Campi Dati Equipment (Tag DICOM)
    station_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    institution_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    manufacturer_model_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    device_serial_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    software_versions: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Timestamps di sistema
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Chiave Esterna verso SCU (definita in fondo ai campi)
    scu_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("public.dicom_scu.id", ondelete="SET NULL"),
        nullable=True,
    )

    # RELAZIONI ORM
    scu: Mapped[Optional["DicomScuModel"]] = relationship(
        "DicomScuModel", back_populates="equipments"
    )
    studies: Mapped[List["DicomStudiesModel"]] = relationship(
        "DicomStudiesModel", back_populates="equipment"
    )