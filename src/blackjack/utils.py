import os
import re
import shutil

from .gameutils.card_display import render_hand, RED, GREEN, YELLOW, RESET


def clear_terminal():
    """Clears the terminal screen."""

    # For Windows
    if os.name == "nt":
        os.system("cls")

    # For macOS and Linux
    else:
        os.system("clear")


def print_symbols(n_symbols=80, symbol="*"):
    print(n_symbols * symbol)


def print_statement_with_deco(
    statement="", n_symbols=80, symbol="", before=False, after=False
):
    if before:
        print_symbols(n_symbols=n_symbols, symbol=symbol)
    print(statement)
    if after:
        print_symbols(n_symbols=n_symbols, symbol=symbol)


def print_game_header():
    print_statement_with_deco(
        "WELCOME TO BLACKJACK", symbol="*", before=True, after=True
    )


def _visible_len(s):
    """Return the visible length of a string, ignoring ANSI escape codes."""
    return len(re.sub(r'\033\[[0-9;]*m', '', s))


def _pad_to_visible(s, width):
    """Pad a string with spaces so its visible width equals `width`."""
    diff = width - _visible_len(s)
    return s + " " * max(0, diff)


def render_player_box(player, hide_first_card=False, is_active=False, box_width=None):
    """Render a player's hand inside a box, returning a list of strings."""
    # Build label.
    if player.player_type == "dealer":
        label = "Dealer"
    elif player.player_type == "normal":
        label = f"Player {player.player_id}"
    else:
        label = f"P{player.player_id} (cpu)"

    if is_active:
        label = f">>> {label}"

    # Render cards for each hand.
    hand_blocks = []
    for idx, hand in enumerate(player.hands):
        hide = hide_first_card if idx == 0 else False
        card_str = render_hand(hand.cards, hide_first=hide)
        card_lines = card_str.split("\n") if card_str else []

        if not hide_first_card:
            score_line = f"Score: {hand.score()}"
        else:
            score_line = "Score: ???"

        if len(player.hands) > 1:
            hand_blocks.append((f"Hand {idx + 1}:", card_lines, score_line))
        else:
            hand_blocks.append((None, card_lines, score_line))

    # Build inner content lines.
    inner_lines = []
    for hand_label, card_lines, score_line in hand_blocks:
        if hand_label:
            inner_lines.append(hand_label)
        inner_lines.extend(card_lines)
        if score_line:
            inner_lines.append(score_line)

    # Calculate box width from content if not provided.
    if box_width is None:
        content_width = max((_visible_len(line) for line in inner_lines), default=0)
        content_width = max(content_width, _visible_len(label))
        box_width = content_width + 4  # │ + space + content + space + │

    inner_width = box_width - 2  # space inside the │ borders

    # Build box lines.
    lines = []

    # Top border with label.
    label_segment = f" {label} "
    remaining = inner_width - len(label_segment) - 1  # -1 for leading ─
    top = f"\u250c\u2500{label_segment}" + "\u2500" * max(0, remaining) + "\u2510"
    lines.append(top)

    # Content lines.
    for line in inner_lines:
        padded = _pad_to_visible(f" {line}", inner_width)
        lines.append(f"\u2502{padded}\u2502")

    # Bottom border.
    bottom = "\u2514" + "\u2500" * inner_width + "\u2518"
    lines.append(bottom)

    return lines


def print_table(player_list, active_player_index=None, dealer_reveal=False):
    """Clear the screen and redraw the full table state with players side-by-side."""
    clear_terminal()
    print_game_header()
    print()

    # Render each player's box.
    boxes = []
    for i, player in enumerate(player_list):
        is_dealer = player.player_type == "dealer"
        hide = is_dealer and not dealer_reveal
        is_active = (i == active_player_index)
        box = render_player_box(player, hide_first_card=hide, is_active=is_active)
        boxes.append(box)

    # Determine how many fit per row based on terminal width.
    term_width = shutil.get_terminal_size().columns
    gap = "  "

    rows_of_boxes = []
    current_row = []
    current_width = 0

    for box in boxes:
        box_w = _visible_len(box[0])
        needed = box_w + (len(gap) if current_row else 0)

        if current_row and current_width + needed > term_width:
            rows_of_boxes.append(current_row)
            current_row = [box]
            current_width = box_w
        else:
            current_row.append(box)
            current_width += needed

    if current_row:
        rows_of_boxes.append(current_row)

    # Normalize box heights within each row and print.
    for row in rows_of_boxes:
        max_height = max(len(box) for box in row)
        # Pad shorter boxes with empty lines matching their width.
        padded_row = []
        for box in row:
            box_w = _visible_len(box[0])
            while len(box) < max_height:
                box.append("\u2502" + " " * (box_w - 2) + "\u2502")
            padded_row.append(box)

        # Print row by joining lines horizontally.
        for line_idx in range(max_height):
            parts = [box[line_idx] for box in padded_row]
            print(gap.join(parts))
        print()


def print_action_menu(can_split=False, can_double=False):
    """Print the available actions menu."""
    print("\u2500" * 28)
    line1 = " [H] Hit    [S] Stand    [Q] Quit"
    print(line1)
    extras = []
    if can_double:
        extras.append("[D] Double Down")
    if can_split:
        extras.append("[P] Split")
    if extras:
        print(" " + "   ".join(extras))
    print("\u2500" * 28)


OUTCOME_COLORS = {
    "WIN": GREEN,
    "BUST": RED,
    "LOSE": RED,
    "PUSH": YELLOW,
}


def print_results_table(player_list):
    """Print formatted results comparing each player to the dealer."""
    dealer = player_list[-1]
    dealer_score = dealer.score_hand()

    print()
    print_symbols(n_symbols=40, symbol="\u2500")
    print("RESULTS")
    print_symbols(n_symbols=40, symbol="\u2500")

    for player in player_list[:-1]:
        label = f"Player {player.player_id}"
        for hand_idx, hand in enumerate(player.hands):
            hand_score = hand.score()
            if hand_score > 21:
                outcome = "BUST"
            elif dealer_score > 21:
                outcome = "WIN"
            elif hand_score > dealer_score:
                outcome = "WIN"
            elif hand_score == dealer_score:
                outcome = "PUSH"
            else:
                outcome = "LOSE"

            color = OUTCOME_COLORS.get(outcome, "")
            colored_outcome = f"{color}{outcome}{RESET}"

            hand_label = label
            if len(player.hands) > 1:
                hand_label = f"{label} (Hand {hand_idx + 1})"
            print(f"  {hand_label}: {colored_outcome}  (You: {hand_score} | Dealer: {dealer_score})")

    print_symbols(n_symbols=40, symbol="\u2500")
