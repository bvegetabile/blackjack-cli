from .hand import Hand

PLAYER_TYPES = [
    "normal",
    "dealer",
    "computer"
]


class Player:
    def __init__(self, player_id=None, player_type=None, starting_cash=0):
        self.player_id = player_id
        self.player_type = player_type
        self.hands = [Hand()]
        self.score = None
        self.last_player_action = None
        self.cash = starting_cash
        self.prev_cash = starting_cash
        self.stats = {
            "wins": 0,
            "losses": 0,
            "pushes": 0,
            "blackjacks": 0,
            "busts": 0,
            "surrenders": 0,
            "peak_cash": starting_cash,
            "streak": 0,
        }

    @property
    def hand(self):
        """Backward-compatible access to the first hand's cards."""
        return self.hands[0].cards

    def update_cash(self, delta):
        self.prev_cash = self.cash
        self.cash += delta
        if self.cash > self.stats["peak_cash"]:
            self.stats["peak_cash"] = self.cash

    def record_outcome(self, outcome):
        """Record a hand outcome for stats tracking."""
        if outcome in ("WIN", "BLACKJACK"):
            self.stats["wins"] += 1
            if outcome == "BLACKJACK":
                self.stats["blackjacks"] += 1
            self.stats["streak"] = max(1, self.stats["streak"] + 1)
        elif outcome in ("LOSE", "BUST"):
            self.stats["losses"] += 1
            if outcome == "BUST":
                self.stats["busts"] += 1
            self.stats["streak"] = min(-1, self.stats["streak"] - 1)
        elif outcome == "SURRENDER":
            self.stats["surrenders"] += 1
            self.stats["streak"] = min(-1, self.stats["streak"] - 1)
        elif outcome == "EVEN MONEY":
            self.stats["wins"] += 1
            self.stats["streak"] = max(1, self.stats["streak"] + 1)
        elif outcome == "PUSH":
            self.stats["pushes"] += 1
            self.stats["streak"] = 0

    def add_card_to_hand(self, new_card, hand_index=0):
        self.hands[hand_index].add_card(new_card)
        if len(self.hands[hand_index].cards) >= 2:
            self.score = self.hands[0].score()

    def score_hand(self, hand_index=0):
        return self.hands[hand_index].score()

    def get_hand_as_str(self, hide_first_card=False, hand_index=0):
        cards = self.hands[hand_index].cards
        cards_str = ', '.join([
            '??'
            if i == 0 and hide_first_card
            else str(x)
            for i, x in enumerate(cards)]
        )
        if not hide_first_card:
            str_out = f"[{cards_str}], Score: {self.hands[hand_index].score()}"
        else:
            str_out = f"[{cards_str}]"
        return str_out

    def print_hand(self, hide_first_card=False, show_player_id=True):
        from .card_display import render_hand

        if self.player_type != "dealer" and show_player_id:
            print(f"Player {self.player_id}")
        elif show_player_id:
            print("Dealer")

        for idx, hand in enumerate(self.hands):
            if len(self.hands) > 1:
                print(f"  Hand {idx + 1}:")
            print(render_hand(hand.cards, hide_first=hide_first_card))
            if not hide_first_card:
                print(f"  Score: {hand.score()}")
        print()

    def reset_hands(self):
        """Reset to a single empty hand for a new round."""
        self.hands = [Hand()]
        self.score = None
        self.last_player_action = None
