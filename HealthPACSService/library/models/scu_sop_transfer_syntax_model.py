# library/models/scu_sop_transfer_syntax_model.py

from typing import Optional
from sqlalchemy import Integer, BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from library.models.base_model import Base
from library.models.dicom_scu_model import DicomScuModel


class ScuSopTransferSyntaxModel(Base):
    """Mappatura ORM della tabella associazione public.scu_sop_transfer_syntax."""

    __tablename__ = "scu_sop_transfer_syntax"
    __table_args__ = (
        UniqueConstraint(
            "dicom_scu_id",
            "sop_class_uid_id",
            "transfer_syntax_uid_id",
            name="unique_scu_sop_ts",
        ),
        {"schema": "public"},
    )

    # Chiave primaria
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Chiavi Esterne
    dicom_scu_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("public.dicom_scu.id", ondelete="CASCADE"),
        nullable=False,
    )
    sop_class_uid_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("public.sop_class_uid.id", ondelete="CASCADE"),
        nullable=False,
    )
    transfer_syntax_uid_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("public.transfer_syntax_uid.id", ondelete="CASCADE"),
        nullable=False,
    )

    # RELAZIONI MONODIREZIONALI (Opzionali, utili per caricare i dettagli in JOIN)
    #scu: Mapped["DicomScuModel"] = relationship("DicomScuModel", back_populates="sop_transfer_syntaxes"
    #)
    #sop_class: Mapped["SopClassUidModel"] = relationship("SopClassUidModel")
    # transfer_syntax: Mapped["TransferSyntaxUidModel"] = relationship("TransferSyntaxUidModel")