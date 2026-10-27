"""Zahlen der README (Befunde): jede dort genannte Zahl steht hier als Behauptung, gerechnet mit den festen Zufalls-Seeds der Reihen."""

import pytest

import kuc_constants as C
import kuc_evaluation as ev


@pytest.fixture(scope="module")
def price():
    return ev.series_price()


@pytest.fixture(scope="module")
def protocols():
    return ev.series_protocols()


@pytest.fixture(scope="module")
def blocks():
    return ev.series_blocks()


def row(rows, **kw):
    return next(r for r in rows if all(r[k] == v for k, v in kw.items()))


# --- Reihe 1: Preis der Neidfreiheit ----------------------------------------------------------------------------------------------------------

def test_price_of_envy_freeness_mean_and_worst_case(price):
    expected = {  # (Teams, Vorlieben): (Mittel, schlechtester Fall) der besten neidfreien Wohlfahrt im Verhältnis zur Höchstwohlfahrt
        (2, "unabh"): (0.99955, 0.98922), (3, "unabh"): (0.99698, 0.96936), (4, "unabh"): (0.99284, 0.94823), (5, "unabh"): (0.98543, 0.94043),
        (2, "aehnlich"): (0.99377, 0.96585), (3, "aehnlich"): (0.98873, 0.95779), (4, "aehnlich"): (0.98323, 0.93758), (5, "aehnlich"): (0.98056, 0.90766),
    }
    for (n, model), (mean, worst) in expected.items():
        r = row(price, n=n, model=model)
        assert r["ef_mean"] == pytest.approx(mean, abs=6e-6) and r["ef_min"] == pytest.approx(worst, abs=6e-6), (n, model)


def test_opposite_preferences_cost_nothing(price):
    for r in (r for r in price if r["model"] == "gegen"):
        assert r["ef_mean"] == pytest.approx(1.0) and r["ef_min"] == pytest.approx(1.0) and r["ef_free"] == r["runs"]


def test_how_often_the_highest_welfare_is_already_envy_free(price):
    assert {(r["n"], r["model"]): r["ef_free"] for r in price if r["model"] != "gegen"} == {
        (2, "unabh"): 174, (3, "unabh"): 97, (4, "unabh"): 23, (5, "unabh"): 6, (2, "aehnlich"): 52, (3, "aehnlich"): 17, (4, "aehnlich"): 2, (5, "aehnlich"): 0}


def test_proportionality_costs_less_than_envy_freeness_and_the_price_grows_with_the_group(price):
    for r in price:
        assert r["prop_mean"] >= r["ef_mean"] - 1e-9 and r["prop_min"] >= r["ef_min"] - 1e-9
    for model in ("unabh", "aehnlich"):
        means = [row(price, n=n, model=model)["ef_mean"] for n in C.SERIES_NS]
        assert means == sorted(means, reverse=True)


def test_price_verdict(price):
    kind, text = ev.verdict_price(price)
    assert text == ("Über 2.400 Instanzen kostet Neidfreiheit im Mittel 0,7 % der Höchstwohlfahrt; der schlechteste Fall (5 Teams, Ähnlich) verliert 9,2 %. "
                    "Bei diesen Vorlieben gibt, wer Neidfreiheit verlangt, kaum Wohlfahrt auf.")


def test_price_table_strings(price):
    t = ev.price_table(price)
    assert t[0] == {"Teams": 2, "Vorlieben": "Unabhängig", "Instanzen": 200, "neidfrei: Mittel": "100,0 %", "neidfrei: schlechtester Fall": "98,9 %", "proportional: Mittel": "100,0 %", "ohne Verlust": "174 von 200"}
    assert t[7]["neidfrei: Mittel"] == "98,1 %" and t[7]["neidfrei: schlechtester Fall"] == "90,8 %" and t[7]["ohne Verlust"] == "0 von 200"


# --- Reihe 2: Protokolle ------------------------------------------------------------------------------------------------------------------------

def test_envy_freeness_proportionality_and_efficiency_counts(protocols):
    for r in protocols:
        assert r["prop"] == r["runs"], r                                                    # alle Protokolle sind proportional
        if r["protocol"] in ("geteilt", "selfridge") or r["n"] == 2:
            assert r["ef"] == r["runs"], r
        else:
            assert r["ef"] == 0, r                                                          # das Messer ab drei Teams ist in keiner Instanz neidfrei
    assert sum(r["pareto"] for r in protocols) == 26 and sum(r["runs"] for r in protocols) == 3600
    assert {(r["protocol"], r["n"], r["model"]): r["pareto"] for r in protocols if r["pareto"]} == {
        ("geteilt", 2, "aehnlich"): 3, ("messer", 2, "aehnlich"): 1, ("selfridge", 3, "aehnlich"): 1, ("geteilt", 2, "gegen"): 14, ("messer", 2, "gegen"): 7}


def test_welfare_of_the_protocols_and_after_improvement(protocols):
    expected = {  # (Protokoll, Teams, Vorlieben): (Summe der Nutzen, nachgebessert) im Verhältnis zur Höchstwohlfahrt
        ("geteilt", 2, "unabh"): (0.80901, 0.99707), ("messer", 2, "unabh"): (0.80825, 0.99702), ("selfridge", 3, "unabh"): (0.78325, 0.99524),
        ("messer", 3, "unabh"): (0.75852, 0.99242), ("messer", 4, "unabh"): (0.73763, 0.98477), ("messer", 5, "unabh"): (0.73236, 0.96823),
        ("geteilt", 2, "gegen"): (0.80738, 0.90945), ("selfridge", 3, "gegen"): (0.65669, 0.94142), ("messer", 4, "gegen"): (0.53037, 0.92698), ("messer", 5, "gegen"): (0.44622, 0.9577),
    }
    for (protocol, n, model), (ratio, fixed) in expected.items():
        r = row(protocols, protocol=protocol, n=n, model=model)
        assert r["ratio_sum"] == pytest.approx(ratio, abs=6e-6) and r["fixed_sum"] == pytest.approx(fixed, abs=6e-6), (protocol, n, model)


def test_gap_between_protocol_and_improvement_and_the_ranges_named_in_the_readme(protocols):
    gaps = [100 * (r["fixed_sum"] - r["ratio_sum"]) for r in protocols]
    assert 7.5 < min(gaps) < 8.5 and 50.5 < max(gaps) < 51.5                                # „8 bis 51 Prozentpunkte“
    fixed_other = [r["fixed_sum"] for r in protocols if r["model"] != "gegen"]
    fixed_gegen = [r["fixed_sum"] for r in protocols if r["model"] == "gegen"]
    assert (ev.pct(min(fixed_other), 0), ev.pct(max(fixed_other), 0)) == ("97 %", "100 %")
    assert (ev.pct(min(fixed_gegen)), ev.pct(max(fixed_gegen))) == ("90,9 %", "95,8 %")
    def aggregate(p, n):
        return sum(r["ratio_sum"] for r in protocols if r["protocol"] == p and r["n"] == n) / 3

    assert [ev.pct(aggregate(p, n)) for p, n in (("geteilt", 2), ("selfridge", 3), ("messer", 5))] == ["84,3 %", "77,7 %", "68,2 %"]


def test_improvement_never_lowers_the_welfare(protocols):
    assert all(r["fixed_sum"] >= r["ratio_sum"] - 1e-9 for r in protocols)


def test_protocol_verdict(protocols):
    kind, text = ev.verdict_protocols(protocols)
    assert text == ("Geteilt und gewählt und Selfridge–Conway sind in allen Instanzen neidfrei und proportional, das Messer ab drei Teams in 0 von 1800 Instanzen neidfrei (proportional immer). "
                    "Pareto-effizient ist über alle Zeilen nur 0,7 %; die Summe der Nutzen liegt bei 84,3 % (Geteilt und gewählt, 2 Teams), 77,7 % (Selfridge–Conway) und 68,2 % (Messer, 5 Teams) der Höchstwohlfahrt.")


def test_protocol_table_strings(protocols):
    t = ev.protocol_table(protocols)
    assert t[0] == {"Protokoll": "Geteilt und gewählt", "Teams": 2, "Vorlieben": "Unabhängig", "neidfrei": "200 von 200", "proportional": "200 von 200", "Pareto-effizient": "0 von 200",
                    "Summe der Nutzen": "80,9 %", "nachgebessert": "99,7 %"}
    assert t[17]["Summe der Nutzen"] == "44,6 %" and t[17]["nachgebessert"] == "95,8 %" and t[17]["Teams"] == 5


# --- Reihe 3: Zersplitterung --------------------------------------------------------------------------------------------------------------------

def test_blocks_per_team(blocks):
    got = {r["n"]: (r["messer"], r["wohlfahrt"], r["neidfrei"]) for r in blocks}
    assert got[2] == pytest.approx((1.0, 3.35, 3.3925)) and got[3] == pytest.approx((1.0, 2.89333, 3.16), abs=1e-5)
    assert got[4] == pytest.approx((1.0, 2.4075, 2.8375)) and got[5] == pytest.approx((1.0, 2.002, 2.559))


def test_blocks_verdict_and_table(blocks):
    assert ev.verdict_blocks(blocks)[1] == "Bei 5 Teams bekommt ein Team beim Messer im Mittel 1,0 Block, bei höchster Wohlfahrt 2,0, bei der besten neidfreien Verteilung 2,6 Blöcke: wer Effizienz will, zerlegt die Hallenzeit (bei den LP-Verteilungen hängt die Zahl von der gewählten Lösung ab)."
    assert ev.block_table(blocks)[1] == {"Teams": 3, "Bewegliches Messer": "1,00", "Höchste Wohlfahrt": "2,89", "Neidfrei, beste Wohlfahrt": "3,16"}


def test_series_are_deterministic(price, protocols, blocks):
    assert ev.series_blocks() == blocks
