from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.sql import func
from library.models import Base
from library.constant_health_pacs import NOTIFY_SEVERITY

class AppNotificationWorkerModel(Base):
    __tablename__ = "app_notification_worker"

    id = Column(Integer, primary_key=True, autoincrement=True)
    notify_key = Column(String(100), unique=True, nullable=False, index=True)
    notify_type = Column(String(50), nullable=False)
    severity = Column(String(20), default=NOTIFY_SEVERITY.INFO, nullable=False)  # <-- NUOVO CAMPO
    notify_description = Column(Text, nullable=True)
    permanent = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    is_sent = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<AppNotificationWorker(key='{self.notify_key}', type='{self.notify_type}', active={self.is_active}, sent={self.is_sent})>"