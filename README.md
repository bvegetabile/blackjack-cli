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
# Play (your name and session history are saved by default)
blackjack-app

# Play without saving any session data
blackjack-app --anonymous

# Override your player name
blackjack-app --player-name "Alice"

# Enable basic strategy hints
blackjack-app --hints

# Show a hand-by-hand history log when you quit
blackjack-app --history

# Control the speed of the dealer reveal animation (seconds per row; 0 = instant)
blackjack-app --animation-delay 0.2
```

### Sessions

On first launch the game confirms your name (pulled from your OS username) and creates a
player profile. After that, each time you start you'll see a session menu where you can:

- **Resume** a previous session — restores your round number, shoe state, cash, and stats
- **Start a new session** — configure the table fresh with arrow-key navigation
- **Quit**

The new session setup screen lets you pick your table settings using `↑↓` to move between
rows and `←→` to change values, then `Enter` to start:

| Setting | Options | Default |
|---------|---------|---------|
| Decks in shoe | 1, 2, 4, 6, 8 | 6 |
| Starting cash | $250 – $5,000 | $1,000 |
| Minimum bet | $5 – $100 | $25 |
| CPU opponents | 0 – 3 | 0 |

Use `--anonymous` to skip identity and session storage entirely and jump straight to setup.

### Betting

Each round begins with a bet. Press Enter to repeat your last bet (or use the table minimum
on the first round). Your cash balance is shown in your player box.

- **Game over**: If you can't afford the minimum bet, you'll see a session summary and can restart with fresh cash
- **Computer players**: Bet randomly; if they go broke, there's a 50% chance they buy back in

### What You'll See

- **Player boxes** show each hand with ASCII card art, score, and current bet. Your box has a cyan border when it's your turn, and a ▲ or ▼ arrow after rounds where your cash changed.
- **Stats footer** below the table tracks your running session: wins, losses, pushes, blackjacks, current streak, and cash balance.
- **Dealer reveal** animates row by row when the hole card is flipped. Speed is controlled by `--animation-delay`.
- **Blackjack banner** appears when you or another player hits a natural blackjack.

### Game Controls

Each turn you'll see your hand displayed as ASCII cards with your current score at the prompt:

| Key | Action |
|-----|--------|
| `H` or Enter | Hit — draw another card |
| `S` | Stand — keep your hand |
| `D` | Double Down — double your bet, draw one card, and stand (first two cards only) |
| `P` | Split — split a pair into two hands, each with its own bet (matching ranks only) |
| `R` | Surrender — forfeit half your bet and end the hand (first action only) |
| `?` | Hint — show a basic strategy recommendation for your current hand |
| `Q` | Quit — exit the game |

### Payouts

| Outcome | Payout |
|---------|--------|
| Natural Blackjack (A + face card) | 3:2 (bet $100, win $150) |
| Win | 1:1 |
| Push (tie) | Bet returned |
| Lose / Bust | Bet lost |
| Surrender | Half bet returned |

### Insurance & Even Money

When the dealer's visible card is an Ace:

- **Even money**: If you have a natural blackjack, you'll be offered a guaranteed 1:1 payout now rather than risking a push if the dealer also has blackjack.
- **Insurance**: Otherwise, you can buy insurance for half your bet. If the dealer has blackjack, insurance pays 2:1; if not, the insurance bet is lost.

### Rules

- Cards 2-10 are face value; J, Q, K are worth 10; Aces are 11 (or 1 if you'd bust)
- Beat the dealer's hand without going over 21
- Dealer stands on all 17s (S17)
- Split aces receive one card each and auto-stand (no re-splitting aces)
- You can split up to 4 hands total
- Surrender is only available as your very first action (before any hit, double, or split)
- Computer players use the same strategy as the dealer (hit on 16 or less)
- The shoe persists across rounds and reshuffles at ~75% penetration

### Learning Features

- **`--hints`**: Displays the recommended action and the reasoning behind it automatically before each prompt (e.g., "Hint: DOUBLE — 11 is the best doubling hand — any 10-value card gives you 21")
- **`?` key**: Available at any action prompt for an on-demand hint — shows the strategy recommendation without consuming your turn
- **`--history`**: Displays a hand-by-hand log at the end of your session showing cards, bets, outcomes, and payouts
- **`--animation-delay`**: Controls how fast the dealer's hole card is revealed (default 0.4 seconds per row; set to 0 to skip animation entirely)

## Running Tests

```bash
pytest -v
```
