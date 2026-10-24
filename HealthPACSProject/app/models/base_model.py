# library/models/base.py

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Classe Base dichiarativa condivisa da tutti i modelli ORM.
    Mantiene un unico registro Metadata per consentire JOIN, 
    relazioni (relationship) e migrazioni coerenti.
    """
    pass