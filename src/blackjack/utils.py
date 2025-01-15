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
