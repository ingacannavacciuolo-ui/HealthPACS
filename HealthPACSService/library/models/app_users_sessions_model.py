# library/models/app_users_sessions_model.py

from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, BigInteger, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from library.models.base_model import Base


class AppUsersSessionsModel(Base):
    """Mappatura ORM della tabella public.app_users_sessions."""

    __tablename__ = "app_users_sessions"
    __table_args__ = {"schema": "public"}

    # Chiave Primaria
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Dati della Sessione
    session_token: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    # Chiave Esterna verso l'Utente (posizionata come ultimo campo)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("public.app_users.id", ondelete="CASCADE"),
        nullable=False,
    )