from typing import List, Optional
from sqlalchemy.orm import Session
from library.models.app_notification_worker_model import AppNotificationWorkerModel


class AppNotificationWorkerRepo:
    def __init__(self, db_session: Session):
        self.session = db_session

    def get_by_key(self, notify_key: str) -> Optional[AppNotificationWorkerModel]:
        """Recupera una notifica tramite la sua chiave univoca."""
        return self.session.query(AppNotificationWorkerModel).filter_by(notify_key=notify_key).first()

    def get_active_notifications(self) -> List[AppNotificationWorkerModel]:
        """
        Usato al LOGIN / Refresh dell'utente:
        Recupera tutte le notifiche attualmente attive nel sistema.
        """
        return self.session.query(AppNotificationWorkerModel).filter_by(is_active=True).all()

    def get_pending_socket_notifications(self) -> List[AppNotificationWorkerModel]:
        """
        Usato dal WORKER SOCKET:
        Recupera le notifiche scattate che devono essere ancora inviate via socket (is_active=True, is_sent=False).
        """
        return self.session.query(AppNotificationWorkerModel).filter_by(
            is_active=True,
            is_sent=False
        ).all()

    def trigger_alert(self, notify_key: str, description: Optional[str] = None) -> bool:
        """
        Attiva un evento precaricato impostando is_active=True e is_sent=False.
        Restituisce True se lo stato è cambiato.
        """
        notif = self.get_by_key(notify_key)
        if notif:
            if not notif.is_active:
                notif.is_active = True
                notif.is_sent = False
                if description:
                    notif.notify_description = description
                self.session.commit()
                return True
        return False

    def resolve_alert(self, notify_key: str) -> bool:
        """
        Riporta l'evento allo stato di quietanza (is_active=False, is_sent=False).
        """
        notif = self.get_by_key(notify_key)
        if notif and notif.is_active:
            notif.is_active = False
            notif.is_sent = False
            self.session.commit()
            return True
        return False

    def mark_as_sent(self, notification_id: int) -> None:
        """
        Segna la notifica come inviata via socket (is_sent=True).
        """
        notif = self.session.query(AppNotificationWorkerModel).get(notification_id)
        if notif:
            notif.is_sent = True
            self.session.commit()