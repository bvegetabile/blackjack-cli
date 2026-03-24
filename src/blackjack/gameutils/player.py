PLAYER_TYPES = [
    "normal",
    "dealer",
    "computer"
]

RANK_SCORES = {
    1: 11,
    11: 10,
    12: 10,
    13: 10
}


class Player:
    def __init__(self, player_id=None, player_type=None, starting_cash=0):
        self.player_id = player_id
        self.player_type = player_type
        self.hand = []
        self.score = None
        self.last_player_action = None
        self.cash = starting_cash

    def update_cash(self, delta):
        self.cash += delta

    def add_card_to_hand(self, new_card):
        self.hand.append(new_card)
        if len(self.hand) >= 2:
            self.score = self.score_hand()

    def get_hand_as_str(self, hide_first_card=False):
        cards_str = ', '.join([
            '??'
            if i == 0 and hide_first_card
            else str(x)
            for i, x in enumerate(self.hand)]
        )
        if not hide_first_card:
            str_out = f"[{cards_str}], Score: {self.score}"
        else:
            str_out = f"[{cards_str}]"
        return str_out

    def print_hand(self, hide_first_card=False, show_player_id=True):
        if self.player_type != "dealer" and show_player_id:
            print(f"Player {self.player_id}")
        elif show_player_id:
            print("Dealer")

        print(self.get_hand_as_str(hide_first_card=hide_first_card))
        print(60*".")

    def score_hand(self):
        score = 0
        ace_count = 0
        for card in self.hand:
            card_score = RANK_SCORES.get(card.rank, card.rank)
            score += card_score
            if card.rank == 1:
                ace_count += 1
        while score > 21 and ace_count > 0:
            score -= 10
            ace_count -= 1
        return score

