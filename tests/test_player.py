from blackjack.gameutils.card import Card
from blackjack.gameutils.player import Player


def _make_player(*cards):
    """Helper: create a player with the given cards."""
    p = Player(player_id=1, player_type="normal")
    for card in cards:
        p.add_card_to_hand(card)
    return p


# --- Scoring tests ---

def test_simple_hand():
    p = _make_player(Card("H", 10), Card("S", 7))
    assert p.score_hand() == 17


def test_blackjack():
    p = _make_player(Card("H", 1), Card("S", 13))
    assert p.score_hand() == 21


def test_ace_as_eleven():
    p = _make_player(Card("H", 1), Card("S", 5))
    assert p.score_hand() == 16


def test_ace_downgrades_to_one():
    # A + 5 + K = 11 + 5 + 10 = 26 -> ace becomes 1 -> 16
    p = _make_player(Card("H", 1), Card("S", 5), Card("D", 13))
    assert p.score_hand() == 16


def test_two_aces():
    # A + A = 11 + 11 = 22 -> one ace becomes 1 -> 12
    p = _make_player(Card("H", 1), Card("S", 1))
    assert p.score_hand() == 12


def test_four_aces_and_seven():
    # 4*A + 7 = 44 + 7 = 51 -> subtract 10 three times -> 21
    p = _make_player(
        Card("H", 1), Card("S", 1), Card("D", 1), Card("C", 1), Card("H", 7)
    )
    assert p.score_hand() == 21


def test_bust():
    p = _make_player(Card("H", 10), Card("S", 7), Card("D", 8))
    assert p.score_hand() == 25


def test_face_cards_worth_ten():
    # J + Q = 10 + 10 = 20
    p = _make_player(Card("H", 11), Card("S", 12))
    assert p.score_hand() == 20


# --- Other Player methods ---

def test_add_card_updates_score():
    p = Player(player_id=1, player_type="normal")
    p.add_card_to_hand(Card("H", 10))
    assert p.score is None  # score not set until 2 cards
    p.add_card_to_hand(Card("S", 7))
    assert p.score == 17


def test_get_hand_as_str_visible():
    p = _make_player(Card("H", 1), Card("S", 13))
    result = p.get_hand_as_str(hide_first_card=False)
    assert "A\u2665" in result
    assert "K\u2660" in result
    assert "Score" in result


def test_get_hand_as_str_hidden():
    p = _make_player(Card("H", 1), Card("S", 13))
    result = p.get_hand_as_str(hide_first_card=True)
    assert "??" in result
    assert "Score" not in result


def test_default_cash():
    p = Player(player_id=1, player_type="normal")
    assert p.cash == 0


def test_update_cash():
    p = Player(player_id=1, player_type="normal", starting_cash=100)
    p.update_cash(50)
    assert p.cash == 150
    p.update_cash(-30)
    assert p.cash == 120


# --- Multi-hand tests ---

def test_player_multiple_hands():
    from blackjack.gameutils.hand import Hand
    p = Player(player_id=1, player_type="normal")
    p.hands = [
        Hand(cards=[Card("H", 8), Card("S", 3)]),
        Hand(cards=[Card("D", 8), Card("C", 6)]),
    ]
    assert p.score_hand(hand_index=0) == 11
    assert p.score_hand(hand_index=1) == 14


def test_hand_property_backward_compat():
    p = _make_player(Card("H", 10), Card("S", 7))
    assert p.hand == [Card("H", 10), Card("S", 7)]
    assert len(p.hand) == 2


def test_reset_hands():
    p = _make_player(Card("H", 10), Card("S", 7))
    p.reset_hands()
    assert len(p.hands) == 1
    assert len(p.hand) == 0
    assert p.score is None
