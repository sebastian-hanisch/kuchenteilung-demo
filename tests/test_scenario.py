"""Szenario: Erzeuger der Bewertungen und die Texteingabe."""

import pytest

import kuc_constants as C
import kuc_scenario as S


@pytest.mark.parametrize("model", list(C.MODELS))
def test_weights_are_deterministic_nonnegative_integers_with_positive_sums(model):
    a = S.make_weights(model, 4, 7)
    assert a == S.make_weights(model, 4, 7) and a != S.make_weights(model, 4, 8)
    assert len(a) == 4 and all(len(row) == C.CELLS for row in a)
    for row in a:
        assert all(isinstance(w, int) and 0 <= w <= C.WEIGHT_MAX for w in row) and sum(row) > 0


@pytest.mark.parametrize("model", list(C.MODELS))
def test_every_row_has_a_positive_sum_even_for_many_seeds(model):
    for seed in range(200):
        assert all(sum(row) > 0 for row in S.make_weights(model, 3, seed))


def test_weights_for_the_default_seed_are_fixed():
    assert S.make_weights("unabh", 3, 4) == [[8, 4, 1, 7, 9, 9, 9, 3, 7, 9, 5, 9], [5, 1, 4, 6, 3, 7, 4, 9, 2, 6, 0, 1], [5, 4, 4, 4, 8, 5, 3, 9, 8, 3, 2, 2]]
    assert S.make_weights("gegen", 5, 29)[0] == [8, 8, 8, 2, 2, 1, 1, 0, 0, 2, 2, 1]                  # Team 1 mag die Stunden 1 bis 3


def test_gegen_gives_each_team_its_own_block_of_hours():
    for seed in range(20):
        rows = S.make_weights("gegen", 3, seed)
        for i, row in enumerate(rows):
            assert row[4 * i: 4 * i + 4] == [8, 8, 8, 8]                                 # Block i: Stunden 4 i bis 4 i + 3
            assert all(w <= 2 for j, w in enumerate(row) if not 4 * i <= j < 4 * i + 4)


def test_aehnlich_teams_share_a_common_shape():
    rows = S.make_weights("aehnlich", 2, 5)
    diffs = [abs(a - b) for a, b in zip(rows[0], rows[1])]
    assert max(diffs) <= 4 and sum(diffs) < sum(rows[0])                                # grob dieselbe Verteilung (Rauschen höchstens ±2 je Team)


def test_unknown_model_raises():
    with pytest.raises(ValueError):
        S.make_weights("nichts", 3, 4)


def test_parse_weights_accepts_commas_semicolons_spaces_and_lines():
    two = "1 2 3 4 5 6 7 8 9 0 1 2\n9,8,7,6,5,4,3,2,1,0,9,8"
    rows, err = S.parse_weights(two)
    assert err is None and rows == [[1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2], [9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 9, 8]]
    assert S.parse_weights("1;1;1;1;1;1;1;1;1;1;1;1\r\n\r\n2 2 2 2 2 2 2 2 2 2 2 2")[0] == [[1] * 12, [2] * 12]


def test_parse_weights_empty_is_no_input_and_no_error():
    assert S.parse_weights("") == (None, None) and S.parse_weights("  \n ") == (None, None) and S.parse_weights(None) == (None, None)


ONE = " ".join(["1"] * 12)


@pytest.mark.parametrize("text,fragment", [
    (ONE, "2 bis 6 Zeilen"),
    ("\n".join([ONE] * 7), "2 bis 6 Zeilen"),
    (ONE + "\n" + ONE.replace("1", "x", 1), "Zeile 2: „x“ ist keine ganze Zahl"),
    (ONE + "\n" + ONE.replace("1", "2.5", 1), "Zeile 2: „2.5“ ist keine ganze Zahl"),
    (ONE + "\n" + ONE.replace("1", "-1", 1), "Zeile 2: „-1“ ist keine ganze Zahl"),
    (ONE + "\n1 1 1", "Zeile 2: Es müssen 12 Zahlen sein, eine je Stunde (eingegeben: 3)"),
    (ONE + "\n" + ONE + " 1", "Zeile 2: Es müssen 12 Zahlen sein, eine je Stunde (eingegeben: 13)"),
    (ONE + "\n" + ONE.replace("1", "10", 1), "Zeile 2: Jede Zahl muss zwischen 0 und 9 liegen"),
    (ONE + "\n" + " ".join(["0"] * 12), "Zeile 2: Mindestens eine Stunde braucht ein Gewicht über 0"),
])
def test_parse_weights_rejects_bad_input_with_a_message(text, fragment):
    rows, err = S.parse_weights(text)
    assert rows is None and fragment in err


def test_parse_weights_accepts_the_bounds():
    assert S.parse_weights("\n".join([ONE] * 2))[0] is not None and S.parse_weights("\n".join([ONE] * 6))[0] is not None
    assert S.parse_weights(" ".join(["9"] * 12) + "\n" + " ".join(["0"] * 11 + ["1"]))[1] is None
