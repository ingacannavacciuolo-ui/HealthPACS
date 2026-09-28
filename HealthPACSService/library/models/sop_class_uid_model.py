# library/models/sop_class_uid_model.py

from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from library.models.base_model import Base


class SopClassUidModel(Base):
    """Mappatura ORM della tabella public.sop_class_uid."""

    __tablename__ = "sop_class_uid"
    __table_args__ = {"schema": "public"}

    # Chiave Primaria
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Campi
    uid: Mapped[str] = mapped_column(String(64), nullable=False)
    uid_description: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    service_type: Mapped[str] = mapped_column(String(20), nullable=False)