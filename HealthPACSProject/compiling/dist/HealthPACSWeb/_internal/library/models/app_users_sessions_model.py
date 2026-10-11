# library/models/app_users_sessions_model.py

from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from library.models.base_model import Base


class AppUsersSessionsModel(Base):
    """Mappatura della tabella unificata per sessioni web, socket e audit."""

    __tablename__ = "app_users_sessions"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("public.app_users.id"), nullable=False)
    session_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_activity: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)