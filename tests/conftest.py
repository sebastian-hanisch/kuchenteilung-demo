"""Gemeinsame Fixtures: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import kuc_algorithm as A  # noqa: E402


def vals_of(*rows):
    """Bewertungen aus Gewichtslisten."""
    return [A.valuation(list(r)) for r in rows]


@pytest.fixture
def mini():
    """Zwei Teams, zwölf Stunden. Team 1: Stunden 1 bis 6 je 1, Stunden 7 bis 12 je 3 (Summe 24); Team 2: Stunden 1 bis 6 je 3, Stunden 7 und 8 je 0, Stunden 9 bis 12 je 1 (Summe 22).
    Handrechnung: Team 1 schneidet bei Stunde 8 (6 + 2 · 3 = 12 = Hälfte); Team 2 bewertet die linke Seite mit 18/22 = 9/11 und nimmt sie; Team 1 behält die rechte Seite (12/24 = 1/2)."""
    return vals_of([1] * 6 + [3] * 6, [3] * 6 + [0, 0, 1, 1, 1, 1])
