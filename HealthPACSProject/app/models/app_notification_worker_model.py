from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from .base_model import Base
from app.core.constants import NOTIFY_SEVERITY

class AppNotificationWorkerModel(Base):
    __tablename__ = "app_notification_worker"

    id = Column(Integer, primary_key=True, autoincrement=True)
    notify_key = Column(String(50), unique=True, nullable=False, index=True)
    notify_type = Column(String(50), nullable=False)
    
    # Campo JSONB per la descrizione multilingua (es. {"it": "Testo", "en": "Text"})
    notify_description = Column(JSONB, nullable=False, default=dict)
    
    severity = Column(String(20), default=NOTIFY_SEVERITY.INFO, nullable=False)
    permanent = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    is_sent = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def get_description(self, lang: str = "it", fallback_lang: str = "en") -> str:
        """
        Restituisce la descrizione nella lingua richiesta.
        In assenza del codice lingua specificato, tenta il fallback_lang 
        o la prima traduzione disponibile.
        """
        if not self.notify_description or not isinstance(self.notify_description, dict):
            return ""
        return (
            self.notify_description.get(lang) 
            or self.notify_description.get(fallback_lang) 
            or next(iter(self.notify_description.values()), "")
        )

    def __repr__(self):
        return f"<AppNotificationWorker(key='{self.notify_key}', type='{self.notify_type}', active={self.is_active}, sent={self.is_sent})>"