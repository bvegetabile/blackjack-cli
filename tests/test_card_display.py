from blackjack.gameutils.card import Card
from blackjack.gameutils import palette
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
    # Heart suit should contain the palette's card_red ANSI code
    assert palette.active.card_red in lines[2]
    assert palette.active.reset in lines[2]


def test_card_black_suit_no_red():
    card = Card("S", 1)
    lines = card_to_lines(card)
    # Spade suit should not contain the card_red color
    assert palette.active.card_red not in lines[2]


def test_face_down_returns_five_lines():
    lines = face_down_lines()
    assert len(lines) == 5


def test_face_down_has_blue():
    lines = face_down_lines()
    assert palette.active.card_back in lines[1]


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
    result = render_hand([Card("H", 1), Card("S", 13)], hide_first=True)
    # First card should be face-down (contains card_back color)
    assert palette.active.card_back in result


def test_render_empty_hand():
    result = render_hand([])
    assert result == ""


def test_green_and_yellow_constants_exist():
    from blackjack.gameutils.card_display import GREEN, YELLOW
    assert GREEN == "\033[92m"
    assert YELLOW == "\033[93m"


def test_render_player_box_structure():
    from blackjack.gameutils.player import Player
    from blackjack.utils import render_player_box

    p = Player(player_id=1, player_type="normal")
    p.add_card_to_hand(Card("H", 1))
    p.add_card_to_hand(Card("S", 13))

    box = render_player_box(p)
    # Box should have: top border + 5 card lines + score line + bet line + bottom border = 9 lines
    assert len(box) == 9
    # Top should contain player label
    assert "Player 1" in box[0]
    # Bottom should be a border
    assert box[-1].startswith("\u2514")
    assert box[-1].endswith("\u2518")


def test_render_player_box_active_marker():
    from blackjack.gameutils.player import Player
    from blackjack.utils import render_player_box

    p = Player(player_id=1, player_type="normal")
    p.add_card_to_hand(Card("H", 1))
    p.add_card_to_hand(Card("S", 13))

    box = render_player_box(p, is_active=True)
    assert palette.active.highlight in box[0]


def test_render_player_box_dealer_hidden():
    from blackjack.gameutils.player import Player
    from blackjack.utils import render_player_box

    p = Player(player_id=None, player_type="dealer")
    p.add_card_to_hand(Card("H", 1))
    p.add_card_to_hand(Card("S", 13))

    box = render_player_box(p, hide_first_card=True)
    box_str = "\n".join(box)
    assert palette.active.card_back in box_str
    assert "Score: ???" in box_str
