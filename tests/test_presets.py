"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, keines auf dem oberen Rand der Teamzahl, keines durch eine einzelne Regleränderung vom Standard;
die Aussagen der Hilfetexte stimmen mit der Rechnung überein."""

from fractions import Fraction as F

import pytest

import kuc_algorithm as A
import kuc_constants as C
import kuc_evaluation as ev
import kuc_presets as P
import kuc_scenario as S

FIRST = "Drei Teams, zwölf Stunden"


def analyse(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_regler_bounds_and_options_exist():
    for name, p in C.PRESETS.items():
        assert C.N_MIN <= p["n"] <= C.N_MAX and 0 <= p["seed"] <= C.SEED_MAX, name
        assert p["model"] in C.MODELS and p["protocol"] in C.PROTOCOLS, name


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS[FIRST]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_no_preset_sits_on_the_upper_bound_of_n_and_two_teams_only_with_a_two_team_protocol():
    """Die untere Grenze 2 ist die kleinste sinnvolle Gruppe und gehört zu „Geteilt und gewählt“; die obere Grenze soll kein Preset belegen."""
    for name, p in C.PRESETS.items():
        assert p["n"] != C.N_MAX, name
        if p["n"] == C.N_MIN:
            assert p["protocol"] == "geteilt", name


def test_no_single_change_of_the_default_produces_another_preset():
    default = C.PRESETS[FIRST]
    for name, p in C.PRESETS.items():
        if name != FIRST:
            assert sum(1 for k in p if p[k] != default[k]) >= 2, name


def test_presets_are_pairwise_different():
    values = [tuple(sorted(p.items())) for p in C.PRESETS.values()]
    assert len(set(values)) == len(values)


def test_presets_with_weights_have_matching_n_and_a_fitting_protocol():
    for name, p in C.PRESETS.items():
        rows, err = S.parse_weights(p["weights"])
        assert err is None, name
        if rows is not None:
            assert p["n"] == len(rows), name
        need = C.PROTOCOL_PEOPLE[p["protocol"]]
        assert need is None or need == p["n"], name


def test_presets_have_no_input_errors_and_no_protocol_note():
    for name in C.PRESETS:
        a = analyse(name)
        assert a.errors == [] and a.note == "" and a.protocol == C.PRESETS[name]["protocol"], name


# --- Aussagen der Hilfetexte ---------------------------------------------------------------------------------------------------------------

def test_cut_and_choose_preset_help():
    a = analyse("Geteilt und gewählt verschenkt Wohlfahrt")
    d, fixed = a.divisions["protokoll"], a.divisions["nachgebessert"]
    assert ev.clock(A.cut_and_choose(a.vals)[1][0][1]) == "16:00"                      # Team 1 schneidet bei 16 Uhr, Team 2 bekommt links
    assert d.pieces == [[(8, 12)], [(0, 8)]] and d.ef and not d.pareto
    assert fixed.util[0] - d.util[0] == pytest.approx(0.25)                              # Team 1 gewinnt 25 Prozentpunkte
    assert fixed.util[1] == pytest.approx(9 / 11)                                         # Team 2 verliert nichts


def test_selfridge_conway_preset_help():
    a = analyse("Selfridge–Conway mit Kürzung")
    d = a.divisions["protokoll"]
    trim = next(e for e in a.trace if e[0] == "kuerzen")
    assert ev.clock(trim[2]) == "10:40" and trim[1] == 1
    assert [e[:3] for e in a.trace if e[0] == "wahl"][0] == ("wahl", 2, 1)              # Team 3 wählt das zweite Stück
    assert next(e for e in a.trace if e[0] == "teilen")[1] == 2                           # Team 3 teilt die Kürzung
    assert d.ef and [ev.pct(u) for u in d.util] == ["37,0 %", "38,9 %", "42,2 %"]


def test_moving_knife_preset_help():
    a = analyse("Bewegliches Messer: Neid ab drei Teams")
    d = a.divisions["protokoll"]
    assert [(e[1], ev.clock(e[2])) for e in a.trace if e[0] == "ruf"] == [(1, "12:00"), (0, "16:00")]
    assert d.envy == [(0, 2)] and A.envy_matrix(a.vals, d.pieces)[0][2] == F(1, 2) and d.util[0] == pytest.approx(1 / 3)


def test_price_of_envy_freeness_preset_help():
    a = analyse("Neidfreiheit kostet etwas")
    assert ev.pct(1 - a.ef_ratio) == "4,2 %" and a.divisions["protokoll"].ef
    assert not a.divisions["wohlfahrt"].ef                                                   # die höchste Wohlfahrt ist hier nicht neidfrei


def test_five_teams_preset_help():
    a = analyse("Fünf Teams, eigene Blöcke")
    assert a.n == 5 and ev.pct(a.divisions["protokoll"].ratio) == "40,1 %" and not a.divisions["protokoll"].ef
