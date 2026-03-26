# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run

```bash
# Install in development mode (includes pytest)
pip install -e ".[dev]"

# Run the game (settings chosen interactively)
blackjack-app
blackjack-app --anonymous   # skip session storage
blackjack-app --hints       # show basic strategy hints

# Run tests
pytest -v

# Run directly without installing
python -m blackjack
```

## Git Workflow

**Never push directly to main.** All work happens on feature branches with PRs:

1. Create a feature branch (e.g., `bvegetabile/feature-name`)
2. Commit changes to the branch
3. Open a PR for review
4. Merge to `main` only after reviewing together

## Architecture

The CLI entry point is `src/blackjack/cli.py`, which uses Typer to expose the `startgame` command as `blackjack-app`.

**Game flow:** `cli.py` → `startgame()` in `startgame.py` → creates `BlackjackGame` which manages the game loop (deal, player input, dealer logic, scoring, replay prompt).

**`gameutils/`** contains the core game primitives:
- `Card` — dataclass with suit (D/C/S/H) and rank (1-13). Display mapping (1→A, 11→J, 12→Q, 13→K) with Unicode suit symbols.
- `card_display` — multi-line ASCII card art with ANSI colors (red for hearts/diamonds, blue for face-down). `render_hand()` joins cards side-by-side.
- `Hand` — represents a single hand of cards. Owns scoring logic (ace soft/hard), and split/double-down eligibility checks (`can_split()`, `can_double()`).
- `DeckOfCards` — manages card deck(s) with `ndecks` support, shuffle, draw (`get_card`), and tracks used cards.
- `Player` — holds one or more `Hand` objects (for splits), tracks player type (`normal`/`computer`/`dealer`). Backward-compatible `hand` property returns first hand's cards.

**`utils.py`** has display helpers and constants:
- `HEADER_WIDTH = 60`, `MENU_WIDTH = 60` — shared width constants used across all separators and borders.
- `print_game_header(round_num=None)` — `═` double-line border; embeds round number when provided.
- `print_table()` — clears screen and redraws all player boxes side-by-side. Boxes size to their **natural card content width** (no uniform stretching). Active player box border is highlighted in cyan.
- `render_player_box()` — renders one player's hand inside a unicode box. Width is `max(card_content, label+1) + 4` to guarantee the top-border label always fits without overhanging.
- `print_action_menu(can_split, can_double, can_surrender, dealer_upcard_str, player_score)` — 60-char wide menu with cyan key labels; only shows actions that are currently available; optionally shows dealer and player scores.
- `print_blackjack_banner(player_name)` — celebratory double-border banner for natural blackjacks.
- `animate_dealer_reveal(player_list, round_num, animation_delay)` — animates the dealer's hole card peeling back row by row; `animation_delay` controls seconds per row (0 = instant).
- `determine_outcome(hand, dealer_hand)` — returns outcome string (WIN/LOSE/PUSH/BUST/BLACKJACK/SURRENDER/EVEN MONEY).
- `_print_stats_footer(player)` — persistent W/L/P/BJ/Streak/Cash line shown below the table during active play.
- `print_results_table()`, `print_player_stats()`, `print_game_over()`, `print_bust_message()`, `prompt_play_again()` — round-end and session display helpers.

**`startgame.py`** contains the `BlackjackGame` class (game loop in `__init__`), `get_player_action()` for input parsing via `ACTION_MAP`, `get_player_bet()` for the bet prompt (Enter repeats last bet), `calculate_payout(hand, dealer_hand)` for net cash changes, `get_basic_strategy_hint(hand, dealer_upcard_rank, can_split, can_double)` for the hints system, and the `startgame()` Typer command. Session/identity helpers: `_resolve_player()` (OS username + DB lookup), `_show_session_menu()` (resume/new/quit with arrow-key nav), `_get_new_session_config()` (interactive setup screen for ndecks/cash/minbid/opponents).

## Testing

pytest with tests in `tests/`. Game integration tests use `monkeypatch` to mock `input()` and `clear_terminal()`. For deterministic card order, use `init_shuffled=False` or monkeypatch `DeckOfCards.get_card`.
