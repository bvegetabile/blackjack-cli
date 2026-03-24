# blackjack-cli

Simple command line implementation of the game Blackjack.

## Purpose

The goal of this project is two fold.

1) Practice and hone some python programming in a controlled environment.
2) Provide a testbed for helping myself understand the game of blackjack better.

## Installation

Requires Python 3.8+.

```bash
# Clone the repo
git clone https://github.com/bvegetabile/blackjack-cli.git
cd blackjack-cli

# Install (includes the blackjack-app command)
pip install -e .

# Or install with dev dependencies (pytest)
pip install -e ".[dev]"
```

## How to Play

Start a game from the terminal:

```bash
# Play solo against the dealer
blackjack-app

# Play with computer opponents and multiple decks
blackjack-app --nplayers 3 --ndecks 2
```

### Game Controls

Each turn you'll see your hand displayed as ASCII cards with your current score at the prompt:

| Key | Action |
|-----|--------|
| `H` or Enter | Hit — draw another card |
| `S` | Stand — keep your hand |
| `D` | Double Down — draw one card and stand (first two cards only) |
| `P` | Split — split a pair into two hands (matching ranks only) |
| `Q` | Quit — exit the game |

### Rules

- Cards 2-10 are face value; J, Q, K are worth 10; Aces are 11 (or 1 if you'd bust)
- Beat the dealer's hand without going over 21
- Dealer hits on 17 or less
- Computer players use the same strategy as the dealer (hit on 16 or less)

After each hand, press Enter to play again or `Q` to quit.

## Running Tests

```bash
pytest -v
```
