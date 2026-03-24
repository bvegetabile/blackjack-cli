from blackjack.gameutils.card import Card


def test_number_card_repr():
    card = Card(suit="H", rank=7)
    assert str(card) == "7\u2665"


def test_ace_repr():
    card = Card(suit="S", rank=1)
    assert str(card) == "A\u2660"


def test_face_card_repr():
    card = Card(suit="D", rank=13)
    assert str(card) == "K\u25C6"


def test_jack_repr():
    card = Card(suit="C", rank=11)
    assert str(card) == "J\u2663"


def test_queen_repr():
    card = Card(suit="H", rank=12)
    assert str(card) == "Q\u2665"


def test_all_suits():
    expected = {
        "D": "\u25C6",
        "C": "\u2663",
        "H": "\u2665",
        "S": "\u2660",
    }
    for suit, symbol in expected.items():
        card = Card(suit=suit, rank=5)
        assert str(card) == f"5{symbol}"
