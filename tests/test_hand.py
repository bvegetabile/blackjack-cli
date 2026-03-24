from blackjack.gameutils.card import Card
from blackjack.gameutils.hand import Hand


def test_score_simple():
    h = Hand(cards=[Card("H", 10), Card("S", 7)])
    assert h.score() == 17


def test_score_blackjack():
    h = Hand(cards=[Card("H", 1), Card("S", 13)])
    assert h.score() == 21


def test_score_ace_downgrades():
    h = Hand(cards=[Card("H", 1), Card("S", 5), Card("D", 13)])
    assert h.score() == 16


def test_score_two_aces():
    h = Hand(cards=[Card("H", 1), Card("S", 1)])
    assert h.score() == 12


def test_is_bust():
    h = Hand(cards=[Card("H", 10), Card("S", 7), Card("D", 8)])
    assert h.is_bust() is True


def test_not_bust():
    h = Hand(cards=[Card("H", 10), Card("S", 7)])
    assert h.is_bust() is False


def test_can_split_matching_ranks():
    h = Hand(cards=[Card("H", 8), Card("S", 8)])
    assert h.can_split() is True


def test_cannot_split_different_ranks():
    h = Hand(cards=[Card("H", 8), Card("S", 9)])
    assert h.can_split() is False


def test_cannot_split_three_cards():
    h = Hand(cards=[Card("H", 8), Card("S", 8), Card("D", 3)])
    assert h.can_split() is False


def test_can_double_two_cards():
    h = Hand(cards=[Card("H", 5), Card("S", 6)])
    assert h.can_double() is True


def test_cannot_double_three_cards():
    h = Hand(cards=[Card("H", 5), Card("S", 6), Card("D", 3)])
    assert h.can_double() is False


def test_add_card():
    h = Hand()
    h.add_card(Card("H", 10))
    assert len(h.cards) == 1
    h.add_card(Card("S", 7))
    assert len(h.cards) == 2
    assert h.score() == 17
