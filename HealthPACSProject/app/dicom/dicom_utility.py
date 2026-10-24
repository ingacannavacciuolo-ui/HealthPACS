# library/dicom/dicom_utility.py

from datetime import datetime, date, time
from typing import Optional, Any


# -------------------------------------------------------------------------
# PARSING (Da DICOM string -> Oggetti Python)
# -------------------------------------------------------------------------

def parse_dicom_date(date_str: Optional[Any]) -> Optional[date]:
    """Converte una stringa DICOM YYYYMMDD in un oggetto datetime.date."""
    if not date_str:
        return None
    try:
        return datetime.strptime(str(date_str).strip(), "%Y%m%d").date()
    except (ValueError, TypeError):
        return None


def parse_dicom_time(time_str: Optional[Any]) -> Optional[time]:
    """Converte una stringa DICOM HHMMSS o HHMMSS.FFFFFF in un oggetto datetime.time."""
    if not time_str:
        return None
    try:
        clean_time = str(time_str).strip().split(".")[0]
        return datetime.strptime(clean_time, "%H%M%S").time()
    except (ValueError, TypeError):
        return None


def clean_dicom_str(val: Optional[Any]) -> Optional[str]:
    """Converte tipi speciali DICOM (es. PersonName) in stringhe pulite o None."""
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


# -------------------------------------------------------------------------
# FORMATTING (Da Oggetti Python -> DICOM string)
# -------------------------------------------------------------------------

def format_dicom_date(dt: Optional[date]) -> Optional[str]:
    """Converte un oggetto datetime.date in una stringa DICOM 'YYYYMMDD'."""
    if not dt:
        return None
    try:
        return dt.strftime("%Y%m%d")
    except (AttributeError, ValueError):
        return None


def format_dicom_time(tm: Optional[time]) -> Optional[str]:
    """Converte un oggetto datetime.time in una stringa DICOM 'HHMMSS'."""
    if not tm:
        return None
    try:
        return tm.strftime("%H%M%S")
    except (AttributeError, ValueError):
        return None