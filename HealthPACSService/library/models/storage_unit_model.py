# library/models/storage_unit.py

from sqlalchemy import String, Integer, Boolean, CheckConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from library.models.base_model import Base


class StorageUnitModel(Base):
    """Mappatura ORM esatta della tabella public.storage_units."""

    __tablename__ = "storage_units"
    __table_args__ = (
        CheckConstraint(
            "alert_threshold_storage >= 1 AND alert_threshold_storage <= 100",
            name="storage_units_alert_threshold_storage_check"
        ),
        CheckConstraint(
            "limit_threshold_storage >= 1 AND limit_threshold_storage <= 100",
            name="storage_units_limit_threshold_storage_check"
        ),
        {"schema": "public"}
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    drive_unit: Mapped[str] = mapped_column(String(2), unique=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    limit_threshold_storage: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    alert_threshold_storage: Mapped[int] = mapped_column(Integer, default=85, nullable=False)