# library/models/sessioni_web_model.py

from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from library.models.base_model import Base


class SessioniWebModel(Base):
    """Mappatura ORM della tabella public.sessioni_web per la gestione delle sessioni WebSocket/Web."""

    __tablename__ = "sessioni_web"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    token_sessione: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    data_scadenza: Mapped[datetime] = mapped_column(DateTime, nullable=False)