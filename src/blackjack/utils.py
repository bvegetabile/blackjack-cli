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


def render_player_box(player, hide_first_card=False, is_active=False, box_width=None):
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
        content_width = max(content_width, _visible_len(label))
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


def print_table(player_list, active_player_index=None, dealer_reveal=False, round_num=None):
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
        box = render_player_box(player, hide_first_card=hide, is_active=is_active)
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
        print(f"  Player shows: {player_score}")
    line1 = f" {_key('H')} Hit    {_key('S')} Stand    {_key('Q')} Quit"
    print(line1)
    extras = []
    if can_double:
        extras.append(f"{_key('D')} Double Down")
    if can_split:
        extras.append(f"{_key('P')} Split")
    if can_surrender:
        extras.append(f"{_key('R')} Surrender")
    if extras:
        print(" " + "   ".join(extras))
    print("\u2500" * MENU_WIDTH)


OUTCOME_COLORS = {
    "WIN": GREEN,
    "BLACKJACK": GREEN,
    "BUST": RED,
    "LOSE": RED,
    "PUSH": YELLOW,
    "SURRENDER": YELLOW,
}


def determine_outcome(hand, dealer_hand):
    """Determine the outcome string for a hand vs dealer."""
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

            # Blackjack celebration.
            if outcome == "BLACKJACK":
                colored_outcome = f"{GREEN}*** BLACKJACK! ***{RESET}"

            # Show payout.
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
