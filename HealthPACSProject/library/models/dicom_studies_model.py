# library/models/dicom_studies_model.py

from datetime import date, time, datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, BigInteger, Date, Time, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from library.models.base_model import Base

if TYPE_CHECKING:
    from library.models.dicom_equipment_model import DicomEquipmentModel
    from library.models.dicom_series_model import DicomSeriesModel


class DicomStudiesModel(Base):
    """Mappatura ORM della tabella public.dicom_studies."""

    __tablename__ = "dicom_studies"
    __table_args__ = {"schema": "public"}

    # Chiave Primaria
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Identificativo Univoco DICOM (0020, 000D)
    study_instance_uid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    # Dati Paziente (Tag DICOM Group 0010)
    patient_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    patient_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    patient_birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    patient_sex: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    # Dati Studio DICOM (Tag DICOM Group 0008)
    study_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    study_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    accession_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    study_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    referring_physician_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    modalities_in_study: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Dimensione dello studio
    study_size: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    # Timestamps di sistema
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Chiave Esterna verso Equipment
    dicom_equipment_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("public.dicom_equipment.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relazioni ORM
    equipment: Mapped[Optional["DicomEquipmentModel"]] = relationship(
        "DicomEquipmentModel", back_populates="studies"
    )
    series: Mapped[List["DicomSeriesModel"]] = relationship(
        "DicomSeriesModel", back_populates="study"
    )