import os
import re
import shutil

from .gameutils.card_display import render_hand, RED, GREEN, YELLOW, BLUE, CYAN, RESET


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


HEADER_WIDTH = 60


def print_game_header(round_num=None):
    border = "\u2550" * HEADER_WIDTH
    if round_num is not None:
        title = f"BLACKJACK  |  Round {round_num}"
    else:
        title = "WELCOME TO BLACKJACK"
    print(border)
    print(f"  {title.center(HEADER_WIDTH - 4)}")
    print(border)


def _visible_len(s):
    """Return the visible length of a string, ignoring ANSI escape codes."""
    return len(re.sub(r'\033\[[0-9;]*m', '', s))


def _pad_to_visible(s, width):
    """Pad a string with spaces so its visible width equals `width`."""
    diff = width - _visible_len(s)
    return s + " " * max(0, diff)


def render_player_box(player, hide_first_card=False, is_active=False, box_width=None, first_card_override=None):
    """Render a player's hand inside a box, returning a list of strings."""
    # Build label with cash trend.
    if player.player_type == "dealer":
        label = "Dealer"
    else:
        trend = ""
        if hasattr(player, "prev_cash") and player.prev_cash != player.cash:
            if player.cash > player.prev_cash:
                trend = f" {GREEN}\u25b2{RESET}"
            else:
                trend = f" {RED}\u25bc{RESET}"

        if player.player_type == "normal":
            label = f"Player {player.player_id} (${player.cash}){trend}"
        else:
            label = f"P{player.player_id} (${player.cash}){trend}"

    # Active player is indicated by the cyan border — no label prefix needed.

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
        top = f"{CYAN}{top}{RESET}"
    lines.append(top)

    # Content lines.
    for line in inner_lines:
        padded = _pad_to_visible(f" {line}", inner_width)
        lines.append(f"\u2502{padded}\u2502")

    # Bottom border.
    bottom = "\u2514" + "\u2500" * inner_width + "\u2518"
    lines.append(bottom)

    return lines


def print_table(player_list, active_player_index=None, dealer_reveal=False, round_num=None, stats_player=None, dealer_hole_card_override=None):
    """Clear the screen and redraw the full table state with players side-by-side."""
    clear_terminal()
    print_game_header(round_num=round_num)
    print()

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
        box = render_player_box(player, hide_first_card=hide, is_active=is_active, first_card_override=override)
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

    # Second pass: use natural boxes as-is; only normalize heights within each row.
    for group in row_groups:
        row_boxes = [natural_boxes[i] for i in group]
        row_widths = [natural_widths[i] for i in group]

        # Normalize heights, padding each box with its own width.
        max_height = max(len(box) for box in row_boxes)
        for box, w in zip(row_boxes, row_widths):
            while len(box) < max_height:
                box.append("\u2502" + " " * (w - 2) + "\u2502")

        # Print row by joining lines horizontally.
        for line_idx in range(max_height):
            parts = [box[line_idx] for box in row_boxes]
            print(gap.join(parts))
        print()

    # Persistent session stats footer for the active human player.
    if stats_player is not None:
        _print_stats_footer(stats_player)


MENU_WIDTH = 60


def _key(k):
    """Return a cyan-colored key label like [H]."""
    return f"{CYAN}[{k}]{RESET}"


def print_action_menu(can_split=False, can_double=False, can_surrender=False, dealer_upcard_str=None, player_score=None):
    """Print the available actions menu."""
    print("\u2500" * MENU_WIDTH)
    if dealer_upcard_str:
        print(f"  Dealer shows: {dealer_upcard_str}")
    if player_score is not None:
        print(f"  Your score:   {player_score}")

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
            print(_pad_to_visible(left, col_width) + right)
        else:
            print(left)
    print("\u2500" * MENU_WIDTH)


def print_blackjack_banner(player_name):
    """Print a full-width celebratory banner for a natural blackjack."""
    inner = f"\u2605  BLACKJACK!  {player_name}  \u2605"
    content_width = HEADER_WIDTH - 2
    top = "\u2554" + "\u2550" * content_width + "\u2557"
    mid = "\u2551" + inner.center(content_width) + "\u2551"
    bot = "\u255a" + "\u2550" * content_width + "\u255d"
    print(f"\n{GREEN}{top}\n{mid}\n{bot}{RESET}\n")


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
    s = player.stats
    streak = s["streak"]
    if streak > 0:
        streak_str = f"{GREEN}W{streak}{RESET}"
    elif streak < 0:
        streak_str = f"{RED}L{abs(streak)}{RESET}"
    else:
        streak_str = "-"
    label = " Your Session "
    side = (HEADER_WIDTH - len(label)) // 2
    print("\u2500" * side + label + "\u2500" * (HEADER_WIDTH - side - len(label)))
    w  = f"{GREEN}{s['wins']}{RESET}"
    l  = f"{RED}{s['losses']}{RESET}"
    p  = f"{YELLOW}{s['pushes']}{RESET}"
    bj = f"{GREEN}{s['blackjacks']}{RESET}"
    print(f"  W:{w}  L:{l}  P:{p}  BJ:{bj}  Streak:{streak_str}  Cash:${player.cash}")
    print("\u2500" * HEADER_WIDTH)


OUTCOME_COLORS = {
    "WIN": GREEN,
    "BLACKJACK": GREEN,
    "EVEN MONEY": GREEN,
    "BUST": RED,
    "LOSE": RED,
    "PUSH": YELLOW,
    "SURRENDER": YELLOW,
}


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

    if dealer is None:
        dealer = player_list[-1]

    print()
    print("\u2550" * 50)
    print("  RESULTS")
    print("\u2550" * 50)

    for player in player_list[:-1]:
        label = f"Player {player.player_id}"
        for hand_idx, hand in enumerate(player.hands):
            outcome = determine_outcome(hand, dealer.hands[0])

            # Record stats.
            player.record_outcome(outcome)

            color = OUTCOME_COLORS.get(outcome, "")
            colored_outcome = f"{color}{outcome}{RESET}"

            # Special outcome displays.
            if outcome == "BLACKJACK":
                colored_outcome = f"{GREEN}*** BLACKJACK! ***{RESET}"
            elif outcome == "EVEN MONEY":
                colored_outcome = f"{GREEN}Even Money (guaranteed){RESET}"

            # Show payout — even money was already paid at offer time.
            if outcome == "EVEN MONEY":
                payout_str = f"{GREEN}+${hand.bet}{RESET}"
            else:
                payout = calculate_payout(hand, dealer.hands[0])
                payout_int = int(payout)
                if payout_int > 0:
                    payout_str = f"{GREEN}+${payout_int}{RESET}"
                elif payout_int < 0:
                    payout_str = f"{RED}-${abs(payout_int)}{RESET}"
                else:
                    payout_str = f"{YELLOW}$0{RESET}"

            hand_label = label
            if len(player.hands) > 1:
                hand_label = f"{label} (Hand {hand_idx + 1})"
            print(f"  {hand_label}: {colored_outcome}   {payout_str}")

    print("\u2500" * 50)


def print_player_stats(player):
    """Print running stats for the human player."""
    s = player.stats
    streak = s["streak"]
    if streak > 0:
        streak_str = f"{GREEN}W{streak}{RESET}"
    elif streak < 0:
        streak_str = f"{RED}L{abs(streak)}{RESET}"
    else:
        streak_str = "-"

    w  = f"{GREEN}{s['wins']}{RESET}"
    l  = f"{RED}{s['losses']}{RESET}"
    p  = f"{YELLOW}{s['pushes']}{RESET}"
    bj = f"{GREEN}{s['blackjacks']}{RESET}"
    bu = f"{RED}{s['busts']}{RESET}"
    print(
        f"  W:{w}   L:{l}   P:{p}   "
        f"BJ:{bj}   Bust:{bu}   "
        f"Streak:{streak_str}"
    )


def print_bust_message():
    """Print a prominent bust notification."""
    print(f"\n  {RED}!!! BUST !!!{RESET}\n")


def print_game_over(player, round_num):
    """Print a game over screen with session stats."""
    s = player.stats
    total_hands = s["wins"] + s["losses"] + s["pushes"] + s["surrenders"]
    border = "\u2550" * 50

    print()
    print(border)
    print(f"  {RED}{'G A M E   O V E R'.center(46)}{RESET}")
    print(border)
    print()
    print(f"  Rounds Played:  {round_num}")
    print(f"  Hands Played:   {total_hands}")
    print(f"  Peak Cash:      {GREEN}${s['peak_cash']}{RESET}")
    print(f"  Final Cash:     ${player.cash}")
    print()
    print(f"  Wins:           {GREEN}{s['wins']}{RESET}")
    print(f"  Losses:         {RED}{s['losses']}{RESET}")
    print(f"  Pushes:         {YELLOW}{s['pushes']}{RESET}")
    print(f"  Blackjacks:     {GREEN}{s['blackjacks']}{RESET}")
    print(f"  Busts:          {RED}{s['busts']}{RESET}")
    print(f"  Surrenders:     {s['surrenders']}")
    print()
    if total_hands > 0:
        win_pct = s["wins"] / total_hands * 100
        print(f"  Win Rate:       {win_pct:.1f}%")
    print(border)


def prompt_play_again():
    """Print a styled play-again separator and return the user's input."""
    print("\n" + "\u2500" * MENU_WIDTH)
    return input(f"  {CYAN}[return]{RESET} Play again   {CYAN}[q]{RESET} Quit  >>> ")
