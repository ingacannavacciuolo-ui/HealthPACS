# library/models/dicom_scp_model.py

from sqlalchemy import String, Integer, BigInteger, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from library.models.base_model import Base


class DicomScpModel(Base):
    """Mappatura ORM della tabella public.dicom_scp."""

    __tablename__ = "dicom_scp"
    __table_args__ = (
        CheckConstraint(
            "porta_locale > 0 AND porta_locale <= 65535", name="chk_porta_locale"
        ),
        {"schema": "public"},
    )

    # Chiave Primaria
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Configurazione Entità SCP
    ae_title: Mapped[str] = mapped_column(String(16), nullable=False)
    porta_locale: Mapped[int] = mapped_column(Integer, nullable=False)
    max_len_pdu: Mapped[int] = mapped_column(Integer, nullable=False)

    # Impostazioni Timeout di Rete
    network_timeout: Mapped[int] = mapped_column(Integer, default=30)
    acse_timeout: Mapped[int] = mapped_column(Integer, default=30)
    dimse_timeout: Mapped[int] = mapped_column(Integer, default=30)