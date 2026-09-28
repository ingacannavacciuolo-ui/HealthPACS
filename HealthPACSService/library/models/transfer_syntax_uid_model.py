# library/models/transfer_syntax_uid_model.py

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from library.models.base_model import Base


class TransferSyntaxUidModel(Base):
    """Mappatura ORM della tabella public.transfer_syntax_uid."""

    __tablename__ = "transfer_syntax_uid"
    __table_args__ = {"schema": "public"}

    # Chiave Primaria
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Campi con vincolo UNIQUE su uid
    uid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    uid_description: Mapped[str] = mapped_column(String(100), nullable=False)