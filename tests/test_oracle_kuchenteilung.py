"""Orakel (DEMO-PLAYBOOK §12): unabhängige Gegenrechnungen.

- Lineare Programme: **exakte Eckenaufzählung** mit Brüchen (kleine Instanzen); das Optimum eines beschränkten LP liegt an einer Ecke.
- Schnittpunkte: Halbierungssuche mit Brüchen statt der Formel.
- Eigenschaften der Protokolle über viele Zufallsinstanzen mit vielen Gleichständen und Nullgewichten (Neidfreiheit und Proportionalität durch Neuberechnung aus den Zellanteilen).
- Ketten: Neidfreiheit ⇒ Proportionalität ⇒ Wohlfahrt unter der Höchstwohlfahrt."""

import itertools
import random
from fractions import Fraction as F

import pytest

import kuc_algorithm as A


def random_weights(rng, n, m, top=4, zero_share=0.3):
    rows = []
    for _ in range(n):
        w = [0 if rng.random() < zero_share else rng.randint(1, top) for _ in range(m)]
        if sum(w) == 0:
            w[rng.randrange(m)] = 1
        rows.append(w)
    return rows


def vals_of(rows):
    return [A.valuation(w) for w in rows]


# --- Exakte Eckenaufzählung -------------------------------------------------------------------------------------------------------------------

def solve(matrix, rhs):
    """Gaußsches Verfahren mit Brüchen; None, wenn die Matrix nicht eindeutig lösbar ist."""
    size = len(matrix)
    aug = [list(map(F, row)) + [F(b)] for row, b in zip(matrix, rhs)]
    for col in range(size):
        pivot = next((r for r in range(col, size) if aug[r][col] != 0), None)
        if pivot is None:
            return None
        aug[col], aug[pivot] = aug[pivot], aug[col]
        inv = 1 / aug[col][col]
        aug[col] = [x * inv for x in aug[col]]
        for r in range(size):
            if r != col and aug[r][col] != 0:
                f = aug[r][col]
                aug[r] = [x - f * y for x, y in zip(aug[r], aug[col])]
    return [aug[r][size] for r in range(size)]


def exact_optimum(vals, envy_free=False, proportional=False, floors=None):
    """Größte Summe der Nutzen als exakter Bruch (Eckenaufzählung); None, wenn der zulässige Bereich leer ist."""
    n, m = len(vals), len(vals[0])
    nv = n * m
    eq = [[F(1) if k % m == j else F(0) for k in range(nv)] for j in range(m)]
    ineq = [([F(-1) if k == c else F(0) for k in range(nv)], F(0)) for c in range(nv)]
    if envy_free:
        for i in range(n):
            for k in range(n):
                if i != k:
                    row = [F(0)] * nv
                    for j in range(m):
                        row[k * m + j] += vals[i][j]
                        row[i * m + j] -= vals[i][j]
                    ineq.append((row, F(0)))
    lower = [F(1, n) if proportional else F(0)] * n
    if floors is not None:
        lower = [max(lo, F(f)) for lo, f in zip(lower, floors)]
    for i in range(n):
        if lower[i] > 0:
            row = [F(0)] * nv
            for j in range(m):
                row[i * m + j] = -vals[i][j]
            ineq.append((row, -lower[i]))
    best = None
    for active in itertools.combinations(range(len(ineq)), nv - m):
        sol = solve(eq + [ineq[a][0] for a in active], [F(1)] * m + [ineq[a][1] for a in active])
        if sol is None:
            continue
        if all(sum(c * x for c, x in zip(row, sol)) <= b for row, b in ineq):
            welfare = sum(vals[i][j] * sol[i * m + j] for i in range(n) for j in range(m))
            if best is None or welfare > best:
                best = welfare
    return best


@pytest.mark.parametrize("n,m,runs", [(2, 3, 25), (2, 4, 12), (3, 2, 12)])
def test_linear_programs_match_the_exact_vertex_enumeration(n, m, runs):
    rng = random.Random(100 * n + m)
    for _ in range(runs):
        vals = vals_of(random_weights(rng, n, m))
        assert A.optimize(vals)[0] == pytest.approx(float(exact_optimum(vals)), abs=1e-8)
        assert A.optimize(vals, envy_free=True)[0] == pytest.approx(float(exact_optimum(vals, envy_free=True)), abs=1e-8)
        assert A.optimize(vals, proportional=True)[0] == pytest.approx(float(exact_optimum(vals, proportional=True)), abs=1e-8)


def test_linear_program_with_floors_matches_the_exact_enumeration():
    rng = random.Random(7)
    for _ in range(25):
        vals = vals_of(random_weights(rng, 2, 3))
        pieces = A.cut_and_choose(vals)
        floors = A.utilities(vals, pieces)
        want = exact_optimum(vals, envy_free=True, floors=floors)
        assert want is not None
        assert A.optimize(vals, envy_free=True, floors=[float(f) for f in floors])[0] == pytest.approx(float(want), abs=1e-8)
        assert A.optimize(vals, floors=[float(f) for f in floors])[0] == pytest.approx(float(exact_optimum(vals, floors=floors)), abs=1e-8)


def test_exact_enumeration_reproduces_the_hand_example():
    vals = vals_of([[1, 0], [9, 1]])
    assert exact_optimum(vals, envy_free=True) == F(19, 18) and exact_optimum(vals) == F(11, 10)
    assert exact_optimum(vals, floors=[F(0), F(4, 5)]) == F(46, 45)


def test_exact_enumeration_detects_an_empty_region():
    assert exact_optimum(vals_of([[1, 0], [1, 0]]), floors=[F(9, 10), F(9, 10)]) is None


# --- Schnittpunkte durch Halbierung -------------------------------------------------------------------------------------------------------------

def bisect_quantile(v, start, target, steps=70):
    lo, hi = F(start), F(len(v))
    if A.value(v, lo, hi) < target:
        return None
    for _ in range(steps):
        mid = (lo + hi) / 2
        if A.value(v, F(start), mid) >= target:
            hi = mid
        else:
            lo = mid
    return hi


def test_quantile_matches_bisection_and_is_exact_and_minimal():
    rng = random.Random(3)
    for _ in range(150):
        v = A.valuation(random_weights(rng, 1, 12)[0])
        start = F(rng.randint(0, 11), rng.choice([1, 2, 3]))
        reachable = A.value(v, start, F(12))
        if reachable == 0:
            continue
        target = reachable * F(rng.randint(1, 9), 10)
        x = A.quantile(v, start, target)
        assert A.value(v, start, x) == target                                              # exakt
        assert abs(float(x) - float(bisect_quantile(v, start, target))) < 1e-15            # gleich der Halbierung
        assert A.value(v, start, x - F(1, 10 ** 6)) < target                              # der kleinste Punkt


# --- Eigenschaften der Protokolle ---------------------------------------------------------------------------------------------------------------

def check_valid(vals, pieces):
    m = len(vals[0])
    assert A.covers_cake(pieces, m)
    x = A.shares(pieces, m)
    for j in range(m):
        assert sum(x[i][j] for i in range(len(vals))) == 1                                # jede Stunde ist genau einmal vergeben
    for i in range(len(vals)):                                                             # Nutzen über die Zellanteile gleich dem über die Intervalle
        assert sum(vals[i][j] * x[i][j] for j in range(m)) == A.piece_value(vals[i], pieces[i])


@pytest.mark.parametrize("zero_share", [0.0, 0.4, 0.8])
def test_cut_and_choose_is_valid_envy_free_and_proportional(zero_share):
    rng = random.Random(11)
    for _ in range(200):
        vals = vals_of(random_weights(rng, 2, 12, top=3, zero_share=zero_share))
        pieces = A.cut_and_choose(vals)
        check_valid(vals, pieces)
        assert A.is_envy_free(vals, pieces) and A.is_proportional(vals, pieces)


@pytest.mark.parametrize("zero_share", [0.0, 0.4, 0.8])
def test_selfridge_conway_is_valid_envy_free_and_proportional(zero_share):
    rng = random.Random(13)
    for _ in range(300):
        vals = vals_of(random_weights(rng, 3, 12, top=3, zero_share=zero_share))
        pieces = A.selfridge_conway(vals)
        check_valid(vals, pieces)
        assert A.is_envy_free(vals, pieces) and A.is_proportional(vals, pieces)


def test_selfridge_conway_with_heavy_ties():
    rng = random.Random(17)
    for _ in range(300):
        vals = vals_of(random_weights(rng, 3, 12, top=1, zero_share=rng.choice([0.0, 0.2])))      # nur Gewichte 0 und 1: Gleichstände überall
        pieces = A.selfridge_conway(vals)
        check_valid(vals, pieces)
        assert A.is_envy_free(vals, pieces)


@pytest.mark.parametrize("n", [2, 3, 4, 5, 6])
def test_moving_knife_is_valid_proportional_and_gives_contiguous_blocks(n):
    rng = random.Random(19 + n)
    for _ in range(200):
        vals = vals_of(random_weights(rng, n, 12, top=4, zero_share=rng.choice([0.0, 0.3, 0.6])))
        pieces = A.moving_knife(vals)
        check_valid(vals, pieces)
        assert A.is_proportional(vals, pieces) and all(len(p) == 1 for p in pieces)


def test_moving_knife_with_two_teams_is_envy_free():
    rng = random.Random(23)
    for _ in range(200):
        vals = vals_of(random_weights(rng, 2, 12))
        assert A.is_envy_free(vals, A.moving_knife(vals))


def test_moving_knife_is_not_envy_free_with_three_generic_teams():
    rng = random.Random(29)
    envy = sum(not A.is_envy_free(v, A.moving_knife(v)) for v in (vals_of(random_weights(rng, 3, 12, top=9, zero_share=0.0)) for _ in range(100)))
    assert envy >= 95                                                                       # der erste Rufer sieht beide übrigen Stücke zusammen mit 2/3: fast immer ist eines mehr als 1/3 wert


def test_the_first_caller_of_the_knife_values_the_rest_at_exactly_two_thirds():
    rng = random.Random(31)
    for _ in range(100):
        vals = vals_of(random_weights(rng, 3, 12))
        pieces = A.moving_knife(vals)
        first = min(range(3), key=lambda i: pieces[i][0][0])                                 # das Stück ganz links gehört dem ersten Rufer
        mat = A.envy_matrix(vals, pieces)
        assert mat[first][first] == F(1, 3) and sum(mat[first][k] for k in range(3) if k != first) == F(2, 3)


# --- Ketten und LP-Ergebnisse ----------------------------------------------------------------------------------------------------------------------

def test_envy_freeness_implies_proportionality_and_the_welfare_chain():
    rng = random.Random(37)
    for _ in range(60):
        n = rng.choice([2, 3, 4])
        vals = vals_of(random_weights(rng, n, 12, top=5, zero_share=0.3))
        bound = float(A.welfare_bound(vals))
        ef, x_ef = A.optimize(vals, envy_free=True)
        prop, _ = A.optimize(vals, proportional=True)
        assert ef <= prop + 1e-8 <= bound + 2e-8
        pieces = A.pieces_from_shares(x_ef)
        assert A.is_envy_free(vals, pieces, tol=A.TOL) and A.is_proportional(vals, pieces, tol=A.TOL)
        assert A.covers_cake(pieces, 12)


def test_envy_free_protocols_never_beat_the_best_envy_free_division():
    rng = random.Random(41)
    for _ in range(60):
        vals2 = vals_of(random_weights(rng, 2, 12))
        vals3 = vals_of(random_weights(rng, 3, 12))
        for vals, proto in ((vals2, "geteilt"), (vals3, "selfridge")):
            w = float(sum(A.utilities(vals, A.divide(proto, vals))))
            assert w <= A.optimize(vals, envy_free=True)[0] + 1e-8


def test_improvement_never_hurts_anyone_and_keeps_envy_freeness_if_asked():
    rng = random.Random(43)
    for _ in range(40):
        vals = vals_of(random_weights(rng, 3, 12, top=6))
        pieces = A.selfridge_conway(vals)
        floors = A.float_utilities(vals, pieces)
        w, x = A.optimize(vals, envy_free=True, floors=floors)
        better = A.pieces_from_shares(x)
        assert w >= sum(floors) - 1e-8
        assert all(u >= f - 1e-7 for u, f in zip(A.float_utilities(vals, better), floors))
        assert A.is_envy_free(vals, better, tol=A.TOL)
        assert A.is_pareto_efficient(vals, better)                                          # nach der Nachbesserung kann niemand mehr gewinnen, ohne dass ein anderer verliert


def test_the_highest_welfare_division_is_pareto_efficient_and_attains_the_bound():
    rng = random.Random(47)
    for _ in range(40):
        n = rng.choice([2, 3, 5])
        vals = vals_of(random_weights(rng, n, 12))
        pieces = A.max_welfare_division(vals)
        assert A.covers_cake(pieces, 12) and sum(A.utilities(vals, pieces)) == A.welfare_bound(vals)
        assert A.is_pareto_efficient(vals, pieces)
        assert A.optimize(vals)[0] == pytest.approx(float(A.welfare_bound(vals)), abs=1e-8)


def test_a_grid_search_never_beats_the_linear_program():
    """Gegenprobe ohne Optimierer: alle Anteile in Zwanzigsteln für zwei Teams und drei Zellen."""
    rng = random.Random(53)
    for _ in range(15):
        vals = vals_of(random_weights(rng, 2, 3))
        grid = [F(k, 20) for k in range(21)]
        best = None
        for a, b, c in itertools.product(grid, repeat=3):
            x = [[a, b, c], [1 - a, 1 - b, 1 - c]]
            u = [sum(vals[i][j] * x[i][j] for j in range(3)) for i in range(2)]
            cross = [sum(vals[i][j] * x[1 - i][j] for j in range(3)) for i in range(2)]
            if all(u[i] >= cross[i] for i in range(2)):
                w = sum(u)
                best = w if best is None or w > best else best
        lp = A.optimize(vals, envy_free=True)[0]
        assert float(best) <= lp + 1e-9 and lp <= float(best) + 0.1
