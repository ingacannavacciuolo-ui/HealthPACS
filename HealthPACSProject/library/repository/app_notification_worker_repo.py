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
        Recupera le notifiche scattate o aggiornate che devono essere ancora inviate via socket (is_active=True, is_sent=False).
        """
        return self.session.query(AppNotificationWorkerModel).filter_by(
            is_active=True,
            is_sent=False
        ).all()

    def trigger_alert(
        self, 
        notify_key: str, 
        description: Optional[str] = None, 
        severity: Optional[str] = None
    ) -> bool:
        """
        Attiva o aggiorna un evento impostando is_active=True e is_sent=False.
        Se l'evento è già attivo ma la descrizione cambia, forza il reinvio (is_sent=False).
        """
        notif = self.get_by_key(notify_key)
        if notif:
            state_changed = False

            # Se l'allarme era spento, lo attiviamo
            if not notif.is_active:
                notif.is_active = True
                state_changed = True

            # Se la descrizione o la severity cambiano, aggiorniamo il record
            if description and notif.notify_description != description:
                notif.notify_description = description
                state_changed = True

            if severity and getattr(notif, "severity", None) != severity:
                notif.severity = severity
                state_changed = True

            # Se c'è stato un qualsiasi cambiamento o l'evento deve essere reinviato
            if state_changed or notif.is_sent:
                notif.is_sent = False  # Forza il worker a reinviare la notifica aggiornata via socket
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