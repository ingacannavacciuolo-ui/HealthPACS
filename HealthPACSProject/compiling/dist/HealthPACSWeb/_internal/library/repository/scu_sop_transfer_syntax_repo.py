# library/repository/scu_sop_transfer_syntax_repo.py

from typing import Optional, List, Dict, Any
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from library.logger import logger

# Importiamo i modelli necessari per eseguire le JOIN
from library.models import ScuSopTransferSyntaxModel,DicomScuModel, SopClassUidModel,TransferSyntaxUidModel



class ScuSopTransferSyntaxRepo:
    """Repository ORM per la gestione delle associazioni tra Client SCU,
    SOP Class UID e Transfer Syntax UID (tabella public.scu_sop_transfer_syntax).
    """

    def __init__(self, db_manager):
        self.db = db_manager

    # -------------------------------------------------------------------------
    # OPERAZIONI DI LETTURA (READ)
    # -------------------------------------------------------------------------

    def get_client_permissions(self, ae_title: str) -> Dict[str, List[str]]:
        """Ritorna la mappa {SOP_Class_UID: [Transfer_Syntax_UIDs]} autorizzata per il client."""
        permissions: Dict[str, List[str]] = {}

        try:
            with self.db.get_session() as session:
                # Costruzione della SELECT con JOIN tra i 4 modelli
                stmt = (
                    select(
                        SopClassUidModel.uid.label("sop_uid"),
                        TransferSyntaxUidModel.uid.label("ts_uid"),
                    )
                    .select_from(ScuSopTransferSyntaxModel)
                    .join(
                        DicomScuModel,
                        ScuSopTransferSyntaxModel.dicom_scu_id == DicomScuModel.id,
                    )
                    .join(
                        SopClassUidModel,
                        ScuSopTransferSyntaxModel.sop_class_uid_id == SopClassUidModel.id,
                    )
                    .join(
                        TransferSyntaxUidModel,
                        ScuSopTransferSyntaxModel.transfer_syntax_uid_id == TransferSyntaxUidModel.id,
                    )
                    .where(
                        DicomScuModel.aetitle == ae_title.strip(),
                        DicomScuModel.enabled == True,
                    )
                )

                rows = session.execute(stmt).all()

                for row in rows:
                    sop_uid = row.sop_uid
                    ts_uid = row.ts_uid

                    if sop_uid not in permissions:
                        permissions[sop_uid] = []
                    permissions[sop_uid].append(ts_uid)

            return permissions

        except Exception as e:
            logger.error(
                f"ScuSopTransferSyntaxRepo: Errore recupero permessi per AE Title '{ae_title}': {e}"
            )
            return {}

    # -------------------------------------------------------------------------
    # OPERAZIONI DI SCRITTURA E CANCELLAZIONE (INSERT / DELETE)
    # -------------------------------------------------------------------------

    def add_client_permission(
        self, scu_id: int, sop_class_id: int, transfer_syntax_id: int
    ) -> bool:
        """Associa una SOP Class e Transfer Syntax a un client SCU.
        Sfrutta ON CONFLICT DO NOTHING di PostgreSQL per evitare duplicati.
        """
        try:
            with self.db.get_session() as session:
                stmt = (
                    pg_insert(ScuSopTransferSyntaxModel)
                    .values(
                        dicom_scu_id=scu_id,
                        sop_class_uid_id=sop_class_id,
                        transfer_syntax_uid_id=transfer_syntax_id,
                    )
                    .on_conflict_do_nothing(
                        constraint="unique_scu_sop_ts"
                    )
                )
                session.execute(stmt)
                return True
        except Exception as e:
            logger.error(
                f"ScuSopTransferSyntaxRepo: Errore durante l'inserimento permessi SCU ID {scu_id}: {e}"
            )
            return False

    def remove_client_permission(
        self, scu_id: int, sop_class_id: Optional[int] = None
    ) -> bool:
        """Rimuove tutti i permessi o solo quelli di una specifica SOP Class per un client."""
        try:
            with self.db.get_session() as session:
                stmt = delete(ScuSopTransferSyntaxModel).where(
                    ScuSopTransferSyntaxModel.dicom_scu_id == scu_id
                )

                if sop_class_id is not None:
                    stmt = stmt.where(
                        ScuSopTransferSyntaxModel.sop_class_uid_id == sop_class_id
                    )

                result = session.execute(stmt)
                return result.rowcount > 0
        except Exception as e:
            logger.error(
                f"ScuSopTransferSyntaxRepo: Errore durante la rimozione permessi SCU ID {scu_id}: {e}"
            )
            return False