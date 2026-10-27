"""Verdikte, Tabellen, Ablauftexte und Formatierung als reine Funktionen: jeder Zweig mit Beispielen, deren Text von Hand erwartet wird."""

from fractions import Fraction as F

import kuc_constants as C
import kuc_evaluation as ev

ONE = "1 1 1 1 1 1 1 1 1 1 1 1"


def analyse(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


# --- Formatierung -----------------------------------------------------------------------------------------------------------------------------

def test_formatting():
    assert ev.num(1.5, 2) == "1,50" and ev.num(-0.5) == "−0,5" and ev.pct(0.5) == "50,0 %" and ev.pct(-0.012) == "−1,2 %"
    assert ev.pct(None) == "–" and ev.pct(float("nan")) == "–" and ev.team(0) == "Team 1" and ev.yes_no(True) == "ja" and ev.yes_no(False) == "nein"


def test_clock_rounds_to_the_minute_half_up():
    assert ev.clock(F(0)) == "08:00" and ev.clock(F(12)) == "20:00"
    assert ev.clock(F(8, 3)) == "10:40" and ev.clock(F(28, 9)) == "11:07" and ev.clock(F(32, 9)) == "11:33"
    assert ev.clock(F(1, 120)) == "08:01" and ev.clock(F(1, 121)) == "08:00"          # 0,5 Minuten wird aufgerundet, weniger nicht
    assert ev.clock(F(119, 60) + F(1, 120)) == "10:00" and ev.clock(F(59, 60) + F(1, 120)) == "09:00"      # Minute 59,5 rundet auf die nächste Stunde


def test_piece_text_merges_and_marks_empty_pieces():
    assert ev.piece_text([(F(0), F(1)), (F(1), F(2)), (F(4), F(5))]) == "08:00–10:00, 12:00–13:00"
    assert ev.piece_text([]) == "–"


# --- Ablauftexte ------------------------------------------------------------------------------------------------------------------------------

def test_trace_of_cut_and_choose():
    assert ev.trace_lines(analyse("Geteilt und gewählt verschenkt Wohlfahrt")) == [
        "Team 1 schneidet bei 16:00: beide Seiten sind ihm je 50,0 % wert.",
        "Team 2 bewertet links mit 81,8 %, rechts mit 18,2 % und nimmt links; Team 1 bekommt die andere Seite.",
    ]


def test_trace_of_selfridge_conway_with_trimming():
    assert ev.trace_lines(analyse("Selfridge–Conway mit Kürzung")) == [
        "Team 1 schneidet bei 12:00 und 16:00 in drei Stücke, die ihm je 33,3 % wert sind.",
        "Team 2 kürzt das Stück 1 bei 10:40, bis es so viel wert ist wie sein zweitbestes.",
        "Es wählen: Team 3 Stück 2, Team 2 Stück 1, Team 1 Stück 3.",
        "Team 3 teilt die Kürzung in drei gleich bewertete Teile; es wählen Team 2, Team 1 und Team 3 in dieser Reihenfolge.",
    ]


def test_trace_of_selfridge_conway_without_trimming():
    a = ev.analyse(ev.Settings(n=3, protocol="selfridge", weights="\n".join([ONE] * 3)))
    lines = ev.trace_lines(a)
    assert lines[1] == "Team 2 hat zwei gleich hohe Spitzenwerte und muss nichts kürzen." and len(lines) == 3


def test_trace_of_the_moving_knife():
    assert ev.trace_lines(analyse("Bewegliches Messer: Neid ab drei Teams")) == [
        "Das Messer steht bei 12:00: Team 2 ruft (das Stück links ist ihm 33,3 % wert) und scheidet aus.",
        "Das Messer steht bei 16:00: Team 1 ruft (das Stück links ist ihm 33,3 % wert) und scheidet aus.",
        "Team 3 bekommt den Rest.",
    ]


# --- Tabellen ---------------------------------------------------------------------------------------------------------------------------------

def test_team_rows_of_the_selfridge_conway_example():
    rows = ev.team_rows(analyse("Selfridge–Conway mit Kürzung"))
    assert rows[0] == {"Team": "Team 1", "Stunden": "11:07–11:33, 16:00–20:00", "Blöcke": 2, "Nutzen": "37,0 %", "beneidet": "niemanden"}
    assert rows[1]["Stunden"] == "08:00–11:07" and rows[2]["Nutzen"] == "42,2 %"


def test_team_rows_name_the_envied_team():
    rows = ev.team_rows(analyse("Bewegliches Messer: Neid ab drei Teams"))
    assert [r["beneidet"] for r in rows] == ["Team 3", "niemanden", "niemanden"]


def test_envy_rows_by_hand():
    rows = ev.envy_rows(analyse("Bewegliches Messer: Neid ab drei Teams"))
    assert rows[0] == {"Bewertet von": "Team 1", "Stück von Team 1": "33,3 %", "Stück von Team 2": "16,7 %", "Stück von Team 3": "50,0 %"}


def test_compare_rows_by_hand():
    rows = ev.compare_rows(analyse("Geteilt und gewählt verschenkt Wohlfahrt"))
    assert [r["Verteilung"] for r in rows] == ["Geteilt und gewählt", "Höchste Wohlfahrt", "Neidfrei, beste Wohlfahrt", "Nachgebessert"]
    assert rows[0] == {"Verteilung": "Geteilt und gewählt", "Summe der Nutzen": "1,32", "Anteil an der Höchstwohlfahrt": "84,1 %", "neidfrei": "ja", "proportional": "ja", "Pareto-effizient": "nein", "Blöcke je Team": "1,0"}
    assert rows[1]["Summe der Nutzen"] == "1,57" and rows[1]["Pareto-effizient"] == "ja" and rows[3]["Anteil an der Höchstwohlfahrt"] == "100,0 %"


# --- verdict_state ----------------------------------------------------------------------------------------------------------------------------

def test_verdict_for_an_inefficient_envy_free_protocol():
    kind, text = ev.verdict_state(analyse("Geteilt und gewählt verschenkt Wohlfahrt"))
    assert kind == "warning" and text == (
        "Geteilt und gewählt: neidfrei, proportional, NICHT Pareto-effizient. Die Summe der Nutzen ist 84,1 % der Höchstwohlfahrt. "
        "Ohne dass ein Team schlechter dasteht und ohne Neid, wären 100,0 % drin (+15,9 Punkte). Die beste neidfreie Verteilung erreicht 100,0 % der Höchstwohlfahrt: Neidfreiheit selbst kostet 0,0 %.")


def test_verdict_for_the_knife_names_who_envies():
    kind, text = ev.verdict_state(analyse("Bewegliches Messer: Neid ab drei Teams"))
    assert kind == "warning" and text.startswith("Bewegliches Messer: NICHT neidfrei (Team 1 beneidet Team 3), proportional, NICHT Pareto-effizient.")
    assert "Ohne dass ein Team schlechter dasteht, wären 93,3 % drin (+13,3 Punkte)." in text and "Neidfreiheit selbst kostet 6,7 %." in text


def test_verdict_success_when_the_protocol_is_envy_free_and_efficient():
    a = ev.analyse(ev.Settings(n=2, protocol="geteilt", weights="\n".join([ONE] * 2)))      # gleiche Bewertungen: jede Verteilung ist effizient
    kind, text = ev.verdict_state(a)
    assert kind == "success" and text.startswith("Geteilt und gewählt: neidfrei, proportional, Pareto-effizient. Die Summe der Nutzen ist 100,0 %")
    assert "Ohne dass" not in text


# --- Analyse ----------------------------------------------------------------------------------------------------------------------------------

def test_protocol_that_does_not_fit_falls_back_to_the_knife_with_a_note():
    a = ev.analyse(ev.Settings(n=4, protocol="selfridge"))
    assert a.protocol == "messer" and a.note == "„Selfridge–Conway“ gilt nur für 3 Teams; gezeigt wird das bewegliche Messer."
    b = ev.analyse(ev.Settings(n=3, protocol="geteilt"))
    assert b.protocol == "messer" and b.note.startswith("„Geteilt und gewählt“ gilt nur für 2 Teams")


def test_invalid_weights_fall_back_to_generated_ones_with_a_message():
    a = ev.analyse(ev.Settings(n=3, weights="1 2 3"))
    assert a.source == "erzeugt" and a.n == 3
    assert a.errors == ["Eigene Bewertungen: Es müssen 2 bis 6 Zeilen sein, eine je Team (eingegeben: 1). Die Eingabe wird ignoriert."]


def test_weights_override_the_number_of_teams():
    a = ev.analyse(ev.Settings(n=5, weights="\n".join([ONE] * 2)))
    assert a.source == "eingegeben" and a.n == 2 and a.errors == []


def test_divisions_contain_the_protocol_and_three_references():
    a = ev.analyse(ev.Settings())
    assert list(a.divisions) == ["protokoll", "wohlfahrt", "neidfrei", "nachgebessert"]
    assert a.divisions["wohlfahrt"].ratio == 1.0 and a.bound > 0
    assert 0 < a.ef_ratio <= a.prop_ratio <= 1 + 1e-9


# --- Reihen-Verdikte mit künstlichen Zeilen ---------------------------------------------------------------------------------------------------

def _price_rows():
    base = {"runs": 100, "prop_mean": 0.99, "prop_min": 0.9, "ef_free": 10}
    return [{"n": 2, "model": "unabh", "ef_mean": 0.99, "ef_min": 0.95, **base}, {"n": 3, "model": "aehnlich", "ef_mean": 0.97, "ef_min": 0.85, **base}]


def test_verdict_price():
    kind, text = ev.verdict_price(_price_rows())
    assert kind == "info" and text == ("Über 200 Instanzen kostet Neidfreiheit im Mittel 2,0 % der Höchstwohlfahrt; der schlechteste Fall (3 Teams, Ähnlich) verliert 15,0 %. "
                                       "Bei diesen Vorlieben gibt, wer Neidfreiheit verlangt, kaum Wohlfahrt auf.")


def _protocol_rows():
    rows = []
    for protocol, n in C.SERIES_PROTOCOL_CASES:
        rows.append({"protocol": protocol, "n": n, "model": "unabh", "runs": 100, "ef": 100 if (protocol != "messer" or n == 2) else 0, "prop": 100, "pareto": 1, "ratio_sum": 0.8 - 0.01 * n, "fixed_sum": 0.99})
    return rows


def test_verdict_protocols():
    kind, text = ev.verdict_protocols(_protocol_rows())
    assert kind == "warning" and text == (
        "Geteilt und gewählt und Selfridge–Conway sind in allen Instanzen neidfrei und proportional, das Messer ab drei Teams in 0 von 300 Instanzen neidfrei (proportional immer). "
        "Pareto-effizient ist über alle Zeilen nur 1,0 %; die Summe der Nutzen liegt bei 78,0 % (Geteilt und gewählt, 2 Teams), 77,0 % (Selfridge–Conway) und 75,0 % (Messer, 5 Teams) der Höchstwohlfahrt.")


def test_verdict_blocks():
    rows = [{"n": 2, "runs": 10, "messer": 1.0, "wohlfahrt": 3.0, "neidfrei": 3.5}, {"n": 5, "runs": 10, "messer": 1.0, "wohlfahrt": 2.0, "neidfrei": 2.5}]
    kind, text = ev.verdict_blocks(rows)
    assert kind == "info" and text == ("Bei 5 Teams bekommt ein Team beim Messer im Mittel 1,0 Block, bei höchster Wohlfahrt 2,0, bei der besten neidfreien Verteilung 2,5 Blöcke: wer Effizienz will, zerlegt die Hallenzeit (bei den LP-Verteilungen hängt die Zahl von der gewählten Lösung ab).")


def test_series_tables_format_the_rows():
    row = ev.price_table(_price_rows())[0]
    assert row == {"Teams": 2, "Vorlieben": "Unabhängig", "Instanzen": 100, "neidfrei: Mittel": "99,0 %", "neidfrei: schlechtester Fall": "95,0 %", "proportional: Mittel": "99,0 %", "ohne Verlust": "10 von 100"}
    prow = ev.protocol_table(_protocol_rows())[3]
    assert prow == {"Protokoll": "Bewegliches Messer", "Teams": 3, "Vorlieben": "Unabhängig", "neidfrei": "0 von 100", "proportional": "100 von 100", "Pareto-effizient": "1 von 100", "Summe der Nutzen": "77,0 %", "nachgebessert": "99,0 %"}
    brow = ev.block_table([{"n": 3, "runs": 5, "messer": 1.0, "wohlfahrt": 2.8933, "neidfrei": 3.16}])[0]
    assert brow == {"Teams": 3, "Bewegliches Messer": "1,00", "Höchste Wohlfahrt": "2,89", "Neidfrei, beste Wohlfahrt": "3,16"}
