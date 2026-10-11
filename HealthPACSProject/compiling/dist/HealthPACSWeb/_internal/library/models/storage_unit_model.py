# library/models/storage_unit_model.py

from sqlalchemy import String, Integer, Boolean, BigInteger, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from library.models.base_model import Base


class StorageUnitModel(Base):
    """Mappatura ORM esatta della tabella public.storage_units."""

    __tablename__ = "storage_units"
    __table_args__ = (
        CheckConstraint(
            "alert_threshold_storage >= 1 AND alert_threshold_storage <= 100",
            name="storage_units_alert_threshold_storage_check",
        ),
        CheckConstraint(
            "limit_threshold_storage >= 1 AND limit_threshold_storage <= 100",
            name="storage_units_limit_threshold_storage_check",
        ),
        {"schema": "public"},
    )

    # Chiave Primaria
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Campi
    drive_unit: Mapped[str] = mapped_column(String(2), unique=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    limit_threshold_storage: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    alert_threshold_storage: Mapped[int] = mapped_column(Integer, default=85, nullable=False)