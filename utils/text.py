# utils/text.py
import unicodedata


def normalize_for_sort(text: str) -> str:
    """
    Normaliza un texto para ordenación alfabética en español.
    Hace que: a == á == à == ä == â, etc.

    NO se usa para mostrar texto, solo para ordenar.
    """
    if not text:
        return ""

    # Normaliza a NFD (separa letras y acentos)
    normalized = unicodedata.normalize("NFD", text)

    # Elimina los diacríticos (acentos)
    without_accents = "".join(
        c for c in normalized
        if unicodedata.category(c) != "Mn"
    )

    return without_accents.casefold()
