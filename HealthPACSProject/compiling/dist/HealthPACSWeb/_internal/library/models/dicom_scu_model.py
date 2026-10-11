# library/models/dicom_scu_model.py

from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, Text, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from library.models.base_model import Base

if TYPE_CHECKING:
    from library.models.dicom_equipment_model import DicomEquipmentModel


class DicomScuModel(Base):
    """Mappatura ORM della tabella public.dicom_scu."""

    __tablename__ = "dicom_scu"
    __table_args__ = {"schema": "public"}

    # Chiave Primaria
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Identificativi e Connettività
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    aetitle: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    ipaddress: Mapped[str] = mapped_column(String(20), nullable=False)
    port: Mapped[int] = mapped_column(Integer, default=104, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Capability SOP Classes (Flag Booleani)
    sop_echo: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True)
    sop_store: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True)
    sop_find: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True)
    sop_move: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True)
    sop_get: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True)
    sop_worklist: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True)
    sop_print: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True)

    # Relazione ORM verso l'Equipment collegato
    equipments: Mapped[List["DicomEquipmentModel"]] = relationship(
        "DicomEquipmentModel", back_populates="scu"
    )