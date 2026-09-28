# library/repository/dicom_scu_repo.py

from typing import Optional, List, Dict, Any, Union
from sqlalchemy import select, and_
from library.logger import logger
from library.models.dicom_scu_model import DicomScuModel


class DicomSCURepo:
    """Repository ORM per le operazioni CRUD e di verifica autorizzazioni
    sulla tabella public.dicom_scu.
    """

    def __init__(self, db_manager):
        self.db = db_manager

    @staticmethod
    def _to_dict(obj: Optional[DicomScuModel]) -> Optional[Dict[str, Any]]:
        """Converte l'istanza ORM in un dizionario Python per garantire
        la compatibilità con i servizi della logica di business.
        """
        if obj is None:
            return None
        return {
            "id": obj.id,
            "name": obj.name,
            "aetitle": obj.aetitle,
            "ipaddress": obj.ipaddress,
            "port": obj.port,
            "enabled": obj.enabled,
            "description": obj.description,
            "sop_echo": obj.sop_echo,
            "sop_store": obj.sop_store,
            "sop_find": obj.sop_find,
            "sop_move": obj.sop_move,
            "sop_get": obj.sop_get,
            "sop_worklist": obj.sop_worklist,
            "sop_print": obj.sop_print,
        }

    # -------------------------------------------------------------------------
    # RICERCA FLESSIBILE (get_config_scu)
    # -------------------------------------------------------------------------

    def get_config_scu(
        self,
        scu_id: Optional[int] = None,
        aetitle: Optional[str] = None,
        ip_address: Optional[str] = None,
        enabled: Optional[bool] = None,
        fetch_one: bool = False,
    ) -> Union[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """Recupera la configurazione dei client SCU applicando filtri opzionali."""
        conditions = []

        if scu_id is not None:
            conditions.append(DicomScuModel.id == scu_id)

        if aetitle is not None:
            conditions.append(DicomScuModel.aetitle == aetitle.strip())

        if ip_address is not None:
            conditions.append(DicomScuModel.ipaddress == ip_address.strip())

        if enabled is not None:
            conditions.append(DicomScuModel.enabled == enabled)

        try:
            with self.db.get_session() as session:
                stmt = select(DicomScuModel)
                
                if conditions:
                    stmt = stmt.where(and_(*conditions))

                stmt = stmt.order_by(DicomScuModel.name.asc(), DicomScuModel.aetitle.asc())

                if fetch_one:
                    result = session.execute(stmt).scalar_one_or_none()
                    return self._to_dict(result)

                results = session.execute(stmt).scalars().all()
                return [self._to_dict(scu) for scu in results]

        except Exception as e:
            logger.error(f"DicomSCURepository: Errore durante il recupero SCU: {e}")
            return None if fetch_one else []

    # -------------------------------------------------------------------------
    # WRAPPER RAPIDI
    # -------------------------------------------------------------------------

    def get_by_id(self, scu_id: int) -> Optional[Dict[str, Any]]:
        """Recupera uno SCU per ID primario."""
        return self.get_config_scu(scu_id=scu_id, fetch_one=True)

    def get_by_aetitle(self, aetitle: str) -> Optional[Dict[str, Any]]:
        """Recupera uno SCU per AE Title."""
        return self.get_config_scu(aetitle=aetitle, fetch_one=True)

    # -------------------------------------------------------------------------
    # VERIFICHE DICOM & RETE
    # -------------------------------------------------------------------------

    def is_scu_authorized(
        self, ae_title: str, client_ip: str, required_service: Optional[str] = None
    ) -> bool:
        """Verifica se il client è registrato, attivo, con IP valido e
        se ha il permesso per uno specifico servizio (es. 'sop_store', 'sop_find').
        """
        scu = self.get_by_aetitle(ae_title)

        if not scu:
            logger.warning(f"DicomSCURepository: AE Title '{ae_title}' non trovato.")
            return False

        if not scu.get("enabled"):
            logger.warning(f"DicomSCURepository: AE Title '{ae_title}' disabilitato.")
            return False

        # Verifica binding IP
        db_ip = scu.get("ipaddress")
        if db_ip and db_ip.strip() and db_ip.strip() != client_ip.strip():
            logger.warning(
                f"DicomSCURepository: IP mismatch per '{ae_title}'. Atteso: '{db_ip}', Rilevato: '{client_ip}'"
            )
            return False

        # Verifica servizio specifico se richiesto (es. required_service='sop_store')
        if required_service and isinstance(scu, dict):
            if not scu.get(required_service, False):
                logger.warning(
                    f"DicomSCURepository: Servizio '{required_service}' non abilitato per '{ae_title}'."
                )
                return False

        return True

    # -------------------------------------------------------------------------
    # INSERIMENTO & MODIFICA (INSERT & UPDATE)
    # -------------------------------------------------------------------------

    def create(
        self,
        name: str,
        aetitle: str,
        ipaddress: str,
        port: int = 104,
        enabled: bool = True,
        description: Optional[str] = None,
        sop_echo: bool = False,
        sop_store: bool = False,
        sop_find: bool = False,
        sop_move: bool = False,
        sop_get: bool = False,
        sop_worklist: bool = False,
        sop_print: bool = False,
    ) -> Optional[int]:
        """Inserisce un nuovo nodo SCU con tutti i flag di servizio DICOM."""
        try:
            with self.db.get_session() as session:
                scu = DicomScuModel(
                    name=name.strip(),
                    aetitle=aetitle.strip(),
                    ipaddress=ipaddress.strip(),
                    port=port,
                    enabled=enabled,
                    description=description.strip() if description else None,
                    sop_echo=sop_echo,
                    sop_store=sop_store,
                    sop_find=sop_find,
                    sop_move=sop_move,
                    sop_get=sop_get,
                    sop_worklist=sop_worklist,
                    sop_print=sop_print,
                )
                session.add(scu)
                session.flush()
                return scu.id
        except Exception as e:
            logger.error(f"DicomSCURepository: Errore durante la creazione dello SCU: {e}")
            return None

    def update_status(self, scu_id: int, enabled: bool) -> bool:
        """Abilita o disabilita uno specifico nodo SCU."""
        try:
            with self.db.get_session() as session:
                scu = session.get(DicomScuModel, scu_id)
                if not scu:
                    return False
                scu.enabled = enabled
                return True
        except Exception as e:
            logger.error(f"DicomSCURepository: Errore durante l'aggiornamento dello stato dello SCU ID {scu_id}: {e}")
            return False