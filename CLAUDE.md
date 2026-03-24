# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A CLI blackjack game built with Python and Typer. The goal is both Python practice and a testbed for understanding blackjack strategy.

## Build & Run

```bash
# Install in development mode
pip install -e .

# Install as isolated CLI tool
pipx install . --force

# Run the game
blackjack-app
blackjack-app --nplayers 2 --ndecks 1 --minbid 25 --init-cash 1000

# Run directly without installing
python -m blackjack
```

No test framework is configured yet. Individual modules have `if __name__ == "__main__"` blocks for manual testing (e.g., `python -m blackjack.gameutils.card`).

## Architecture

The CLI entry point is `src/blackjack/cli.py`, which uses Typer to expose the `startgame` command as `blackjack-app`.

**Game flow:** `cli.py` → `startgame()` in `startgame.py` → creates `BlackjackGame` which manages the game loop (deal, player input, dealer logic, scoring, replay prompt).

**`gameutils/`** contains the core game primitives:
- `Card` — dataclass with suit (D/C/S/H) and rank (1-13). Handles display mapping (1→A, 11→J, 12→Q, 13→K) with Unicode suit symbols.
- `DeckOfCards` — manages a 52-card deck with shuffle, draw (`get_card`), and tracks used cards.
- `Player` — holds a hand of cards, tracks player type (`normal`/`computer`/`dealer`), and implements hand scoring with ace soft/hard logic (ace=11, falls back to ace=1 if bust).

**`utils.py`** has terminal helpers (clear screen, decorative print).

## Active Refactor

The `bvegetabile/refactor` branch is moving card utilities from `cardutils/` to `gameutils/`, adding the `Player` class. The old `cardutils/` package is being deleted.
