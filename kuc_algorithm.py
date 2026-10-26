"""Kern: Kuchenteilung. Der „Kuchen“ ist das Intervall [0, m] aus m gleich langen Zellen (zum Beispiel Stunden); jede Person bewertet jede Zelle mit einer festen Dichte (stückweise konstant), ihr Gesamtwert ist 1.

Alle Protokolle (Geteilt und gewählt, Selfridge–Conway, bewegliches Messer) rechnen EXAKT mit Brüchen (`fractions.Fraction`): Schnittpunkte lösen lineare Gleichungen innerhalb einer Zelle, kein Rundungsfehler.
Ein Stück ist eine Liste von Intervallen (a, b) mit a < b; Gleichstände entscheidet die kleinere Nummer der Person. Die Verteilungen „höchste Wohlfahrt“ und alle Optimierungen mit Nebenbedingungen
(neidfrei, proportional, nicht schlechter als ein Protokoll) sind lineare Programme über den Anteilen x[i][j] (Anteil der Zelle j für Person i) und werden mit HiGHS (scipy) numerisch gelöst."""

from fractions import Fraction

import numpy as np
from scipy.optimize import linprog

PROTOCOL_NAMES = ("geteilt", "selfridge", "messer")
TOL = 1e-7   # Toleranz für alle LP-Ergebnisse (Gleitkomma); die Protokolle werden exakt geprüft


def valuation(weights) -> tuple:
    """Dichten je Zelle aus ganzzahligen Gewichten; der Wert des ganzen Kuchens ist 1."""
    if not weights or any(int(w) != w or w < 0 for w in weights) or sum(weights) == 0:
        raise ValueError("Gewichte müssen nichtnegative ganze Zahlen mit positiver Summe sein")
    total = sum(weights)
    return tuple(Fraction(int(w), total) for w in weights)


def value(v, a, b) -> Fraction:
    """Wert des Intervalls [a, b] für die Dichten v."""
    total = Fraction(0)
    for j, d in enumerate(v):
        lo, hi = max(a, Fraction(j)), min(b, Fraction(j + 1))
        if hi > lo:
            total += d * (hi - lo)
    return total


def piece_value(v, piece) -> Fraction:
    return sum((value(v, a, b) for a, b in piece), Fraction(0))


def quantile(v, start, target, end=None):
    """Der kleinste Punkt x ≥ start, bis zu dem das Intervall [start, x] genau den Wert `target` hat; None, wenn er bis `end` (Standard: Ende des Kuchens) nicht erreicht wird."""
    m = len(v)
    end = Fraction(m) if end is None else end
    if target == 0:
        return start
    acc = Fraction(0)
    x = start
    j = int(start)
    while x < end and j < m:
        hi = min(Fraction(j + 1), end)
        seg = v[j] * (hi - x)
        if acc + seg >= target:                         # bei Dichte 0 ist seg = 0 und acc < target: das Stück wird übersprungen
            return x + (target - acc) / v[j]
        acc += seg
        x = hi
        j += 1
    return None


def normalize(piece) -> list:
    """Intervalle sortieren, leere entfernen und aneinanderstoßende verschmelzen."""
    out = []
    for a, b in sorted(i for i in piece if i[1] > i[0]):
        if out and out[-1][1] == a:
            out[-1] = (out[-1][0], b)
        else:
            out.append((a, b))
    return out


def fragments(piece) -> int:
    """Zahl der getrennten Blöcke eines Stücks (bei Zeitfenstern: wie oft die Gruppe die Halle wechseln muss)."""
    return len(normalize(piece))


def _check(vals, n_required=None):
    if len(vals) < 2:
        raise ValueError("Es braucht mindestens zwei Personen")
    if n_required is not None and len(vals) != n_required:
        raise ValueError(f"Dieses Protokoll gilt nur für {n_required} Personen")
    if len({len(v) for v in vals}) != 1:
        raise ValueError("Alle Bewertungen brauchen gleich viele Zellen")


def cut_and_choose(vals, trace=None) -> list:
    """Geteilt und gewählt (zwei Personen): Person 1 schneidet den Kuchen in zwei Stücke, die sie gleich bewertet; Person 2 wählt das Stück, das sie höher bewertet (bei Gleichstand das linke).
    `trace` (Liste) bekommt die Schritte: ("schnitt", Person, x) und ("wahl", Person, "links" oder "rechts")."""
    _check(vals, 2)
    v1, v2 = vals
    m = len(v1)
    x = quantile(v1, Fraction(0), Fraction(1, 2))
    left, right = [(Fraction(0), x)], [(x, Fraction(m))]
    takes_left = piece_value(v2, left) >= piece_value(v2, right)
    if trace is not None:
        trace.append(("schnitt", 0, x))
        trace.append(("wahl", 1, "links" if takes_left else "rechts"))
    return [right, left] if takes_left else [left, right]


def selfridge_conway(vals, trace=None) -> list:
    """Selfridge–Conway (drei Personen A, B, C = 0, 1, 2), neidfrei. A schneidet in drei gleich bewertete Stücke; B kürzt das von B am höchsten bewertete Stück, bis es dem zweithöchsten gleicht (bei Gleichstand wird nicht gekürzt);
    C wählt; hat C das gekürzte Stück nicht genommen, bekommt B es, sonst wählt B unter den übrigen; A bekommt das letzte. Den Rest der Kürzung teilt die Person aus {B, C}, die das gekürzte Stück NICHT hat,
    in drei gleich bewertete Teile; es wählen zuerst die Person mit dem gekürzten Stück, dann A, zuletzt die teilende Person.
    `trace` bekommt die Schritte: ("schnitt", 0, x) je Schnitt von A, ("kuerzen", 1, Punkt) mit dem Punkt, an dem B kürzt (None: kein Kürzen nötig), ("wahl", Person, Stück), ("teilen", Person, Rest) für die Teilung der Kürzung."""
    _check(vals, 3)
    vA, vB, vC = vals
    m = len(vA)
    x1 = quantile(vA, Fraction(0), Fraction(1, 3))
    x2 = quantile(vA, x1, Fraction(1, 3))
    pieces = [[(Fraction(0), x1)], [(x1, x2)], [(x2, Fraction(m))]]
    if trace is not None:
        trace.extend([("schnitt", 0, x1), ("schnitt", 0, x2)])
    bv = [piece_value(vB, p) for p in pieces]
    order = sorted(range(3), key=lambda i: (-bv[i], i))
    largest, second = order[0], order[1]
    trimming = []
    if bv[largest] > bv[second]:
        a, b = pieces[largest][0]
        keep = quantile(vB, a, bv[second], b)
        trimming = [(keep, b)]
        pieces[largest] = [(a, keep)]
    if trace is not None:
        trace.append(("kuerzen", 1, trimming[0][0] if trimming else None, largest))
    cv = [piece_value(vC, p) for p in pieces]
    c_pick = max(range(3), key=lambda i: (cv[i], -i))
    owner = {c_pick: 2}
    if largest != c_pick:
        owner[largest] = 1                                               # B bekommt das gekürzte Stück
    else:
        rest = [i for i in range(3) if i != c_pick]
        b_pick = max(rest, key=lambda i: (piece_value(vB, pieces[i]), -i))
        owner[b_pick] = 1
    owner[next(i for i in range(3) if i not in owner)] = 0
    if trace is not None:
        trace.extend(("wahl", owner[i], i) for i in sorted(owner, key=lambda i: {2: 0, 1: 1, 0: 2}[owner[i]]))
    result = {owner[i]: list(pieces[i]) for i in range(3)}
    if trimming:
        holder = owner[largest]
        divider = 1 if holder == 2 else 2
        vq = vals[divider]
        a, b = trimming[0]
        if trace is not None:
            trace.append(("teilen", divider, holder))
        third = piece_value(vq, trimming) / 3
        t1 = quantile(vq, a, third, b)
        t2 = quantile(vq, t1, third, b)
        parts = [[(a, t1)], [(t1, t2)], [(t2, b)]]
        for who in (holder, 0, divider):
            k = max(range(len(parts)), key=lambda i: (piece_value(vals[who], parts[i]), -i))
            result[who] += parts.pop(k)
    return [normalize(result[i]) for i in range(3)]


def moving_knife(vals, trace=None) -> list:
    """Bewegliches Messer (Dubins–Spanier), beliebig viele Personen: das Messer wandert von links; wer zuerst ruft (das Stück links vom Messer ist ihr 1/n wert), bekommt es und scheidet aus; der Rest läuft weiter.
    Die letzte Person bekommt den Rest. Proportional, ab drei Personen nicht neidfrei. `trace` bekommt je Ruf ("ruf", Person, x)."""
    _check(vals)
    n, m = len(vals), len(vals[0])
    remaining = list(range(n))
    start = Fraction(0)
    out = {}
    while len(remaining) > 1:
        best = None
        for i in remaining:
            x = quantile(vals[i], start, Fraction(1, n))
            if best is None or x < best[0]:
                best = (x, i)
        out[best[1]] = [(start, best[0])]
        if trace is not None:
            trace.append(("ruf", best[1], best[0]))
        start = best[0]
        remaining.remove(best[1])
    out[remaining[0]] = [(start, Fraction(m))]
    return [normalize(out[i]) for i in range(n)]


def divide(protocol: str, vals, trace=None) -> list:
    if protocol == "geteilt":
        return cut_and_choose(vals, trace)
    if protocol == "selfridge":
        return selfridge_conway(vals, trace)
    if protocol == "messer":
        return moving_knife(vals, trace)
    raise ValueError(protocol)


# --- Bewertung einer Verteilung ---------------------------------------------------------------------------------------------------------------

def utilities(vals, pieces) -> list:
    return [piece_value(v, p) for v, p in zip(vals, pieces)]


def envy_matrix(vals, pieces) -> list:
    """Eintrag [i][k]: wie Person i das Stück von Person k bewertet."""
    return [[piece_value(vals[i], pieces[k]) for k in range(len(pieces))] for i in range(len(vals))]


def envy_pairs(vals, pieces, tol=0) -> list:
    """Paare (i, k), bei denen i das Stück von k höher bewertet als das eigene (um mehr als `tol`)."""
    mat = envy_matrix(vals, pieces)
    return [(i, k) for i in range(len(vals)) for k in range(len(vals)) if i != k and mat[i][k] - mat[i][i] > tol]


def is_envy_free(vals, pieces, tol=0) -> bool:
    return not envy_pairs(vals, pieces, tol)


def is_proportional(vals, pieces, tol=0) -> bool:
    n = len(vals)
    return all(u >= Fraction(1, n) - tol for u in utilities(vals, pieces))


def covers_cake(pieces, m) -> bool:
    """Die Stücke sind paarweise überschneidungsfrei und decken [0, m] vollständig ab."""
    spans = sorted(i for p in pieces for i in normalize(p))
    pos = Fraction(0)
    for a, b in spans:
        if a != pos:
            return False
        pos = b
    return pos == m


def shares(pieces, m) -> list:
    """Anteil x[i][j] der Zelle j, den Person i bekommt (exakt)."""
    return [[sum((max(Fraction(0), min(b, Fraction(j + 1)) - max(a, Fraction(j))) for a, b in p), Fraction(0)) for j in range(m)] for p in pieces]


# --- Lineare Programme --------------------------------------------------------------------------------------------------------------------------

def welfare_bound(vals) -> Fraction:
    """Höchste Summe der Nutzen ohne Nebenbedingung: jede Zelle an die Person, die sie am höchsten bewertet."""
    m = len(vals[0])
    return sum((max(v[j] for v in vals) for j in range(m)), Fraction(0))


def max_welfare_division(vals) -> list:
    """Jede Zelle ganz an die Person mit der höchsten Dichte (Gleichstand: kleinere Nummer); Stücke als Intervalle."""
    n, m = len(vals), len(vals[0])
    owner = [max(range(n), key=lambda i: (vals[i][j], -i)) for j in range(m)]
    return [normalize([(Fraction(j), Fraction(j + 1)) for j in range(m) if owner[j] == i]) for i in range(n)]


def optimize(vals, envy_free=False, proportional=False, floors=None):
    """Größte Summe der Nutzen unter Nebenbedingungen: Rückgabe (Wohlfahrt als float, x[i][j] als float-Matrix).

    Nebenbedingungen: neidfrei (kein Nutzen unter der Bewertung eines fremden Stücks), proportional (Nutzen ≥ 1/n), `floors` (Nutzen von Person i mindestens floors[i]). Für stückweise konstante Bewertungen
    genügen die Anteile je Zelle: innerhalb einer Zelle sind alle Teilstücke gleich viel wert."""
    _check(vals)
    n, m = len(vals), len(vals[0])
    f = [[float(d) for d in v] for v in vals]
    c = np.array([-f[i][j] for i in range(n) for j in range(m)])
    a_eq = np.zeros((m, n * m))
    for j in range(m):
        for i in range(n):
            a_eq[j, i * m + j] = 1
    a_ub, b_ub = [], []
    if envy_free:
        for i in range(n):
            for k in range(n):
                if i != k:
                    row = np.zeros(n * m)
                    for j in range(m):
                        row[k * m + j] += f[i][j]
                        row[i * m + j] -= f[i][j]
                    a_ub.append(row)
                    b_ub.append(0.0)
    lower = [1.0 / n] * n if proportional else [0.0] * n
    if floors is not None:
        lower = [max(lo, float(fl)) for lo, fl in zip(lower, floors)]
    for i in range(n):                                  # Untergrenze für den Nutzen (bei 0 eine überflüssige, immer erfüllte Zeile)
        row = np.zeros(n * m)
        for j in range(m):
            row[i * m + j] = -f[i][j]
        a_ub.append(row)
        b_ub.append(-lower[i] + 1e-12)
    res = linprog(c, A_ub=np.array(a_ub) if a_ub else None, b_ub=b_ub if b_ub else None, A_eq=a_eq, b_eq=np.ones(m), bounds=(0, 1), method="highs", options={"primal_feasibility_tolerance": 1e-10, "dual_feasibility_tolerance": 1e-10})
    if res.status != 0:
        raise ValueError("Das lineare Programm hat keine Lösung")
    x = [[float(res.x[i * m + j]) for j in range(m)] for i in range(n)]
    return float(-res.fun), x


def pieces_from_shares(x) -> list:
    """Aus Anteilen je Zelle Stücke bauen: in jeder Zelle liegen die Teilstücke der Personen hintereinander (in Nummernfolge); die letzte Person nimmt den Rest bis zum Zellenende."""
    n, m = len(x), len(x[0])
    out = [[] for _ in range(n)]
    for j in range(m):
        pos = Fraction(j)
        owners = [i for i in range(n) if x[i][j] > 1e-12]
        for idx, i in enumerate(owners):
            end = Fraction(j + 1) if idx == len(owners) - 1 else min(Fraction(j + 1), pos + Fraction(x[i][j]))
            out[i].append((pos, end))
            pos = end
    return [normalize(p) for p in out]


def float_utilities(vals, pieces) -> list:
    return [float(u) for u in utilities(vals, pieces)]


def pareto_improvement(vals, pieces):
    """Die größte Summe der Nutzen, wenn niemand schlechter gestellt werden darf als in `pieces`: Rückgabe (Wohlfahrt, x, ob eine Pareto-Verbesserung möglich ist)."""
    u = float_utilities(vals, pieces)
    w, x = optimize(vals, floors=u)
    return w, x, w > sum(u) + TOL


def is_pareto_efficient(vals, pieces) -> bool:
    return not pareto_improvement(vals, pieces)[2]
