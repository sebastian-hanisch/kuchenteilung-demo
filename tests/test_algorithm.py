"""Kern von Hand gerechnet: Bewertung, Schnittpunkte, die drei Protokolle (jede Entscheidung des Ablaufs), Eigenschaften, lineare Programme."""

from fractions import Fraction as F

import pytest
from conftest import vals_of

import kuc_algorithm as A

TWELVE = [1] * 12


# --- Bewertung und Schnittpunkte ----------------------------------------------------------------------------------------------------------------

def test_valuation_normalises_to_one():
    v = A.valuation([1, 3])
    assert v == (F(1, 4), F(3, 4)) and sum(v) == 1


@pytest.mark.parametrize("bad", [[], [0, 0], [1, -1], [3, -1], [1, 1.5]])
def test_valuation_rejects_bad_weights(bad):
    with pytest.raises(ValueError):
        A.valuation(bad)


def test_value_of_intervals_inside_and_across_cells():
    v = A.valuation([1, 3])                                   # Dichten 1/4 und 3/4
    assert A.value(v, F(0), F(1)) == F(1, 4) and A.value(v, F(1), F(2)) == F(3, 4)
    assert A.value(v, F(1, 2), F(3, 2)) == F(1, 8) + F(3, 8)  # halbe erste und halbe zweite Zelle
    assert A.value(v, F(1, 2), F(1, 2)) == 0 and A.value(v, F(0), F(2)) == 1
    assert A.piece_value(v, [(F(0), F(1)), (F(1), F(2))]) == 1 and A.piece_value(v, []) == 0


def test_quantile_by_hand():
    v = A.valuation([1, 3])
    assert A.quantile(v, F(0), F(1, 4)) == 1                  # genau das Ende der ersten Zelle
    assert A.quantile(v, F(0), F(1, 2)) == F(1) + F(1, 3)     # 1/4 aus Zelle 1, dann 1/4 mit Dichte 3/4: 1/3 Zelle
    assert A.quantile(v, F(1, 2), F(1, 8)) == 1               # von der halben Zelle 1 aus noch 1/8
    assert A.quantile(v, F(0), 0) == 0 and A.quantile(v, F(1), F(1, 4)) == F(4, 3)
    assert A.quantile(v, F(0), F(11, 10)) is None             # mehr als der ganze Kuchen
    assert A.quantile(v, F(0), F(1, 2), end=F(1)) is None      # bis zur Grenze nicht erreichbar


def test_quantile_with_an_end_beyond_the_cake_does_not_run_off_the_end():
    v = A.valuation([1, 3])
    assert A.quantile(v, F(0), F(11, 10), end=F(100)) is None and A.quantile(v, F(0), F(1, 2), end=F(100)) == F(4, 3)
    assert A.quantile(v, F(2), F(1, 100)) is None                                          # ab dem Ende des Kuchens ist nichts mehr zu holen


def test_quantile_skips_zero_density_and_picks_the_leftmost_point():
    v = A.valuation([1, 0, 0, 1])
    assert A.quantile(v, F(0), F(1, 2)) == 1                  # Zellen 2 und 3 sind wertlos: der kleinste Punkt ist das Ende von Zelle 1
    assert A.quantile(v, F(1), F(1, 4)) == F(3) + F(1, 2)


def test_normalize_merges_touching_and_drops_empty():
    assert A.normalize([(F(2), F(3)), (F(0), F(1)), (F(1), F(2)), (F(5), F(5))]) == [(0, 3)]
    assert A.normalize([(F(4), F(5)), (F(0), F(1))]) == [(0, 1), (4, 5)]
    assert A.fragments([(F(0), F(1)), (F(1), F(2)), (F(3), F(4))]) == 2 and A.fragments([]) == 0


def test_covers_cake():
    assert A.covers_cake([[(F(0), F(5))], [(F(5), F(12))]], 12)
    assert not A.covers_cake([[(F(0), F(5))], [(F(6), F(12))]], 12)      # Lücke
    assert not A.covers_cake([[(F(0), F(6))], [(F(5), F(12))]], 12)      # Überschneidung
    assert not A.covers_cake([[(F(0), F(5))]], 12)


# --- Geteilt und gewählt ---------------------------------------------------------------------------------------------------------------------------

def test_cut_and_choose_hand_example(mini):
    trace = []
    pieces = A.cut_and_choose(mini, trace)
    assert pieces == [[(8, 12)], [(0, 8)]]
    assert trace == [("schnitt", 0, 8), ("wahl", 1, "links")]
    assert A.utilities(mini, pieces) == [F(1, 2), F(9, 11)]


def test_cut_and_choose_welfare_and_efficiency_of_the_hand_example(mini):
    pieces = A.cut_and_choose(mini)
    # höchste Wohlfahrt: Stunden 1 bis 6 an Team 2 (3/22 > 1/24), Stunden 7 bis 12 an Team 1 (1/8 > 0 bzw. 1/22): 6 · 3/22 + 6 · 1/8 = 9/11 + 3/4 = 69/44
    assert A.welfare_bound(mini) == F(69, 44)
    assert A.is_envy_free(mini, pieces) and A.is_proportional(mini, pieces)
    w, x, improvable = A.pareto_improvement(mini, pieces)
    assert improvable and w == pytest.approx(69 / 44)                         # Team 1 bekommt Stunden 7 und 8 dazu, Team 2 verliert nichts (Gewicht 0)
    assert not A.is_pareto_efficient(mini, pieces)


def test_cut_and_choose_tie_goes_to_the_left_for_person_two():
    uniform = vals_of(TWELVE, TWELVE)
    assert A.cut_and_choose(uniform) == [[(6, 12)], [(0, 6)]]


def test_cut_and_choose_picks_the_right_side_when_it_is_worth_more():
    vals = vals_of(TWELVE, [1] * 6 + [3] * 6)                                  # Team 2 will die zweite Hälfte (3/4)
    assert A.cut_and_choose(vals) == [[(0, 6)], [(6, 12)]]


def test_cut_and_choose_rejects_other_group_sizes():
    with pytest.raises(ValueError):
        A.cut_and_choose(vals_of(TWELVE, TWELVE, TWELVE))


# --- Selfridge–Conway ---------------------------------------------------------------------------------------------------------------------------

SC_ROWS = ([1] * 12, [3, 3, 3, 3, 1, 1, 1, 1, 2, 2, 2, 2], [1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2])


def test_selfridge_conway_hand_example_with_trimming():
    """A (uniform) schneidet bei 4 und 8. B (Summe 24) bewertet die Stücke mit 12/24, 4/24, 8/24, kürzt das erste auf den Wert des zweitbesten (8/24): 3/24 je Stunde, also bis 8/3.
    C (Summe 20) bewertet X1' mit (8/3)/20, X2 und X3 mit je 8/20 und nimmt X2 (Gleichstand: das kleinere). B bekommt X1'. A bekommt X3. B hat das gekürzte Stück, C teilt die Kürzung [8/3, 4]
    (Länge 4/3, Dichte 1/20 gleichmäßig) in drei Teile der Länge 4/9. Es wählen B, A, C: alle Teile sind B und A gleich viel wert (gleichmäßig), also jeweils der erste verbleibende Teil."""
    vals = vals_of(*SC_ROWS)
    trace = []
    pieces = A.selfridge_conway(vals, trace)
    assert pieces == [[(F(28, 9), F(32, 9)), (8, 12)], [(0, F(28, 9))], [(F(32, 9), 8)]]
    assert A.covers_cake(pieces, 12)
    assert A.utilities(vals, pieces) == [F(10, 27), F(7, 18), F(19, 45)]
    assert trace == [("schnitt", 0, 4), ("schnitt", 0, 8), ("kuerzen", 1, F(8, 3), 0), ("wahl", 2, 1), ("wahl", 1, 0), ("wahl", 0, 2), ("teilen", 2, 1)]


def test_selfridge_conway_hand_example_is_envy_free_with_the_expected_ties():
    vals = vals_of(*SC_ROWS)
    pieces = A.selfridge_conway(vals)
    mat = A.envy_matrix(vals, pieces)
    assert A.is_envy_free(vals, pieces) and A.is_proportional(vals, pieces)
    assert mat[0] == [F(10, 27), F(7, 27), F(10, 27)]          # Team 1 ist zwischen eigenem und Team 3 gleichgültig
    assert mat[1] == [F(7, 18), F(7, 18), F(2, 9)]             # Team 2: eigenes und das von Team 1 gleich viel
    assert mat[2] == [F(19, 45), F(7, 45), F(19, 45)]          # Team 3: eigenes und das von Team 1 gleich viel


def test_selfridge_conway_without_trimming_when_the_top_value_is_tied():
    vals = vals_of(TWELVE, TWELVE, TWELVE)
    trace = []
    pieces = A.selfridge_conway(vals, trace)
    # B bewertet alle drei Stücke gleich: kein Kürzen. C nimmt das erste (Gleichstand: kleinste Nummer), B wählt unter den übrigen das kleinere, A bekommt den Rest.
    assert pieces == [[(8, 12)], [(4, 8)], [(0, 4)]]
    assert ("kuerzen", 1, None, 0) in trace and not any(e[0] == "teilen" for e in trace)


def test_selfridge_conway_when_c_takes_the_trimmed_piece():
    # C bewertet das erste Stück am höchsten: C nimmt das gekürzte Stück, B wählt unter den beiden übrigen, A bekommt das letzte; die Kürzung teilt B
    vals = vals_of(TWELVE, [3, 3, 3, 3, 1, 1, 1, 1, 1, 1, 1, 1], [5, 5, 5, 5, 1, 1, 1, 1, 1, 1, 1, 1])
    trace = []
    pieces = A.selfridge_conway(vals, trace)
    assert A.covers_cake(pieces, 12) and A.is_envy_free(vals, pieces) and A.is_proportional(vals, pieces)
    teilen = next(e for e in trace if e[0] == "teilen")
    assert teilen[1] == 1 and teilen[2] == 2                                     # B teilt, C hält das gekürzte Stück


def test_selfridge_conway_rejects_other_group_sizes():
    with pytest.raises(ValueError):
        A.selfridge_conway(vals_of(TWELVE, TWELVE))


# --- Bewegliches Messer ----------------------------------------------------------------------------------------------------------------------------

def test_moving_knife_hand_example_shows_envy():
    """Team 1 (1 · 6, 3 · 6; Summe 24) will für 1/3 = 8: 6 + 2 · 3 gibt 8 bei Stunde 8; Team 2 und 3 (gleichmäßig) rufen bei 4. Team 2 ruft zuerst (Gleichstand mit Team 3: kleinere Nummer).
    Dann Team 1 von 4 aus: 2 + 3 · 2 = 8 bei Stunde 8; Team 3 von 4 aus: 4 Stunden = 1/3 bei 8; Gleichstand, Team 1 gewinnt. Team 3 bekommt [8, 12]: für Team 1 12/24 = 1/2 > 1/3."""
    vals = vals_of([1] * 6 + [3] * 6, TWELVE, TWELVE)
    trace = []
    pieces = A.moving_knife(vals, trace)
    assert pieces == [[(4, 8)], [(0, 4)], [(8, 12)]]
    assert trace == [("ruf", 1, 4), ("ruf", 0, 8)]
    assert A.utilities(vals, pieces) == [F(1, 3)] * 3
    assert A.envy_pairs(vals, pieces) == [(0, 2)] and A.envy_matrix(vals, pieces)[0][2] == F(1, 2)
    assert A.is_proportional(vals, pieces) and not A.is_envy_free(vals, pieces)


def test_moving_knife_with_two_teams_is_envy_free():
    vals = vals_of([1] * 6 + [3] * 6, TWELVE)
    pieces = A.moving_knife(vals)
    assert A.is_envy_free(vals, pieces) and A.is_proportional(vals, pieces)


def test_moving_knife_for_many_teams_gives_everyone_a_block_in_order():
    vals = vals_of(*[TWELVE] * 4)
    pieces = A.moving_knife(vals)
    assert pieces == [[(0, 3)], [(3, 6)], [(6, 9)], [(9, 12)]]


def test_moving_knife_gives_the_rest_to_the_last_team_even_if_it_values_it_less():
    """Team 1 will die geraden Zellen (Dichte 1/6 je Zelle 0, 2, 4, …), Team 2 die ungeraden. Team 1 ruft nach drei Zellen (am Ende von Zelle 4: x = 5), Team 2 erst bei x = 6; Team 1 bekommt [0, 5],
    Team 2 den Rest [5, 12] mit den Zellen 5, 7, 9, 11 (4/6)."""
    vals = vals_of([1, 0] * 6, [0, 1] * 6)
    pieces = A.moving_knife(vals)
    assert pieces == [[(0, 5)], [(5, 12)]]
    assert A.utilities(vals, pieces) == [F(1, 2), F(2, 3)]


def test_divide_dispatches_and_rejects_unknown_protocols():
    vals = vals_of(TWELVE, TWELVE)
    assert A.divide("geteilt", vals) == A.cut_and_choose(vals) and A.divide("messer", vals) == A.moving_knife(vals)
    assert A.divide("selfridge", vals_of(TWELVE, TWELVE, TWELVE)) == A.selfridge_conway(vals_of(TWELVE, TWELVE, TWELVE))
    with pytest.raises(ValueError):
        A.divide("kuchen", vals)
    with pytest.raises(ValueError):
        A.moving_knife(vals_of(TWELVE))
    with pytest.raises(ValueError):
        A.moving_knife([A.valuation([1, 1]), A.valuation([1, 1, 1])])


# --- Eigenschaften ----------------------------------------------------------------------------------------------------------------------------------

def test_envy_and_proportionality_checks_with_tolerance():
    vals = vals_of([1, 1], [1, 3])
    pieces = [[(F(0), F(1))], [(F(1), F(2))]]
    assert A.envy_pairs(vals, pieces) == []
    unfair = [[(F(0), F(1, 2))], [(F(1, 2), F(2))]]
    assert A.envy_pairs(vals, unfair) == [(0, 1)]
    assert not A.is_proportional(vals, unfair) and A.is_proportional(vals, unfair, tol=F(1, 2))
    assert A.envy_pairs(vals, unfair, tol=F(1, 2)) == []


def test_shares_per_cell():
    x = A.shares([[(F(0), F(3, 2))], [(F(3, 2), F(2))]], 2)
    assert x == [[1, F(1, 2)], [0, F(1, 2)]]


# --- Lineare Programme ------------------------------------------------------------------------------------------------------------------------------

def test_max_welfare_division_gives_each_cell_to_the_highest_density():
    vals = vals_of([3, 1, 0], [1, 2, 0], [0, 1, 5])
    pieces = A.max_welfare_division(vals)
    assert pieces == [[(0, 1)], [(1, 2)], [(2, 3)]]
    assert A.welfare_bound(vals) == F(3, 4) + F(2, 3) + F(5, 6)
    assert A.max_welfare_division(vals_of([1, 1], [1, 1])) == [[(0, 2)], []]               # Gleichstand: kleinere Nummer


def test_price_of_envy_freeness_by_hand():
    """A will nur Zelle 1 (Dichte 1), B bewertet Zelle 1 mit 9/10 und Zelle 2 mit 1/10. Höchste Wohlfahrt 11/10 (Zelle 1 an A, Zelle 2 an B), aber B beneidet A.
    Neidfrei: A bekommt den Anteil x der Zelle 1 (A: x, B: 9/10 (1 − x) + 1/10, B sieht in A's Stück 9x/10): x ≤ 5/9; A sieht in B's Stück 1 − x: x ≥ 1/2. Wohlfahrt 1 + x/10, am besten 19/18."""
    vals = vals_of([1, 0], [9, 1])
    assert A.welfare_bound(vals) == F(11, 10)
    w, x = A.optimize(vals, envy_free=True)
    assert w == pytest.approx(19 / 18, abs=1e-9) and x[0][0] == pytest.approx(5 / 9, abs=1e-7)
    w_plain, _ = A.optimize(vals)
    assert w_plain == pytest.approx(11 / 10, abs=1e-9)
    w_prop, _ = A.optimize(vals, proportional=True)
    assert w_prop == pytest.approx(19 / 18, abs=1e-9)                                       # hier ist die Proportionalität genauso teuer


def test_optimize_with_floors():
    """B soll mindestens 4/5 bekommen: B bewertet Zelle 1 mit 9/10, Zelle 2 mit 1/10; A bekommt den Anteil x der Zelle 1: 9/10 (1 − x) + 1/10 ≥ 4/5 gibt x ≤ 2/9; Wohlfahrt 1 + x/10 = 46/45."""
    vals = vals_of([1, 0], [9, 1])
    w, x = A.optimize(vals, floors=[0.0, 0.8])
    assert w == pytest.approx(46 / 45, abs=1e-9) and x[0][0] == pytest.approx(2 / 9, abs=1e-7)
    assert A.optimize(vals, floors=[0.8, 0.0])[0] == pytest.approx(11 / 10, abs=1e-9)    # die Untergrenze für A kostet nichts: A bekommt Zelle 1 ganz


def test_optimize_infeasible_floors_raise():
    with pytest.raises(ValueError):
        A.optimize(vals_of([1, 0], [1, 0]), floors=[0.9, 0.9])


def test_pieces_from_shares_clips_float_overshoot_at_the_cell_end():
    pieces = A.pieces_from_shares([[1.0000001, 0.0], [1e-6, 1.0]])
    assert pieces == [[(0, 1)], [(1, 2)]]                                                  # der Überschuss von 1e-7 wird abgeschnitten, das Restchen der Zelle 0 für Team 2 verschwindet


def test_pieces_from_shares_builds_blocks_in_team_order():
    pieces = A.pieces_from_shares([[1.0, 0.25], [0.0, 0.75]])
    assert pieces == [[(0, F(5, 4))], [(F(5, 4), 2)]]
    assert A.covers_cake(pieces, 2)
    assert A.pieces_from_shares([[0.0], [1.0]]) == [[], [(0, 1)]]


def test_pareto_efficiency_by_hand():
    vals = vals_of([1, 1], [1, 1])
    assert A.is_pareto_efficient(vals, [[(F(0), F(1))], [(F(1), F(2))]])               # gleiche Bewertungen: jede Verteilung ist effizient
    opposite = vals_of([1, 0], [0, 1])
    assert not A.is_pareto_efficient(opposite, [[(F(1), F(2))], [(F(0), F(1))]])         # jeder hat die Zelle, die er nicht will
    assert A.is_pareto_efficient(opposite, [[(F(0), F(1))], [(F(1), F(2))]])


def test_float_utilities_match_exact_ones():
    vals = vals_of([1, 3], [2, 1])
    pieces = [[(F(0), F(1, 2))], [(F(1, 2), F(2))]]
    assert A.float_utilities(vals, pieces) == [float(u) for u in A.utilities(vals, pieces)]
