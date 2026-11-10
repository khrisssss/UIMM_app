"""SIREN helpers shared by the company form and the data pipeline.

A SIREN is the 9-digit French company identifier. Its last digit is a Luhn
checksum, so a typo in one digit is detected before any external call.
"""
import re

LA_POSTE_SIREN = "356000000"  # the only official SIREN that does not follow the Luhn rule


def luhn_is_valid(digits: str) -> bool:
    total = 0
    for index, char in enumerate(reversed(digits)):
        value = int(char)
        if index % 2 == 1:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def normalize_siren(value) -> str | None:
    """Return a clean 9-digit SIREN, None for an empty value, or raise ValueError."""
    if value is None:
        return None
    cleaned = re.sub(r"[\s.\-]", "", str(value))
    if cleaned == "":
        return None
    if not re.fullmatch(r"\d{9}", cleaned):
        raise ValueError("A SIREN must contain exactly 9 digits.")
    if cleaned != LA_POSTE_SIREN and not luhn_is_valid(cleaned):
        raise ValueError("This SIREN is not valid (checksum error).")
    return cleaned
