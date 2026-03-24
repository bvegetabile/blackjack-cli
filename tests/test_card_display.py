from blackjack.gameutils.card import Card
from blackjack.gameutils.card_display import (
    card_to_lines,
    face_down_lines,
    render_hand,
    RED,
    RESET,
)


def test_card_to_lines_returns_five_lines():
    card = Card("H", 1)
    lines = card_to_lines(card)
    assert len(lines) == 5


def test_card_to_lines_top_bottom_border():
    card = Card("S", 5)
    lines = card_to_lines(card)
    assert lines[0] == "\u250c\u2500\u2500\u2500\u2500\u2500\u2510"
    assert lines[4] == "\u2514\u2500\u2500\u2500\u2500\u2500\u2518"


def test_card_red_suit_has_color():
    card = Card("H", 1)
    lines = card_to_lines(card)
    # Heart suit should contain red ANSI code
    assert RED in lines[2]
    assert RESET in lines[2]


def test_card_black_suit_no_red():
    card = Card("S", 1)
    lines = card_to_lines(card)
    # Spade suit should not contain red ANSI code
    assert RED not in lines[2]


def test_face_down_returns_five_lines():
    lines = face_down_lines()
    assert len(lines) == 5


def test_face_down_has_blue():
    from blackjack.gameutils.card_display import BLUE
    lines = face_down_lines()
    assert BLUE in lines[1]


def test_render_hand_single_card():
    result = render_hand([Card("H", 1)])
    lines = result.split("\n")
    assert len(lines) == 5


def test_render_hand_multiple_cards():
    result = render_hand([Card("H", 1), Card("S", 13)])
    lines = result.split("\n")
    assert len(lines) == 5
    # Two cards joined by space should be wider than one
    assert len(lines[0]) > 7


def test_render_hand_hide_first():
    from blackjack.gameutils.card_display import BLUE
    result = render_hand([Card("H", 1), Card("S", 13)], hide_first=True)
    # First card should be face-down (contains blue)
    assert BLUE in result


def test_render_empty_hand():
    result = render_hand([])
    assert result == ""
