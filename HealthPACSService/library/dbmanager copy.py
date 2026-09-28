from contextlib import contextmanager
from typing import Generator, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from library.type_health_pacs import HEALT_PACS_CONFIG
from library.logger import logger


class DatabaseManager:
    """
    Gestore centrale del database tramite SQLAlchemy ORM.
    Mantiene la compatibilità con le vecchie query SQL grezze se necessarie.
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
        """Inizializza l'Engine di SQLAlchemy e il Connection Pool gestito."""
        try:
            self.engine = create_engine(
                self.db_url,
                pool_size=self.max_size,
                max_overflow=5,
                pool_timeout=30,
                pool_recycle=1800,
                pool_pre_ping=True
            )
            
            # Creo la factory per generare le sessioni ORM
            self.SessionFactory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False
            )
            
            # Test rapido di connessione al DB
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
        """Context manager per gestire le sessioni ORM con commit e rollback automatici."""
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
    # METODO DI COMPATIBILITÀ PER EXECUTE_WRITE (Se hai ancora codice legacy)
    # -------------------------------------------------------------------------

    def execute_write(self, sql: str, params: tuple = ()) -> Any:
        """
        Esegue query SQL grezze in modo transazionale. 
        Utile per mantenere compatibilità temporanea con vecchi moduli.
        """
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