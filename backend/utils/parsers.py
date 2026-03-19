"""Aviation data parsing utilities."""

from datetime import date
from typing import Optional


def mode_s_octal_to_hex(octal_str: str) -> str:
    """Convert a Mode-S octal address string to a 6-character hex string.

    Args:
        octal_str: Octal representation of the Mode-S / ICAO 24-bit address.

    Returns:
        Uppercase 6-character hex string (e.g., 'A12F3B').

    Raises:
        ValueError: If the input is not a valid octal string.
    """
    decimal_value = int(octal_str, 8)
    return format(decimal_value, "06X")


def parse_faa_date(date_str: str) -> Optional[date]:
    """Parse an FAA-format date string (YYYYMMDD) into a date object.

    Args:
        date_str: Date in YYYYMMDD format (e.g., '20240315').

    Returns:
        A date object, or None if the input is empty, malformed, or cannot
        be parsed.
    """
    if not date_str or not date_str.strip():
        return None

    cleaned = date_str.strip()
    if len(cleaned) != 8:
        return None

    try:
        year = int(cleaned[:4])
        month = int(cleaned[4:6])
        day = int(cleaned[6:8])
        return date(year, month, day)
    except (ValueError, OverflowError):
        return None


def normalize_n_number(n: str) -> str:
    """Normalize a US aircraft N-number by stripping the 'N' prefix and whitespace.

    Args:
        n: Raw N-number string (e.g., 'N12345', 'n12345', '12345').

    Returns:
        Cleaned N-number without the 'N' prefix, uppercased and stripped
        (e.g., '12345').
    """
    cleaned = n.strip().upper()
    if cleaned.startswith("N"):
        cleaned = cleaned[1:]
    return cleaned
