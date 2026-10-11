# library/models/dicom_series_model.py

from datetime import date, time, datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, BigInteger, Date, Time, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from library.models.base_model import Base

if TYPE_CHECKING:
    from library.models.dicom_studies_model import DicomStudiesModel


class DicomSeriesModel(Base):
    """Mappatura ORM della tabella public.dicom_series."""

    __tablename__ = "dicom_series"
    __table_args__ = {"schema": "public"}

    # Chiave Primaria
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Tag DICOM della Serie
    series_instance_uid: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    series_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    modality: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    series_description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    body_part_examined: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    patient_position: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    series_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    series_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)

    # Timestamps di sistema
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Chiave Esterna verso lo Studio (posizionata come ultimo campo di colonna)
    study_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("public.dicom_studies.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relazione ORM verso lo Studio
    study: Mapped["DicomStudiesModel"] = relationship(
        "DicomStudiesModel", back_populates="series"
    )

    # In DicomSeriesModel
    instances = relationship("DicomInstancesModel", back_populates="series", cascade="all, delete-orphan")