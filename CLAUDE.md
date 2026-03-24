# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run

```bash
# Install in development mode (includes pytest)
pip install -e ".[dev]"

# Run the game
blackjack-app
blackjack-app --nplayers 2 --ndecks 2

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

**`utils.py`** has display helpers: `print_table()` (clear + full redraw), `print_action_menu()`, `print_results_table()`, and terminal utilities.

**`startgame.py`** contains the `BlackjackGame` class (game loop in `__init__`), `get_player_action()` for input parsing via `ACTION_MAP`, and the `startgame()` Typer command.

## Testing

pytest with tests in `tests/`. Game integration tests use `monkeypatch` to mock `input()` and `clear_terminal()`. For deterministic card order, use `init_shuffled=False` or monkeypatch `DeckOfCards.get_card`.
