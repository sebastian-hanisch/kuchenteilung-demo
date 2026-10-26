"""Randfälle: Extremwerte der Regler, Invarianten jeder Analyse, Gleichstände und Nullgewichte, Adresszeile und eigene Eingaben."""

import itertools
import os
from fractions import Fraction as F

import pytest
from streamlit.testing.v1 import AppTest

import kuc_algorithm as A
import kuc_constants as C
import kuc_evaluation as ev

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
GRID = list(itertools.product((C.N_MIN, 3, C.N_MAX), tuple(C.MODELS), (0, C.SEED_MAX), tuple(C.PROTOCOLS)))


@pytest.mark.parametrize("n,model,seed,protocol", GRID)
def test_invariants_at_the_extremes(n, model, seed, protocol):
    a = ev.analyse(ev.Settings(n=n, model=model, seed=seed, protocol=protocol))
    need = C.PROTOCOL_PEOPLE[protocol]
    assert a.n == n and a.protocol == (protocol if need in (None, n) else "messer") and bool(a.note) == (need not in (None, n))
    for key, d in a.divisions.items():
        assert len(d.pieces) == n and len(d.util) == n and len(d.frags) == n, key
        assert abs(sum(d.util) - d.welfare) < 1e-12 and 0 < d.ratio <= 1 + 1e-9, key
        assert A.covers_cake(d.pieces, C.CELLS), key
    p = a.divisions["protokoll"]
    assert p.prop and (p.ef or a.protocol == "messer" and n >= 3)                          # Proportionalität immer; Neidfreiheit außer beim Messer ab drei Teams
    assert a.divisions["wohlfahrt"].ratio == pytest.approx(1.0) and a.divisions["neidfrei"].ef and a.divisions["nachgebessert"].pareto
    assert a.divisions["nachgebessert"].ratio >= p.ratio - 1e-9
    assert a.divisions["neidfrei"].ratio == pytest.approx(a.ef_ratio) and a.ef_ratio <= a.prop_ratio + 1e-9
    kind, text = ev.verdict_state(a)
    assert kind in ("warning", "success") and text
    assert len(ev.team_rows(a)) == n and len(ev.envy_rows(a)) == n and len(ev.compare_rows(a)) == 4 and ev.trace_lines(a)


def test_a_single_hour_wanted_by_both_teams():
    row = "0 0 0 0 0 0 0 0 0 0 0 9"
    a = ev.analyse(ev.Settings(protocol="geteilt", weights="\n".join([row, row])))
    p = a.divisions["protokoll"]
    # alles hängt an der letzten Stunde: Team 1 schneidet bei 19:30, beide Seiten sind Team 2 gleich viel wert (Gleichstand: die linke Seite geht an Team 2)
    assert ev.piece_text(p.pieces[0]) == "19:30–20:00" and ev.piece_text(p.pieces[1]) == "08:00–19:30"
    assert p.util == [0.5, 0.5] and p.ef and p.pareto


def test_hours_nobody_wants_are_still_assigned():
    a = ev.analyse(ev.Settings(n=3, protocol="selfridge", weights="\n".join(["0 0 0 0 0 0 5 5 5 5 5 5"] * 3)))
    for d in a.divisions.values():
        assert A.covers_cake(d.pieces, C.CELLS)
    assert a.divisions["protokoll"].ef and a.divisions["protokoll"].util == pytest.approx([1 / 3] * 3)


def test_identical_teams_get_equal_shares_and_no_envy_in_every_protocol():
    rows = "\n".join(["2 7 1 9 4 4 0 3 8 1 6 5"] * 3)
    for protocol in ("selfridge", "messer"):
        a = ev.analyse(ev.Settings(protocol=protocol, weights=rows))
        d = a.divisions["protokoll"]
        assert d.util == pytest.approx([1 / 3] * 3) and d.ef, protocol                       # gleiche Bewertungen: alle Stücke gleich viel wert, kein Neid
        assert d.pareto and a.ef_ratio == pytest.approx(1.0)


def test_team_with_a_single_wanted_hour_in_a_big_group():
    rows = ["0 0 0 0 0 0 0 0 0 0 0 1"] + ["1 1 1 1 1 1 1 1 1 1 1 1"] * 5
    a = ev.analyse(ev.Settings(weights="\n".join(rows)))
    assert a.n == 6 and a.divisions["protokoll"].prop
    assert A.covers_cake(a.divisions["protokoll"].pieces, C.CELLS)


def test_default_settings_give_the_known_numbers():
    a = ev.analyse(ev.Settings())
    assert a.n == 3 and a.protocol == "messer" and ev.pct(a.divisions["protokoll"].ratio) == "77,3 %"
    assert [ev.clock(e[2]) for e in a.trace if e[0] == "ruf"] == ["12:00", "14:58"]


# --- App: Adresszeile und eigene Eingaben ------------------------------------------------------------------------------------------------------

def _run(**params):
    at = AppTest.from_file(APP, default_timeout=180)
    for k, v in params.items():
        at.query_params[k] = v
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_permalink_with_multi_line_weights_fills_the_text_area_and_disables_the_generator():
    at = _run(weights="1 1 1 1 1 1 1 1 1 1 1 1\n1 2 1 2 1 2 1 2 1 2 1 2", protocol="geteilt")
    assert at.sidebar.text_area(key="weights_text").value.count("\n") == 1
    assert at.sidebar.slider(key="n_slider").proto.disabled and at.sidebar.selectbox(key="model_select").disabled
    assert at.sidebar.selectbox(key="protocol_select").value == "geteilt" and at.metric[0].label == "Geteilt und gewählt: neidfrei"


def test_permalink_values_are_clamped_and_bad_values_ignored():
    at = _run(n="99", model="nichts", protocol="kuchen", seed="-3")
    assert at.sidebar.slider(key="n_slider").value == C.N_MAX and at.sidebar.selectbox(key="model_select").value == C.DEFAULT_MODEL
    assert at.sidebar.selectbox(key="protocol_select").value == C.DEFAULT_PROTOCOL and at.sidebar.number_input(key="seed_input").value == 0


def test_long_text_from_the_address_line_is_cut():
    at = _run(weights="1 " * 500)
    assert len(at.sidebar.text_area(key="weights_text").value) <= 400


def test_bad_weights_show_a_warning_and_the_app_still_runs():
    at = _run(weights="1 2 x")
    assert any("Eigene Bewertungen" in w.value for w in at.warning)
    assert not at.sidebar.slider(key="n_slider").proto.disabled


def test_protocol_that_does_not_fit_shows_a_note():
    at = _run(n="4", protocol="selfridge")
    assert any("gilt nur für 3 Teams" in i.value for i in at.info) and at.metric[0].label == "Bewegliches Messer: neidfrei"


def test_changing_the_number_of_teams_keeps_the_app_running():
    at = _run()
    for n in (2, 6, 4):
        at.sidebar.slider(key="n_slider").set_value(n).run()
        assert not at.exception and "Bewegliches Messer" in at.metric[0].label


def test_exact_quantities_in_the_analysis_are_fractions():
    a = ev.analyse(ev.Settings())
    trace_x = [e[2] for e in a.trace if e[0] == "ruf"]
    assert all(isinstance(x, F) for x in trace_x)
