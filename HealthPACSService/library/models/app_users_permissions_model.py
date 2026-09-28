# library/models/app_permissions_model.py

from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from library.models.base_model import Base


class AppUsersPermissionsModel(Base):
    """Mappatura ORM della tabella public.app_permissions."""

    __tablename__ = "app_users_permissions"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)