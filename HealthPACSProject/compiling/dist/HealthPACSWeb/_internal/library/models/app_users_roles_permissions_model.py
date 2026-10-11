# library/models/app_users_roles_permissions_model.py

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from library.models.base_model import Base


class AppUsersRolesPermissionsModel(Base):
    """Mappatura ORM della tabella ponte public.app_users_roles_permissions."""

    __tablename__ = "app_users_roles_permissions"
    __table_args__ = {"schema": "public"}

    role_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("public.app_users_roles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    permission_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("public.app_users_permissions.id", ondelete="CASCADE"),
        primary_key=True,
    )