from .card import Card, RANK_MAPPING, SHAPE_MAPPING

# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"

RED_SUITS = {"H", "D"}


def _rank_str(card):
    """Get the display string for a card's rank."""
    return str(RANK_MAPPING.get(card.rank, card.rank))


def _suit_str(card):
    """Get the display string for a card's suit."""
    return SHAPE_MAPPING.get(card.suit, card.suit)


def _colorize(text, suit):
    """Wrap text in ANSI color based on suit."""
    if suit in RED_SUITS:
        return f"{RED}{text}{RESET}"
    return text


def card_to_lines(card):
    """Return 5-line list representing an ASCII card with colored suit."""
    rank = _rank_str(card)
    suit = _suit_str(card)
    color_rank = _colorize(rank, card.suit)
    color_suit = _colorize(suit, card.suit)

    # Handle alignment for "10" (2 chars) vs single-char ranks
    if len(rank) == 2:
        top_rank = f"{color_rank}   "
        bot_rank = f"   {color_rank}"
    else:
        top_rank = f"{color_rank}    "
        bot_rank = f"    {color_rank}"

    return [
        "\u250c\u2500\u2500\u2500\u2500\u2500\u2510",
        f"\u2502{top_rank}\u2502",
        f"\u2502  {color_suit}  \u2502",
        f"\u2502{bot_rank}\u2502",
        "\u2514\u2500\u2500\u2500\u2500\u2500\u2518",
    ]


def face_down_lines():
    """Return 5-line list for a face-down card with blue tint."""
    fill = f"{BLUE}\u2593\u2593\u2593\u2593\u2593{RESET}"
    return [
        "\u250c\u2500\u2500\u2500\u2500\u2500\u2510",
        f"\u2502{fill}\u2502",
        f"\u2502{fill}\u2502",
        f"\u2502{fill}\u2502",
        "\u2514\u2500\u2500\u2500\u2500\u2500\u2518",
    ]


def render_hand(cards, hide_first=False):
    """Render a list of cards side-by-side as a multi-line string."""
    if not cards:
        return ""

    all_lines = []
    for i, card in enumerate(cards):
        if i == 0 and hide_first:
            all_lines.append(face_down_lines())
        else:
            all_lines.append(card_to_lines(card))

    # Join cards horizontally with 1-space gap
    rows = []
    for row_idx in range(5):
        rows.append(" ".join(line_set[row_idx] for line_set in all_lines))

    return "\n".join(rows)
