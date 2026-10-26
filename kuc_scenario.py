"""Szenario: Bewertungen der Teams für die zwölf Hallenstunden (erzeugt oder eingegeben). Deterministisch aus (Modell, Zahl der Teams, Zufalls-Seed)."""

import re

import numpy as np

import kuc_constants as C


def make_weights(model: str, n: int, seed: int) -> list:
    """Ganzzahlige Gewichte je Team und Stunde (n Listen mit CELLS Zahlen von 0 bis WEIGHT_MAX; jede Liste hat eine positive Summe).

    Unabhängig: jedes Gewicht gleichverteilt. Ähnlich: eine gemeinsame Grundverteilung (Exponentialverteilung) plus kleines Rauschen. Gegensätzlich: jedes Team mag einen eigenen Block von Stunden
    (Gewicht 8), alle anderen Stunden mit 0 bis 2."""
    if model not in C.MODELS:
        raise ValueError(model)
    rng = np.random.default_rng(seed)
    base = rng.exponential(1.0, size=C.CELLS)
    rows = []
    for i in range(n):
        if model == "unabh":
            w = rng.integers(0, C.WEIGHT_MAX + 1, size=C.CELLS)
        elif model == "aehnlich":
            w = np.clip(np.round(base * 5 + rng.uniform(-2, 2, size=C.CELLS)), 0, C.WEIGHT_MAX).astype(int)
        else:
            w = np.where((np.arange(C.CELLS) * n // C.CELLS) == i, 8, rng.integers(0, 3, size=C.CELLS))
        w = [int(x) for x in w]
        if sum(w) == 0:
            w[int(rng.integers(0, C.CELLS))] = 1
        rows.append(w)
    return rows


def parse_weights(text: str):
    """Eingabe: eine Zeile je Team, je Zeile CELLS ganze Zahlen von 0 bis WEIGHT_MAX (getrennt durch Komma, Semikolon oder Leerzeichen).
    Rückgabe (Liste von Listen oder None, Fehlermeldung oder None); leerer Text: (None, None)."""
    text = (text or "").strip()
    if not text:
        return None, None
    lines = [ln for ln in re.split(r"[\r\n]+", text) if ln.strip()]
    if not C.N_MIN <= len(lines) <= C.N_MAX:
        return None, f"Es müssen {C.N_MIN} bis {C.N_MAX} Zeilen sein, eine je Team (eingegeben: {len(lines)})."
    rows = []
    for k, line in enumerate(lines, start=1):
        parts = [t for t in re.split(r"[,;\s]+", line.strip()) if t]
        for t in parts:
            if not re.fullmatch(r"\d+", t):
                return None, f"Zeile {k}: „{t}“ ist keine ganze Zahl (erlaubt: Ziffern, getrennt durch Komma, Semikolon oder Leerzeichen)."
        if len(parts) != C.CELLS:
            return None, f"Zeile {k}: Es müssen {C.CELLS} Zahlen sein, eine je Stunde (eingegeben: {len(parts)})."
        w = [int(t) for t in parts]
        if max(w) > C.WEIGHT_MAX:
            return None, f"Zeile {k}: Jede Zahl muss zwischen 0 und {C.WEIGHT_MAX} liegen."
        if sum(w) == 0:
            return None, f"Zeile {k}: Mindestens eine Stunde braucht ein Gewicht über 0."
        rows.append(w)
    return rows, None
