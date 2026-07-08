"""Journalisation homogene pour toute la plateforme."""
from __future__ import annotations

import logging
import sys

_CONFIGURED = False


def get_logger(name: str = "urbanhub") -> logging.Logger:
    """Retourne un logger configure (console, format horodate)."""
    global _CONFIGURED
    if not _CONFIGURED:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        root = logging.getLogger("urbanhub")
        root.setLevel(logging.INFO)
        root.addHandler(handler)
        root.propagate = False
        _CONFIGURED = True
    return logging.getLogger(name if name.startswith("urbanhub") else f"urbanhub.{name}")
