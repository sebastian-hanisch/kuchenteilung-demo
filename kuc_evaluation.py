"""Auswertung: Einstellungen, Verteilungen (Protokoll und Referenzen), Kennzahlen, Tabellen, Verdikte als reine Funktionen (ohne Streamlit) und die festen Reihen."""

import math
from dataclasses import dataclass
from fractions import Fraction

import kuc_algorithm as A
import kuc_constants as C
import kuc_scenario as S


def num(x: float, digits: int = 1) -> str:
    return f"{x:.{digits}f}".replace(".", ",").replace("-", "−")


def pct(x, digits: int = 1) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    return f"{100 * x:.{digits}f} %".replace(".", ",").replace("-", "−")


def team(i: int) -> str:
    return f"Team {i + 1}"


def clock(x) -> str:
    """Uhrzeit zu einem Punkt des Kuchens (0 = Beginn, Zelleneinheit = Stunde), auf die Minute gerundet (halbe Minuten nach oben)."""
    minutes = math.floor(Fraction(x) * 60 + Fraction(1, 2))
    return f"{C.START_HOUR + minutes // 60:02d}:{minutes % 60:02d}"


def piece_text(piece) -> str:
    return ", ".join(f"{clock(a)}–{clock(b)}" for a, b in A.normalize(piece)) or "–"


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    model: str = C.DEFAULT_MODEL
    seed: int = C.DEFAULT_SEED
    protocol: str = C.DEFAULT_PROTOCOL
    weights: str = ""


@dataclass
class Division:
    key: str             # "protokoll" oder ein Schlüssel aus REFERENCES
    name: str
    pieces: list         # je Team eine Liste von Intervallen
    util: list           # Nutzen je Team (float)
    welfare: float       # Summe der Nutzen
    ratio: float         # Wohlfahrt geteilt durch die höchste Wohlfahrt
    envy: list           # Paare (i, k): i beneidet k
    prop: bool
    pareto: bool
    frags: list          # Zahl der Blöcke je Team
    exact: bool          # exakt gerechnet (Protokoll) oder numerisch (LP)

    @property
    def ef(self) -> bool:
        return not self.envy


@dataclass
class Analysis:
    settings: Settings
    weights: list
    vals: list
    source: str          # "eingegeben" oder "erzeugt"
    errors: list
    n: int
    protocol: str        # tatsächlich gerechnetes Protokoll
    note: str            # Hinweis, falls das gewählte Protokoll nicht passte
    trace: list
    bound: float         # höchste Wohlfahrt ohne Nebenbedingung
    divisions: dict      # Schlüssel -> Division
    ef_ratio: float      # beste neidfreie Wohlfahrt / höchste Wohlfahrt
    prop_ratio: float    # beste proportionale Wohlfahrt / höchste Wohlfahrt


def make_division(key, name, vals, pieces, exact, bound) -> Division:
    tol = 0 if exact else A.TOL
    u = A.utilities(vals, pieces)
    welfare = float(sum(u))
    return Division(
        key=key, name=name, pieces=pieces, util=[float(x) for x in u], welfare=welfare, ratio=welfare / bound,
        envy=A.envy_pairs(vals, pieces, tol), prop=A.is_proportional(vals, pieces, tol), pareto=A.is_pareto_efficient(vals, pieces),
        frags=[A.fragments(p) for p in pieces], exact=exact,
    )


def analyse(settings: Settings) -> Analysis:
    errors, note = [], ""
    rows, err = S.parse_weights(settings.weights)
    if err:
        errors.append("Eigene Bewertungen: " + err + " Die Eingabe wird ignoriert.")
    if rows is not None:
        weights, source = rows, "eingegeben"
    else:
        weights, source = S.make_weights(settings.model, settings.n, settings.seed), "erzeugt"
    n = len(weights)
    vals = [A.valuation(w) for w in weights]
    protocol = settings.protocol
    need = C.PROTOCOL_PEOPLE[protocol]
    if need is not None and need != n:
        note = f"„{C.PROTOCOL_SHORT[protocol]}“ gilt nur für {need} Teams; gezeigt wird das bewegliche Messer."
        protocol = "messer"
    trace = []
    pieces = A.divide(protocol, vals, trace)
    bound = float(A.welfare_bound(vals))
    divisions = {"protokoll": make_division("protokoll", C.PROTOCOL_SHORT[protocol], vals, pieces, True, bound)}
    divisions["wohlfahrt"] = make_division("wohlfahrt", C.REFERENCE_SHORT["wohlfahrt"], vals, A.max_welfare_division(vals), True, bound)
    _, x = A.optimize(vals, envy_free=True)
    divisions["neidfrei"] = make_division("neidfrei", C.REFERENCE_SHORT["neidfrei"], vals, A.pieces_from_shares(x), False, bound)
    base = divisions["protokoll"]
    _, x = A.optimize(vals, envy_free=base.ef, floors=base.util)
    divisions["nachgebessert"] = make_division("nachgebessert", C.REFERENCE_SHORT["nachgebessert"], vals, A.pieces_from_shares(x), False, bound)
    ef_w, _ = A.optimize(vals, envy_free=True)
    prop_w, _ = A.optimize(vals, proportional=True)
    return Analysis(settings=settings, weights=weights, vals=vals, source=source, errors=errors, n=n, protocol=protocol, note=note, trace=trace, bound=bound,
                    divisions=divisions, ef_ratio=ef_w / bound, prop_ratio=prop_w / bound)


# --- Tabellen und Texte ---------------------------------------------------------------------------------------------------------------------

def yes_no(flag: bool) -> str:
    return "ja" if flag else "nein"


def team_rows(a: Analysis) -> list:
    d = a.divisions["protokoll"]
    envied = {i: [team(k) for (j, k) in d.envy if j == i] for i in range(a.n)}
    return [{"Team": team(i), "Stunden": piece_text(d.pieces[i]), "Blöcke": d.frags[i], "Nutzen": pct(d.util[i]), "beneidet": ", ".join(envied[i]) or "niemanden"} for i in range(a.n)]


def envy_rows(a: Analysis) -> list:
    """Wie jedes Team (Zeile) das Stück jedes Teams (Spalte) bewertet, in Prozent des ganzen Kuchens."""
    mat = A.envy_matrix(a.vals, a.divisions["protokoll"].pieces)
    return [{"Bewertet von": team(i), **{f"Stück von {team(k)}": pct(float(mat[i][k])) for k in range(a.n)}} for i in range(a.n)]


def compare_rows(a: Analysis) -> list:
    rows = []
    for key in ("protokoll", "wohlfahrt", "neidfrei", "nachgebessert"):
        d = a.divisions[key]
        rows.append({
            "Verteilung": d.name, "Summe der Nutzen": num(d.welfare, 2), "Anteil an der Höchstwohlfahrt": pct(d.ratio),
            "neidfrei": yes_no(d.ef), "proportional": yes_no(d.prop), "Pareto-effizient": yes_no(d.pareto), "Blöcke je Team": num(sum(d.frags) / a.n, 1),
        })
    return rows


def trace_lines(a: Analysis) -> list:
    """Der Ablauf des gewählten Protokolls in Worten."""
    lines = []
    tr = a.trace
    if a.protocol == "geteilt":
        cut = next(e for e in tr if e[0] == "schnitt")
        pick = next(e for e in tr if e[0] == "wahl")
        v2 = a.vals[1]
        left, right = A.piece_value(v2, [(Fraction(0), cut[2])]), A.piece_value(v2, [(cut[2], Fraction(len(v2)))])
        lines.append(f"{team(0)} schneidet bei {clock(cut[2])}: beide Seiten sind ihm je 50,0 % wert.")
        lines.append(f"{team(1)} bewertet links mit {pct(float(left))}, rechts mit {pct(float(right))} und nimmt {pick[2]}; {team(0)} bekommt die andere Seite.")
    elif a.protocol == "selfridge":
        cuts = [e for e in tr if e[0] == "schnitt"]
        lines.append(f"{team(0)} schneidet bei {clock(cuts[0][2])} und {clock(cuts[1][2])} in drei Stücke, die ihm je 33,3 % wert sind.")
        trim = next(e for e in tr if e[0] == "kuerzen")
        if trim[2] is None:
            lines.append(f"{team(1)} hat zwei gleich hohe Spitzenwerte und muss nichts kürzen.")
        else:
            lines.append(f"{team(1)} kürzt das Stück {trim[3] + 1} bei {clock(trim[2])}, bis es so viel wert ist wie sein zweitbestes.")
        picks = [e for e in tr if e[0] == "wahl"]
        lines.append("Es wählen: " + ", ".join(f"{team(p)} Stück {k + 1}" for _, p, k in picks) + ".")
        split = next((e for e in tr if e[0] == "teilen"), None)
        if split:
            lines.append(f"{team(split[1])} teilt die Kürzung in drei gleich bewertete Teile; es wählen {team(split[2])}, {team(0)} und {team(split[1])} in dieser Reihenfolge.")
    else:
        for _, who, x in (e for e in tr if e[0] == "ruf"):
            lines.append(f"Das Messer steht bei {clock(x)}: {team(who)} ruft (das Stück links ist ihm {pct(1 / a.n)} wert) und scheidet aus.")
        last = next(i for i in range(a.n) if i not in {e[1] for e in tr})
        lines.append(f"{team(last)} bekommt den Rest.")
    return lines


# --- Verdikte -------------------------------------------------------------------------------------------------------------------------------

def verdict_state(a: Analysis):
    """Kernfrage: was kann das Protokoll, und was kostet es? Rückgabe (st-Methode, Text)."""
    d = a.divisions["protokoll"]
    fixed = a.divisions["nachgebessert"]
    parts = [f"{d.name}: {'neidfrei' if d.ef else 'NICHT neidfrei (' + ', '.join(f'{team(i)} beneidet {team(k)}' for i, k in d.envy) + ')'}, {'proportional' if d.prop else 'NICHT proportional'}, "
             f"{'Pareto-effizient' if d.pareto else 'NICHT Pareto-effizient'}."]
    parts.append(f"Die Summe der Nutzen ist {pct(d.ratio)} der Höchstwohlfahrt.")
    if not d.pareto:
        parts.append(f"Ohne dass ein Team schlechter dasteht{'' if not d.ef else ' und ohne Neid'}, wären {pct(fixed.ratio)} drin (+{num(100 * (fixed.ratio - d.ratio), 1)} Punkte).")
    parts.append(f"Die beste neidfreie Verteilung erreicht {pct(a.ef_ratio)} der Höchstwohlfahrt: Neidfreiheit selbst kostet {pct(1 - a.ef_ratio)}.")
    return ("success" if d.ef and d.pareto else "warning"), " ".join(parts)


def verdict_price(rows):
    """Reihe 1: was kostet Neidfreiheit, was Proportionalität? Rückgabe (st-Methode, Text)."""
    mean_ef = sum(r["ef_mean"] * r["runs"] for r in rows) / sum(r["runs"] for r in rows)
    worst = min(rows, key=lambda r: r["ef_min"])
    tot = sum(r["runs"] for r in rows)
    text = (f"Über {tot:,} Instanzen".replace(",", ".") + f" kostet Neidfreiheit im Mittel {pct(1 - mean_ef)} der Höchstwohlfahrt; der schlechteste Fall ({worst['n']} Teams, {C.MODEL_SHORT[worst['model']]}) verliert {pct(1 - worst['ef_min'])}. "
            "Bei diesen Vorlieben gibt, wer Neidfreiheit verlangt, kaum Wohlfahrt auf.")
    return "info", text


def verdict_protocols(rows):
    """Reihe 2: Protokolle im Vergleich. Rückgabe (st-Methode, Text)."""
    def agg(proto, n, key):
        sel = [r for r in rows if r["protocol"] == proto and r["n"] == n]
        return sum(r[key] * r["runs"] for r in sel) / sum(r["runs"] for r in sel)

    pareto_total = sum(r["pareto"] for r in rows) / sum(r["runs"] for r in rows)
    ds3_ef = sum(r["ef"] for r in rows if r["protocol"] == "messer" and r["n"] >= 3)
    ds3_runs = sum(r["runs"] for r in rows if r["protocol"] == "messer" and r["n"] >= 3)
    text = (f"Geteilt und gewählt und Selfridge–Conway sind in allen Instanzen neidfrei und proportional, das Messer ab drei Teams in {ds3_ef} von {ds3_runs} Instanzen neidfrei (proportional immer). "
            f"Pareto-effizient ist über alle Zeilen nur {pct(pareto_total)}; die Summe der Nutzen liegt bei {pct(agg('geteilt', 2, 'ratio_sum'))} (Geteilt und gewählt, 2 Teams), "
            f"{pct(agg('selfridge', 3, 'ratio_sum'))} (Selfridge–Conway) und {pct(agg('messer', 5, 'ratio_sum'))} (Messer, 5 Teams) der Höchstwohlfahrt.")
    return "warning", text


def verdict_blocks(rows):
    """Reihe 3: Zersplitterung. Rückgabe (st-Methode, Text)."""
    big = rows[-1]
    text = (f"Bei {big['n']} Teams bekommt ein Team beim Messer im Mittel {num(big['messer'], 1)} Block, bei höchster Wohlfahrt {num(big['wohlfahrt'], 1)}, "
            f"bei der besten neidfreien Verteilung {num(big['neidfrei'], 1)} Blöcke: wer Effizienz will, zerlegt die Hallenzeit.")
    return "info", text


# --- Feste Reihen ---------------------------------------------------------------------------------------------------------------------------

def _instance(model, n, seed):
    return [A.valuation(w) for w in S.make_weights(model, n, seed)]


def series_price() -> list:
    """Je Zahl der Teams und Modell: beste neidfreie bzw. proportionale Wohlfahrt im Verhältnis zur Höchstwohlfahrt (Mittel und schlechtester Fall)."""
    rows = []
    for mi, model in enumerate(C.MODELS):
        for n in C.SERIES_NS:
            ef, prop = [], []
            for run in range(C.SERIES_RUNS):
                vals = _instance(model, n, C.SERIES_SEED + 10000 * mi + 1000 * n + run)
                bound = float(A.welfare_bound(vals))
                ef.append(A.optimize(vals, envy_free=True)[0] / bound)
                prop.append(A.optimize(vals, proportional=True)[0] / bound)
            rows.append({"n": n, "model": model, "runs": C.SERIES_RUNS, "ef_mean": sum(ef) / len(ef), "ef_min": min(ef), "prop_mean": sum(prop) / len(prop), "prop_min": min(prop),
                         "ef_free": sum(r >= 1 - A.TOL for r in ef)})
    return rows


def series_protocols() -> list:
    """Je Protokoll, Zahl der Teams und Modell: Anteile neidfrei, proportional, Pareto-effizient und mittleres Wohlfahrtsverhältnis (Protokoll und nachgebessert)."""
    rows = []
    for mi, model in enumerate(C.MODELS):
        for ci, (protocol, n) in enumerate(C.SERIES_PROTOCOL_CASES):
            ef = prop = pareto = 0
            ratio, fixed = [], []
            for run in range(C.SERIES_RUNS):
                vals = _instance(model, n, C.SERIES_SEED + 100000 + 10000 * mi + 1000 * ci + run)
                bound = float(A.welfare_bound(vals))
                pieces = A.divide(protocol, vals)
                u = A.float_utilities(vals, pieces)
                is_ef = A.is_envy_free(vals, pieces)
                ef += is_ef
                prop += A.is_proportional(vals, pieces)
                w_par, _, improvable = A.pareto_improvement(vals, pieces)
                pareto += not improvable
                ratio.append(sum(u) / bound)
                fixed.append((A.optimize(vals, envy_free=True, floors=u)[0] if is_ef else w_par) / bound)
            rows.append({"protocol": protocol, "n": n, "model": model, "runs": C.SERIES_RUNS, "ef": ef, "prop": prop, "pareto": pareto,
                         "ratio_sum": sum(ratio) / len(ratio), "fixed_sum": sum(fixed) / len(fixed)})
    return rows


def series_blocks() -> list:
    """Je Zahl der Teams: mittlere Zahl der Blöcke je Team beim Messer, bei höchster Wohlfahrt und bei der besten neidfreien Verteilung (unabhängige Vorlieben)."""
    rows = []
    for n in C.SERIES_NS:
        acc = {"messer": [], "wohlfahrt": [], "neidfrei": []}
        for run in range(C.SERIES_RUNS):
            vals = _instance("unabh", n, C.SERIES_SEED + 200000 + 1000 * n + run)
            acc["messer"].append(sum(A.fragments(p) for p in A.moving_knife(vals)) / n)
            acc["wohlfahrt"].append(sum(A.fragments(p) for p in A.max_welfare_division(vals)) / n)
            acc["neidfrei"].append(sum(A.fragments(p) for p in A.pieces_from_shares(A.optimize(vals, envy_free=True)[1])) / n)
        rows.append({"n": n, "runs": C.SERIES_RUNS, **{k: sum(v) / len(v) for k, v in acc.items()}})
    return rows


def price_table(rows) -> list:
    return [{"Teams": r["n"], "Vorlieben": C.MODEL_SHORT[r["model"]], "Instanzen": r["runs"], "neidfrei: Mittel": pct(r["ef_mean"]), "neidfrei: schlechtester Fall": pct(r["ef_min"]),
             "proportional: Mittel": pct(r["prop_mean"]), "ohne Verlust": f"{r['ef_free']} von {r['runs']}"} for r in rows]


def protocol_table(rows) -> list:
    return [{"Protokoll": C.PROTOCOL_SHORT[r["protocol"]], "Teams": r["n"], "Vorlieben": C.MODEL_SHORT[r["model"]], "neidfrei": f"{r['ef']} von {r['runs']}", "proportional": f"{r['prop']} von {r['runs']}",
             "Pareto-effizient": f"{r['pareto']} von {r['runs']}", "Summe der Nutzen": pct(r["ratio_sum"]), "nachgebessert": pct(r["fixed_sum"])} for r in rows]


def block_table(rows) -> list:
    return [{"Teams": r["n"], "Bewegliches Messer": num(r["messer"], 2), "Höchste Wohlfahrt": num(r["wohlfahrt"], 2), "Neidfrei, beste Wohlfahrt": num(r["neidfrei"], 2)} for r in rows]
