# library/models/app_users_roles_model.py

from typing import Optional
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from library.models.base_model import Base


class AppUsersRolesModel(Base):
    """Mappatura ORM della tabella public.app_users_roles."""

    __tablename__ = "app_users_roles"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    can_delete_studies: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)