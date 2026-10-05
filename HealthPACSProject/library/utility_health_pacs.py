# library/utility_health_pacs.py

from pathlib import Path
from typing import Union
from library.logger import logger


def ensure_directory_exists(path_input: Union[str, Path]) -> Path:
    """Risolve e crea una directory se non esiste, restituendo l'oggetto Path assoluto."""
    try:
        target_path = Path(path_input).resolve()

        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Utility: Creata nuova directory: {target_path}")
        else:
            logger.info(f"Utility: Directory esistente verificata: {target_path}")

        return target_path

    except Exception as e:
        logger.error(f"Utility: Errore durante la creazione della directory '{path_input}': {e}")
        raise OSError(f"Impossibile creare la directory '{path_input}': {e}")


def build_storage_path(drive_unit: str, root_storage: str, *subdirs: str) -> Path:
    """Costruisce e garantisce un percorso di archiviazione valido partendo dall'unità di memoria."""
    drive = drive_unit.strip()
    if len(drive) == 2 and drive[1] == ":":
        drive = f"{drive}\\"

    clean_root = str(root_storage).lstrip("/\\")
    full_path = Path(drive) / clean_root

    for subdir in subdirs:
        if subdir:
            full_path = full_path / str(subdir).strip("/\\")

    return ensure_directory_exists(full_path)


def get_file_size_bytes(file_path: Union[str, Path]) -> int:
    """
    Ritorna la dimensione in byte di un file specificato dal percorso.
    Se il file non esiste o si verifica un errore, restituisce 0.
    """
    try:
        path = Path(file_path)
        if path.exists() and path.is_file():
            return path.stat().st_size
        return 0
    except Exception as e:
        logger.error(f"[Utility] Errore durante il calcolo della dimensione per {file_path}: {e}")
        return 0