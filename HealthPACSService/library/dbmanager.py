# library/dbmanager.py

from contextlib import contextmanager
from typing import Generator, Any, Union
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from library.type_health_pacs import HEALT_PACS_CONFIG
from library.logger import logger


class DatabaseManager:
    """Gestore centrale del database tramite SQLAlchemy ORM (SQLAlchemy 2.0 + psycopg3).

    Mantiene il supporto per execute_write per garantire la retrocompatibilità
    con eventuali componenti del sistema non ancora totalmente migrati.
    """

    def __init__(self, min_size: int = 1, max_size: int = 10):
        # Costruzione della stringa di connessione per SQLAlchemy con psycopg (v3)
        user = HEALT_PACS_CONFIG.get_database_user()
        password = HEALT_PACS_CONFIG.get_database_password()
        host = HEALT_PACS_CONFIG.get_database_host()
        port = HEALT_PACS_CONFIG.get_database_port()
        dbname = HEALT_PACS_CONFIG.get_database_name()

        self.db_url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{dbname}"
        self.min_size = min_size
        self.max_size = max_size

        self.engine = None
        self.SessionFactory = None

    def connect(self) -> bool:
        """Inizializza l'Engine di SQLAlchemy e la SessionFactory per l'ORM."""
        try:
            self.engine = create_engine(
                self.db_url,
                pool_size=self.max_size,
                max_overflow=5,
                pool_timeout=30,
                pool_recycle=1800,
                pool_pre_ping=True,
            )

            # Factory per generare le sessioni ORM con gestione transazionale esplicta
            self.SessionFactory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
            )

            # Test rapido di connettività al database
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            logger.info("DatabaseManager: Engine ORM e Pool di connessioni inizializzati con successo.")
            return True
        except Exception as e:
            logger.error(f"DatabaseManager: Errore durante l'inizializzazione dell'Engine DB: {e}")
            return False

    def disconnect(self):
        """Chiude l'Engine e rilascia tutte le connessioni nel pool."""
        if self.engine:
            self.engine.dispose()
            logger.info("DatabaseManager: Engine e pool di connessioni dismessi.")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Context manager per la gestione automatica del ciclo di vita delle sessioni ORM.

        Esegue automaticamente commit in caso di successo, rollback su eccezione
        e garantisce la chiusura pulita della sessione al termine dell'operazione.
        """
        if not self.SessionFactory:
            raise RuntimeError("DatabaseManager non inizializzato. Chiama prima connect().")

        session: Session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"DatabaseManager: Errore durante la transazione ORM: {e}")
            raise e
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # METODO DI RETROCOMPATIBILITÀ (Esecuzione Query SQL Grezze)
    # -------------------------------------------------------------------------

    def execute_write(self, sql: str, params: Union[tuple, dict, list] = ()) -> Any:
        """Esegue query SQL grezze in modo transazionale per moduli legacy."""
        if not self.engine:
            raise RuntimeError("DatabaseManager non inizializzato. Chiama prima connect().")

        try:
            with self.engine.begin() as conn:
                result = conn.execute(text(sql), params)

                if result.returns_rows:
                    row = result.fetchone()
                    return dict(row._mapping) if row else None
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"DatabaseManager: Errore durante execute_write: {e} | SQL: {sql}")
            raise e