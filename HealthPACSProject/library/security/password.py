# library/security/password.py

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from library.logger import logger

# Inizializza l'hasher Argon2id con i parametri consigliati da OWASP
_ph = PasswordHasher()


def hash_password(password: str) -> str:
    """Genera l'hash sicuro della password utilizzando Argon2id."""
    return _ph.hash(password)


def verify_password(stored_hash: str, password: str) -> bool:
    """Verifica se una password in chiaro corrisponde all'hash salvato nel DB.
    
    Ritorna True se corretta, False altrimenti.
    """
    try:
        return _ph.verify(stored_hash, password)
    except (VerifyMismatchError, VerificationError):
        return False
    except Exception as e:
        logger.error(f"Errore durante la verifica della password: {e}")
        return False


def needs_rehash(stored_hash: str) -> bool:
    """Controlla se l'hash memorizzato deve essere aggiornato a parametri più recenti."""
    try:
        return _ph.check_needs_rehash(stored_hash)
    except Exception:
        return False