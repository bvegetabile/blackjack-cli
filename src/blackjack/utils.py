import os
import re
import shutil

from .gameutils import palette
from .gameutils.card_display import render_hand


def clear_terminal():
    """Clears the terminal screen."""

    # For Windows
    if os.name == "nt":
        os.system("cls")

    # For macOS and Linux
    else:
        os.system("clear")


def vertical_pad(content_height):
    """Print blank lines to vertically center content_height lines in the terminal."""
    term_lines = shutil.get_terminal_size().lines
    pad = max(0, (term_lines - content_height) // 2)
    print("\n" * pad, end="")


def print_symbols(n_symbols=80, symbol="*"):
    p = palette.active
    offset = center_offset(n_symbols)
    print(offset + p.chrome + n_symbols * symbol + p.reset)


def print_statement_with_deco(
    statement="", n_symbols=80, symbol="", before=False, after=False
):
    offset = center_offset(n_symbols)
    if before:
        print_symbols(n_symbols=n_symbols, symbol=symbol)
    print(offset + statement)
    if after:
        print_symbols(n_symbols=n_symbols, symbol=symbol)


HEADER_WIDTH = 60


def print_game_header(round_num=None, vpad_content_height=0):
    """Print the game header. If vpad_content_height > 0, vertically center first."""
    p = palette.active
    if vpad_content_height > 0:
        vertical_pad(vpad_content_height)
    offset = center_offset(HEADER_WIDTH)
    border = p.chrome + "\u2500" * HEADER_WIDTH + p.reset
    if round_num is not None:
        title = f"BLACKJACK  |  Round {round_num}"
    else:
        title = "WELCOME TO BLACKJACK"
    print(offset + border)
    print(offset + f"  {p.chrome}{title.center(HEADER_WIDTH - 4)}{p.reset}")
    print(offset + border)


def _visible_len(s):
    """Return the visible length of a string, ignoring ANSI escape codes."""
    return len(re.sub(r'\033\[[0-9;]*m', '', s))


def _pad_to_visible(s, width):
    """Pad a string with spaces so its visible width equals `width`."""
    diff = width - _visible_len(s)
    return s + " " * max(0, diff)


def render_player_box(player, hide_first_card=False, is_active=False, box_width=None, first_card_override=None, has_active_player=False):
    """Render a player's hand inside a box, returning a list of strings."""
    p = palette.active
    # Build label with cash trend.
    if player.player_type == "dealer":
        label = "Dealer"
    else:
        trend = ""
        if hasattr(player, "prev_cash") and player.prev_cash != player.cash:
            if player.cash > player.prev_cash:
                trend = f" {p.win}\u25b2{p.reset}"
            else:
                trend = f" {p.loss}\u25bc{p.reset}"

        if player.player_type == "normal":
            label = f"Player {player.player_id} (${player.cash}){trend}"
        else:
            label = f"P{player.player_id} (${player.cash}){trend}"

    # Render cards for each hand.
    hand_blocks = []
    for idx, hand in enumerate(player.hands):
        hide = hide_first_card if idx == 0 else False
        card_str = render_hand(
            hand.cards,
            hide_first=hide,
            first_card_override=first_card_override if idx == 0 else None,
        )
        card_lines = card_str.split("\n") if card_str else []

        if not hide_first_card:
            score_line = f"Score: {hand.score()}"
        else:
            score_line = "Score: ???"

        if player.player_type != "dealer":
            bet_line = f"Bet: ${hand.bet}"
        else:
            bet_line = " "

        if len(player.hands) > 1:
            hand_blocks.append((f"Hand {idx + 1}:", card_lines, score_line, bet_line))
        else:
            hand_blocks.append((None, card_lines, score_line, bet_line))

    # Build inner content lines.
    inner_lines = []
    for hand_label, card_lines, score_line, bet_line in hand_blocks:
        if hand_label:
            inner_lines.append(hand_label)
        if card_lines:
            inner_lines.extend(card_lines)
        else:
            # Empty hand — pad to match card height (5 lines).
            inner_lines.extend([""] * 5)
        inner_lines.append(score_line)
        inner_lines.append(bet_line)

    # Calculate box width from content if not provided.
    if box_width is None:
        content_width = max((_visible_len(line) for line in inner_lines), default=0)
        # +1 ensures the label fits with at least remaining=0 in the top border formula.
        content_width = max(content_width, _visible_len(label) + 1)
        box_width = content_width + 4  # │ + space + content + space + │

    inner_width = box_width - 2  # space inside the │ borders

    # Build box lines.
    lines = []

    # Top border with label.
    label_segment = f" {label} "
    remaining = inner_width - _visible_len(label_segment) - 1  # -1 for leading ─
    top = f"\u250c\u2500{label_segment}" + "\u2500" * max(0, remaining) + "\u2510"
    if is_active:
        top = f"{p.highlight}{top}{p.reset}"
    elif has_active_player:
        top = f"{p.dim}{top}{p.reset}"
    lines.append(top)

    # Content lines.
    for line in inner_lines:
        padded = _pad_to_visible(f" {line}", inner_width)
        lines.append(f"\u2502{padded}\u2502")

    # Bottom border.
    bottom = "\u2514" + "\u2500" * inner_width + "\u2518"
    lines.append(bottom)

    return lines


def center_offset(content_width):
    """Return a string of spaces to center content_width in the terminal."""
    term_width = shutil.get_terminal_size().columns
    pad = max(0, (term_width - content_width) // 2)
    return " " * pad


def _print_context_header(round_num, stats_player, offset=""):
    """Print a compact context line above the player boxes."""
    p = palette.active
    if round_num is None and stats_player is None:
        return
    parts = []
    if round_num is not None:
        parts.append(f"{p.chrome}Round {round_num}{p.reset}")
    if stats_player is not None:
        s = stats_player.stats
        streak = s["streak"]
        if streak > 0:
            streak_str = f"{p.win}W{streak}{p.reset}{p.chrome}"
        elif streak < 0:
            streak_str = f"{p.loss}L{abs(streak)}{p.reset}{p.chrome}"
        else:
            streak_str = "-"
        stats_str = (
            f"{p.chrome}W:{s['wins']}  L:{s['losses']}  "
            f"P:{s['pushes']}  BJ:{s['blackjacks']}    "
            f"Streak: {streak_str}    "
            f"Cash: ${stats_player.cash}{p.reset}"
        )
        parts.append(stats_str)
    line = f"    ".join(parts)
    print(f"{offset}  {line}")
    print()


def print_table(player_list, active_player_index=None, dealer_reveal=False, round_num=None, stats_player=None, dealer_hole_card_override=None):
    """Clear the screen and redraw the full table state with players side-by-side."""
    clear_terminal()

    has_active = active_player_index is not None

    # Collect player info for rendering.
    player_info = []
    for i, player in enumerate(player_list):
        is_dealer = player.player_type == "dealer"
        hide = is_dealer and not dealer_reveal
        is_active = (i == active_player_index)
        player_info.append((player, hide, is_active))

    # First pass: render boxes to determine natural widths.
    natural_boxes = []
    natural_widths = []
    for player, hide, is_active in player_info:
        override = dealer_hole_card_override if player.player_type == "dealer" else None
        box = render_player_box(player, hide_first_card=hide, is_active=is_active,
                                first_card_override=override, has_active_player=has_active)
        natural_boxes.append(box)
        natural_widths.append(_visible_len(box[0]))

    # Group into rows. Use greedy approach: sum actual natural widths + gaps.
    term_width = shutil.get_terminal_size().columns
    gap = "  "
    gap_w = len(gap)

    row_groups = []
    current_row = []
    current_row_w = 0

    for idx in range(len(natural_boxes)):
        w = natural_widths[idx]
        tentative_count = len(current_row) + 1
        total_w = current_row_w + w + gap_w * (tentative_count - 1)

        if current_row and total_w > term_width:
            row_groups.append(current_row)
            current_row = [idx]
            current_row_w = w
        else:
            current_row.append(idx)
            current_row_w += w

    if current_row:
        row_groups.append(current_row)

    # Estimate total content height for vertical centering.
    # Context header (2 lines) + box rows + ~10 lines for menu/results below.
    box_lines = sum(max(len(natural_boxes[i]) for i in group) + 1 for group in row_groups)
    content_h = 2 + box_lines + 10
    vertical_pad(content_h)

    # Compute centering offset for the first row (used for context header alignment).
    if row_groups:
        first_group = row_groups[0]
        first_row_w = sum(natural_widths[i] for i in first_group) + gap_w * (len(first_group) - 1)
        header_offset = center_offset(max(first_row_w, MENU_WIDTH))
    else:
        header_offset = ""

    _print_context_header(round_num, stats_player, offset=header_offset)

    # Second pass: use natural boxes as-is; only normalize heights within each row.
    for group in row_groups:
        row_boxes = [natural_boxes[i] for i in group]
        row_widths = [natural_widths[i] for i in group]

        row_w = sum(row_widths) + gap_w * (len(group) - 1)
        offset = center_offset(max(row_w, MENU_WIDTH))

        # Normalize heights, padding each box with its own width.
        max_height = max(len(box) for box in row_boxes)
        for box, w in zip(row_boxes, row_widths):
            while len(box) < max_height:
                box.append("\u2502" + " " * (w - 2) + "\u2502")

        # Print row by joining lines horizontally.
        for line_idx in range(max_height):
            parts = [box[line_idx] for box in row_boxes]
            print(offset + gap.join(parts))
        print()


MENU_WIDTH = 60


def _key(k):
    """Return a chrome-colored key label like [H]."""
    p = palette.active
    return f"{p.chrome}[{k}]{p.reset}"


def print_action_menu(can_split=False, can_double=False, can_surrender=False, dealer_upcard_str=None, player_score=None):
    """Print the available actions menu."""
    p = palette.active
    offset = center_offset(MENU_WIDTH)
    sep = p.chrome + "\u2500" * MENU_WIDTH + p.reset
    print(offset + sep)
    if dealer_upcard_str:
        print(offset + f"  Dealer shows: {dealer_upcard_str}")
    if player_score is not None:
        print(offset + f"  Your score:   {player_score}")

    # Build ordered list of (key, description) pairs.
    items = [("H", "Hit"), ("S", "Stand")]
    if can_double:
        items.append(("D", "Double (\u00d72 bet, 1 card)"))
    if can_split:
        items.append(("P", "Split pairs"))
    if can_surrender:
        items.append(("R", "Surrender (\u00bd bet)"))
    items.append(("?", "Hint"))
    items.append(("Q", "Quit"))

    # Print two items per row using visible-length-aware padding.
    col_width = 32
    for i in range(0, len(items), 2):
        k1, label1 = items[i]
        left = f"  {_key(k1)} {label1}"
        if i + 1 < len(items):
            k2, label2 = items[i + 1]
            right = f"{_key(k2)} {label2}"
            print(offset + _pad_to_visible(left, col_width) + right)
        else:
            print(offset + left)
    print(offset + sep)


def print_blackjack_banner(player_name):
    """Print a full-width celebratory banner for a natural blackjack."""
    p = palette.active
    offset = center_offset(HEADER_WIDTH)
    inner = f"\u2605  BLACKJACK!  {player_name}  \u2605"
    content_width = HEADER_WIDTH - 2
    top = p.chrome + "\u250c" + "\u2500" * content_width + "\u2510" + p.reset
    mid = p.chrome + "\u2502" + p.reset + p.win + inner.center(content_width) + p.reset + p.chrome + "\u2502" + p.reset
    bot = p.chrome + "\u2514" + "\u2500" * content_width + "\u2518" + p.reset
    print(f"\n{offset}{top}\n{offset}{mid}\n{offset}{bot}\n")


def animate_dealer_reveal(player_list, round_num, animation_delay=0.4):
    """Animate the dealer's hole card peeling back row by row.

    animation_delay controls seconds per row reveal. Set to 0 to skip
    animation entirely (useful for simulations or fast play).
    """
    import time
    from .gameutils.card_display import partial_reveal_lines

    dealer = player_list[-1]
    hole_card = dealer.hands[0].cards[0]

    time.sleep(animation_delay * 1.25)  # Pause on face-down state before animation starts

    for n in range(1, 3):  # n=1: top row revealed; n=2: top two rows revealed
        override = partial_reveal_lines(hole_card, n)
        print_table(player_list, dealer_reveal=False, round_num=round_num,
                    dealer_hole_card_override=override)
        time.sleep(animation_delay)

    # Final frame: full reveal with score shown
    print_table(player_list, dealer_reveal=True, round_num=round_num)


def _print_stats_footer(player):
    """Print a persistent session stats line below the table."""
    p = palette.active
    s = player.stats
    streak = s["streak"]
    if streak > 0:
        streak_str = f"{p.win}W{streak}{p.reset}"
    elif streak < 0:
        streak_str = f"{p.loss}L{abs(streak)}{p.reset}"
    else:
        streak_str = "-"
    label = " Your Session "
    side = (HEADER_WIDTH - len(label)) // 2
    print(p.chrome + "\u2500" * side + label + "\u2500" * (HEADER_WIDTH - side - len(label)) + p.reset)
    w  = f"{p.win}{s['wins']}{p.reset}"
    l  = f"{p.loss}{s['losses']}{p.reset}"
    pu = f"{p.neutral}{s['pushes']}{p.reset}"
    bj = f"{p.win}{s['blackjacks']}{p.reset}"
    print(f"  W:{w}  L:{l}  P:{pu}  BJ:{bj}  Streak:{streak_str}  Cash:${player.cash}")
    print(p.chrome + "\u2500" * HEADER_WIDTH + p.reset)


def _outcome_color(outcome):
    """Return the palette color for a given outcome string."""
    p = palette.active
    if outcome in ("WIN", "BLACKJACK", "EVEN MONEY"):
        return p.win
    if outcome in ("BUST", "LOSE"):
        return p.loss
    return p.neutral


def determine_outcome(hand, dealer_hand):
    """Determine the outcome string for a hand vs dealer."""
    if hand.is_even_money:
        return "EVEN MONEY"
    if hand.is_surrendered:
        return "SURRENDER"
    if hand.score() > 21:
        return "BUST"
    if hand.is_natural_blackjack() and not dealer_hand.is_natural_blackjack():
        return "BLACKJACK"
    dealer_score = dealer_hand.score()
    hand_score = hand.score()
    if dealer_score > 21:
        return "WIN"
    if hand_score > dealer_score:
        return "WIN"
    if hand_score == dealer_score:
        return "PUSH"
    return "LOSE"


def print_results_table(player_list, dealer=None):
    """Print formatted results comparing each player to the dealer."""
    from .startgame import calculate_payout

    p = palette.active
    if dealer is None:
        dealer = player_list[-1]

    offset = center_offset(MENU_WIDTH)
    sep = p.chrome + "\u2500" * MENU_WIDTH + p.reset
    print()
    print(offset + sep)
    print(offset + f"  {p.chrome}RESULTS{p.reset}")
    print(offset + sep)

    for player in player_list[:-1]:
        label = f"Player {player.player_id}"
        for hand_idx, hand in enumerate(player.hands):
            outcome = determine_outcome(hand, dealer.hands[0])

            # Record stats.
            player.record_outcome(outcome)

            color = _outcome_color(outcome)
            colored_outcome = f"{color}{outcome}{p.reset}"

            # Special outcome displays.
            if outcome == "BLACKJACK":
                colored_outcome = f"{p.win}*** BLACKJACK! ***{p.reset}"
            elif outcome == "EVEN MONEY":
                colored_outcome = f"{p.win}Even Money (guaranteed){p.reset}"

            # Show payout — even money was already paid at offer time.
            if outcome == "EVEN MONEY":
                payout_str = f"{p.win}+${hand.bet}{p.reset}"
            else:
                payout = calculate_payout(hand, dealer.hands[0])
                payout_int = int(payout)
                if payout_int > 0:
                    payout_str = f"{p.win}+${payout_int}{p.reset}"
                elif payout_int < 0:
                    payout_str = f"{p.loss}-${abs(payout_int)}{p.reset}"
                else:
                    payout_str = f"{p.neutral}$0{p.reset}"

            hand_label = label
            if len(player.hands) > 1:
                hand_label = f"{label} (Hand {hand_idx + 1})"
            print(offset + f"  {hand_label}: {colored_outcome}   {payout_str}")

    print(offset + sep)


def print_player_stats(player):
    """Print running stats for the human player."""
    p = palette.active
    offset = center_offset(MENU_WIDTH)
    s = player.stats
    streak = s["streak"]
    if streak > 0:
        streak_str = f"{p.win}W{streak}{p.reset}"
    elif streak < 0:
        streak_str = f"{p.loss}L{abs(streak)}{p.reset}"
    else:
        streak_str = "-"

    w  = f"{p.win}{s['wins']}{p.reset}"
    l  = f"{p.loss}{s['losses']}{p.reset}"
    pu = f"{p.neutral}{s['pushes']}{p.reset}"
    bj = f"{p.win}{s['blackjacks']}{p.reset}"
    bu = f"{p.loss}{s['busts']}{p.reset}"
    print(
        f"{offset}  W:{w}   L:{l}   P:{pu}   "
        f"BJ:{bj}   Bust:{bu}   "
        f"Streak:{streak_str}"
    )


def print_bust_message():
    """Print a prominent bust notification."""
    p = palette.active
    offset = center_offset(MENU_WIDTH)
    print(f"\n{offset}  {p.loss}!!! BUST !!!{p.reset}\n")


def print_game_over(player, round_num):
    """Print a game over screen with session stats."""
    p = palette.active
    offset = center_offset(MENU_WIDTH)
    s = player.stats
    total_hands = s["wins"] + s["losses"] + s["pushes"] + s["surrenders"]
    border = p.chrome + "\u2500" * MENU_WIDTH + p.reset

    print()
    print(offset + border)
    print(offset + f"  {p.loss}{'G A M E   O V E R'.center(MENU_WIDTH - 4)}{p.reset}")
    print(offset + border)
    print()
    print(offset + f"  Rounds Played:  {round_num}")
    print(offset + f"  Hands Played:   {total_hands}")
    print(offset + f"  Peak Cash:      {p.win}${s['peak_cash']}{p.reset}")
    print(offset + f"  Final Cash:     ${player.cash}")
    print()
    print(offset + f"  Wins:           {p.win}{s['wins']}{p.reset}")
    print(offset + f"  Losses:         {p.loss}{s['losses']}{p.reset}")
    print(offset + f"  Pushes:         {p.neutral}{s['pushes']}{p.reset}")
    print(offset + f"  Blackjacks:     {p.win}{s['blackjacks']}{p.reset}")
    print(offset + f"  Busts:          {p.loss}{s['busts']}{p.reset}")
    print(offset + f"  Surrenders:     {s['surrenders']}")
    print()
    if total_hands > 0:
        win_pct = s["wins"] / total_hands * 100
        print(offset + f"  Win Rate:       {win_pct:.1f}%")
    print(offset + border)


def read_key():
    """Read one keypress from stdin without requiring Enter.

    Returns a string: 'up', 'down', 'left', 'right', 'enter', 'q',
    or the raw character for anything else. Raises KeyboardInterrupt on Ctrl-C.

    Falls back to line-based input when stdin is not a TTY (pipes, simulation).
    """
    import sys
    if not sys.stdin.isatty():
        line = input().strip().lower()
        if line in ('', 'enter'):
            return 'enter'
        return line[0] if line else 'enter'

    import tty
    import termios
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.buffer.read(1)
        if ch == b'\x03':
            raise KeyboardInterrupt
        if ch == b'\r' or ch == b'\n':
            return 'enter'
        if ch == b'\x1b':
            ch2 = sys.stdin.buffer.read(1)
            if ch2 == b'[':
                ch3 = sys.stdin.buffer.read(1)
                return {b'A': 'up', b'B': 'down',
                        b'C': 'right', b'D': 'left'}.get(ch3, 'unknown')
            return 'escape'
        return ch.decode('utf-8', errors='replace')
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def prompt_play_again():
    """Arrow-key play-again prompt. Returns '' to play again or 'q' to quit."""
    import sys
    p = palette.active
    options = ["Play again", "Quit"]
    # Lines rendered each pass: blank + separator + 2 options + hint = 5
    LINES = 5
    offset = center_offset(MENU_WIDTH)
    sel = 0
    first = True
    while True:
        p = palette.active
        sep = p.chrome + "\u2500" * MENU_WIDTH + p.reset
        if not first:
            # Erase previous render: move up LINES lines then clear to end of screen.
            sys.stdout.write(f"\033[{LINES}F\033[J")
            sys.stdout.flush()
        first = False
        print("\n" + offset + sep)
        for i, opt in enumerate(options):
            if i == sel:
                print(offset + f"  {p.highlight}\u25b6 {opt}{p.reset}")
            else:
                print(offset + f"    {opt}")
        print(offset + f"{p.dim}\u2191\u2193 navigate   Enter select{p.reset}")
        key = read_key()
        if key in ('up', 'down'):
            sel = (sel + 1) % len(options)
        elif key == 'enter':
            return '' if sel == 0 else 'q'
        elif key == 'q':
            return 'q'
