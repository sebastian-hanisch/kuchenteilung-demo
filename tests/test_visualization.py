"""Abbildungen: Aufbau, gesperrte Achsen, Werte an der Hand-Analyse."""

import pytest

import kuc_constants as C
import kuc_evaluation as ev
import kuc_visualization as V


def locked(fig):
    return all(ax.fixedrange for ax in fig.select_xaxes()) and all(ax.fixedrange for ax in fig.select_yaxes())


def analyse(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


def test_values_figure_has_one_step_line_per_team():
    a = analyse("Selfridge–Conway mit Kürzung")
    fig = V.build_values(a)
    assert [t.name for t in fig.data] == ["Team 1", "Team 2", "Team 3"] and all(t.line.shape == "hv" for t in fig.data)
    assert list(fig.data[0].y) == pytest.approx([1 / 12] * 13)                                      # Team 1 bewertet alle Stunden gleich: 1/12
    assert list(fig.data[1].y)[:5] == pytest.approx([3 / 24] * 4 + [1 / 24]) and len(fig.data[1].x) == C.CELLS + 1
    assert list(fig.layout.xaxis.ticktext)[:3] == ["08:00", "10:00", "12:00"] and locked(fig)


def test_division_figure_draws_one_stripe_per_interval_with_a_legend_entry_per_team():
    a = analyse("Selfridge–Conway mit Kürzung")
    fig = V.build_division(a)
    bars = list(fig.data)
    assert [b.name for b in bars if b.showlegend] == ["Team 1", "Team 2", "Team 3"]
    first_row = [b for b in bars if b.y[0] == "Selfridge–Conway"]
    assert sorted((b.name, float(b.base[0]), float(b.x[0])) for b in first_row) == sorted([
        ("Team 1", 28 / 9, 4 / 9), ("Team 1", 8.0, 4.0), ("Team 2", 0.0, 28 / 9), ("Team 3", 32 / 9, 40 / 9)])
    assert {b.y[0] for b in bars} == {"Selfridge–Conway", "Höchste Wohlfahrt", "Neidfrei, beste Wohlfahrt", "Nachgebessert"}
    assert fig.layout.barmode == "overlay" and fig.layout.yaxis.autorange == "reversed" and locked(fig)


def test_utilities_figure_has_four_groups_and_the_fair_share_line():
    a = analyse("Selfridge–Conway mit Kürzung")
    fig = V.build_utilities(a)
    assert [t.name for t in fig.data] == ["Selfridge–Conway", "Höchste Wohlfahrt", "Neidfrei, beste Wohlfahrt", "Nachgebessert"]
    assert list(fig.data[0].y) == pytest.approx([10 / 27, 7 / 18, 19 / 45]) and list(fig.data[0].x) == ["Team 1", "Team 2", "Team 3"]
    assert [s.y0 for s in fig.layout.shapes] == [pytest.approx(1 / 3)] and locked(fig)


def test_price_series_figure():
    rows = [{"n": n, "model": m, "runs": 10, "ef_mean": 0.99, "ef_min": 0.9, "prop_mean": 1.0, "prop_min": 1.0, "ef_free": 0} for m in C.MODELS for n in C.SERIES_NS]
    fig = V.build_price_series(rows)
    bars = [t for t in fig.data if t.type == "bar"]
    marks = [t for t in fig.data if t.type == "scatter"]
    assert len(bars) == 3 and len(marks) == 3 and list(bars[0].x) == ["2 Teams", "3 Teams", "4 Teams", "5 Teams"]
    assert list(bars[0].y) == pytest.approx([0.01] * 4) and list(marks[0].y) == pytest.approx([0.1] * 4) and locked(fig)


def test_protocol_series_figure():
    rows = [{"protocol": p, "n": n, "model": m, "runs": 10, "ef": 0, "prop": 10, "pareto": 0, "ratio_sum": 0.8, "fixed_sum": 0.95} for m in C.MODELS for p, n in C.SERIES_PROTOCOL_CASES]
    fig = V.build_protocol_series(rows)
    bars = [t for t in fig.data if t.type == "bar"]
    assert len(bars) == 3 and list(bars[0].x) == ["Geteilt und gewählt, 2", "Bewegliches Messer, 2", "Selfridge–Conway, 3", "Bewegliches Messer, 3", "Bewegliches Messer, 4", "Bewegliches Messer, 5"]
    assert list(bars[0].y) == [0.8] * 6 and [t.y[0] for t in fig.data if t.type == "scatter"] == [0.95] * 3 and tuple(fig.layout.yaxis.range) == (0, 1.05) and locked(fig)


def test_block_series_figure():
    rows = [{"n": n, "runs": 10, "messer": 1.0, "wohlfahrt": 2.0 + n / 10, "neidfrei": 3.0} for n in C.SERIES_NS]
    fig = V.build_block_series(rows)
    assert [t.name for t in fig.data] == ["Bewegliches Messer", "Höchste Wohlfahrt", "Neidfrei, beste Wohlfahrt"]
    assert list(fig.data[1].y) == pytest.approx([2.2, 2.3, 2.4, 2.5]) and locked(fig)
