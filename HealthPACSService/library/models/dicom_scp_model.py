# library/models/dicom_scp.py

from sqlalchemy import String, Integer, CheckConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from library.models.base_model import Base

class DicomScpModel(Base):
    __tablename__ = "dicom_scp"
    __table_args__ = (
        CheckConstraint("porta_locale > 0 AND porta_locale <= 65535", name="chk_porta_locale"),
        {"schema": "public"}
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ae_title: Mapped[str] = mapped_column(String(16), nullable=False)
    porta_locale: Mapped[int] = mapped_column(Integer, nullable=False)
    max_len_pdu: Mapped[int] = mapped_column(Integer, nullable=False)
    network_timeout: Mapped[int] = mapped_column(Integer, default=30)
    acse_timeout: Mapped[int] = mapped_column(Integer, default=30)
    dimse_timeout: Mapped[int] = mapped_column(Integer, default=30)