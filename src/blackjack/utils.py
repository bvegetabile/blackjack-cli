import os


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


def print_table(player_list, active_player_index=None, dealer_reveal=False):
    """Clear the screen and redraw the full table state."""
    clear_terminal()
    print_game_header()
    print()

    for i, player in enumerate(player_list):
        is_dealer = player.player_type == "dealer"
        hide = is_dealer and not dealer_reveal

        # Label
        if is_dealer:
            label = "Dealer"
        elif player.player_type == "normal":
            label = f"Player {player.player_id}"
        else:
            label = f"Player {player.player_id} (computer)"

        if i == active_player_index:
            label = f">>> {label} (your turn)"

        print(label)
        player.print_hand(hide_first_card=hide, show_player_id=False)


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

            hand_label = label
            if len(player.hands) > 1:
                hand_label = f"{label} (Hand {hand_idx + 1})"
            print(f"  {hand_label}: {outcome}  (You: {hand_score} | Dealer: {dealer_score})")

    print_symbols(n_symbols=40, symbol="\u2500")
