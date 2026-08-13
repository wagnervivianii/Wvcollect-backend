from __future__ import annotations

import re
import unicodedata


def normalize_display_text(value: str) -> str:
    """
    Remove espaços excedentes sem destruir a grafia original.
    """

    return re.sub(
        r"\s+",
        " ",
        value,
    ).strip()


def normalize_lookup_key(value: str) -> str:
    """
    Produz uma chave canônica para comparação.

    A representação original não é modificada no dado de origem.
    """

    normalized = unicodedata.normalize(
        "NFKD",
        value,
    )

    normalized = "".join(
        char
        for char in normalized
        if not unicodedata.combining(char)
    )

    normalized = normalized.upper().strip()

    normalized = re.sub(
        r"[^A-Z0-9]+",
        " ",
        normalized,
    )

    return re.sub(
        r"\s+",
        " ",
        normalized,
    ).strip()
