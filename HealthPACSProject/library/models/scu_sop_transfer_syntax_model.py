# library/models/scu_sop_transfer_syntax_model.py

from typing import Optional, TYPE_CHECKING
from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from library.models.base_model import Base

if TYPE_CHECKING:
    from library.models.dicom_scu_model import DicomScuModel
    from library.models.sop_class_uid_model import SopClassUidModel
    from library.models.transfer_syntax_uid_model import TransferSyntaxUidModel


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

    # Chiave Primaria
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Chiavi Esterne (posizionate come ultimi campi di colonna)
    dicom_scu_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("public.dicom_scu.id", ondelete="CASCADE"),
        nullable=False,
    )
    sop_class_uid_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("public.sop_class_uid.id", ondelete="CASCADE"),
        nullable=False,
    )
    transfer_syntax_uid_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("public.transfer_syntax_uid.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relazioni ORM
    scu: Mapped["DicomScuModel"] = relationship("DicomScuModel")
    sop_class: Mapped["SopClassUidModel"] = relationship("SopClassUidModel")
    transfer_syntax: Mapped["TransferSyntaxUidModel"] = relationship("TransferSyntaxUidModel")