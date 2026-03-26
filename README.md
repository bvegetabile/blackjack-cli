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
# Play solo against the dealer (default: $1000 cash, $25 minimum bet)
blackjack-app

# Customize starting cash and minimum bet
blackjack-app --init-cash 500 --minbid 10

# Play with computer opponents and multiple decks
blackjack-app --nplayers 3 --ndecks 2

# Enable basic strategy hints
blackjack-app --hints

# Show hand history log when you quit or go broke
blackjack-app --history

# Control the speed of the dealer hole-card reveal animation (seconds per row; 0 = instant)
blackjack-app --animation-delay 0.2
```

### Betting

Each round begins with a bet. Press Enter to repeat your last bet (or use the table minimum on the first round). Your cash balance is shown in your player box.

- **Game over**: If you can't afford the minimum bet, you'll see a session summary and can restart with fresh cash
- **Computer players**: Bet randomly; if they go broke, there's a 50% chance they buy back in

### Game Controls

Each turn you'll see your hand displayed as ASCII cards with your current score at the prompt:

| Key | Action |
|-----|--------|
| `H` or Enter | Hit — draw another card |
| `S` | Stand — keep your hand |
| `D` | Double Down — double your bet, draw one card, and stand (first two cards only) |
| `P` | Split — split a pair into two hands, each with its own bet (matching ranks only) |
| `R` | Surrender — forfeit half your bet and end the hand (first action only) |
| `Q` | Quit — exit the game |

### Payouts

| Outcome | Payout |
|---------|--------|
| Natural Blackjack (A + face card) | 3:2 (bet $100, win $150) |
| Win | 1:1 |
| Push (tie) | Bet returned |
| Lose / Bust | Bet lost |
| Surrender | Half bet returned |

### Insurance

When the dealer's visible card is an Ace, you'll be offered insurance at half your bet. If the dealer has blackjack, insurance pays 2:1.

### Rules

- Cards 2-10 are face value; J, Q, K are worth 10; Aces are 11 (or 1 if you'd bust)
- Beat the dealer's hand without going over 21
- Dealer stands on all 17s (S17)
- Split aces receive one card each and auto-stand (no re-splitting aces)
- Computer players use the same strategy as the dealer (hit on 16 or less)
- The shoe persists across rounds and reshuffles at ~75% penetration

### Learning Features

- **`--hints`**: Shows basic strategy recommendations before each action (e.g., "Hint: Basic strategy says HIT")
- **`--history`**: Displays a hand-by-hand log at the end of your session showing cards, bets, outcomes, and payouts

## Running Tests

```bash
pytest -v
```
