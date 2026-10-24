from typing import List, Optional, Union, Dict
from sqlalchemy.orm import Session
from app.models.app_notification_worker_model import AppNotificationWorkerModel
from app.core.constants import NOTIFY_SEVERITY


class AppNotificationWorkerRepo:
    def __init__(self, db_session: Session):
        self.session = db_session

    # =========================================================================
    # METODI DI LETTURA (READ)
    # =========================================================================

    # Recupera una notifica tramite la sua chiave univoca.
    #
    # ESEMPIO DI UTILIZZO:
    # notif = repo.get_by_key("DISK_FULL_WARNING")
    # if notif:
    #     print(notif.get_description("it"))
    def get_by_key(self, notify_key: str) -> Optional[AppNotificationWorkerModel]:
        return self.session.query(AppNotificationWorkerModel).filter_by(notify_key=notify_key).first()

    # Usato al LOGIN / Refresh dell'utente:
    # Recupera tutte le notifiche attualmente attive e già inviate nel sistema (is_active=True, is_sent=True).
    #
    # ESEMPIO DI UTILIZZO:
    # active_notifs = repo.get_active_notifications()
    # for n in active_notifs:
    #     print(n.notify_key, n.get_description("it"))
    def get_active_notifications(self) -> List[AppNotificationWorkerModel]:
        return self.session.query(AppNotificationWorkerModel).filter_by(
            is_active=True, 
            is_sent=True
            ).all()

    # Usato dal WORKER SOCKET:
    # Recupera le notifiche attive non ancora inviate via socket (is_active=True, is_sent=False).
    #
    # ESEMPIO DI UTILIZZO:
    # pending_notifs = repo.get_pending_socket_notifications()
    # for n in pending_notifs:
    #     socket.emit("notification", n.notify_description)
    #     repo.mark_as_sent(n.id)
    def get_pending_socket_notifications(self) -> List[AppNotificationWorkerModel]:
        return self.session.query(AppNotificationWorkerModel).filter_by(
            is_active=True,
            is_sent=False
        ).all()

    # =========================================================================
    # METODO DI CREAZIONE (CREATE)
    # =========================================================================

    # Crea e inserisce un nuovo record da zero salvando il dict JSON così com'è.
    #
    # ESEMPIO DI UTILIZZO:
    #
    # # Esempio 1: Notifica multilingua completa
    # repo.create(
    #     notify_key="DISK_FULL_WARNING",
    #     notify_type="SYSTEM",
    #     notify_description={
    #         "it": "Spazio su disco in esaurimento (rimasto < 10%)",
    #         "en": "Disk space running low (less than 10% remaining)",
    #         "es": "Espacio en disco agotado (menos del 10% restante)"
    #     },
    #     severity=NOTIFY_SEVERITY.WARNING,
    #     permanent=False,
    #     is_active=True,
    #     is_sent=False
    # )
    #
    # # Esempio 2: Notifica con singola lingua iniziale
    # repo.create(
    #     notify_key="PACS_SERVICE_STOPPED",
    #     notify_type="PACS_SERVICE",
    #     notify_description={
    #         "it": "Il servizio DICOM Receiver si è arrestato inaspettatamente"
    #     },
    #     severity=NOTIFY_SEVERITY.CRITICAL,
    #     permanent=True,
    #     is_active=True,
    #     is_sent=False
    # )
    def create(
        self,
        notify_key: str,
        notify_type: str,
        notify_description: Dict[str, str],
        severity: str = NOTIFY_SEVERITY.INFO,
        permanent: bool = False,
        is_active: bool = False,
        is_sent: bool = False
    ) -> AppNotificationWorkerModel:
        new_notif = AppNotificationWorkerModel(
            notify_key=notify_key,
            notify_type=notify_type,
            notify_description=notify_description,
            severity=severity,
            permanent=permanent,
            is_active=is_active,
            is_sent=is_sent
        )
        self.session.add(new_notif)
        self.session.commit()
        self.session.refresh(new_notif)
        return new_notif

    # =========================================================================
    # METODI DI AGGIORNAMENTO (UPDATE)
    # =========================================================================

    # Aggiorna un record esistente tramite notify_key.
    #
    # GESTIONE DI 'description':
    # - Se si passa un dict (es. {"it": "Testo", "en": "Text"}): sovrascrive l'intero campo JSONB.
    # - Se si passa una str (es. "Messaggio"): aggiorna/aggiunge SOLO la voce per la lingua 'lang' specificata.
    #
    # ESEMPIO DI UTILIZZO:
    #
    # # Aggiornamento con intero dict multilingua:
    # repo.update(
    #     notify_key="DISK_FULL_WARNING",
    #     description={"it": "Disco pieno al 99%", "en": "Disk 99% full"},
    #     is_active=True,
    #     is_sent=False
    # )
    #
    # # Aggiornamento o aggiunta di una singola lingua (es. inglese) senza cancellare l'italiano:
    # repo.update(
    #     notify_key="DISK_FULL_WARNING",
    #     description="Disk space low",
    #     lang="en"
    # )
    def update(
        self,
        notify_key: str,
        description: Optional[Union[Dict[str, str], str]] = None,
        severity: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_sent: Optional[bool] = None,
        lang: str = "it"
    ) -> Optional[AppNotificationWorkerModel]:
        notif = self.get_by_key(notify_key)
        if not notif:
            return None

        # Gestione aggiornamento descrizione (dict vs str)
        if description is not None:
            if isinstance(description, dict):
                notif.notify_description = description
            elif isinstance(description, str):
                current_desc = dict(notif.notify_description) if notif.notify_description else {}
                current_desc[lang] = description
                notif.notify_description = current_desc

        if severity is not None:
            notif.severity = severity

        if is_active is not None:
            notif.is_active = is_active

        if is_sent is not None:
            notif.is_sent = is_sent

        self.session.commit()
        self.session.refresh(notif)
        return notif

    # Riporta l'evento allo stato di quietanza (is_active=False, is_sent=False).
    #
    # ESEMPIO DI UTILIZZO:
    # repo.resolve_alert("DISK_FULL_WARNING")
    def resolve_alert(self, notify_key: str) -> bool:
        notif = self.get_by_key(notify_key)
        if notif and notif.is_active:
            notif.is_active = False
            notif.is_sent = False
            self.session.commit()
            return True
        return False

    # Segna la notifica come inviata via socket (is_sent=True).
    #
    # ESEMPIO DI UTILIZZO:
    # repo.mark_as_sent(notification_id=12)
    def mark_as_sent(self, notification_id: int) -> None:
        notif = self.session.query(AppNotificationWorkerModel).get(notification_id)
        if notif:
            notif.is_sent = True
            self.session.commit()