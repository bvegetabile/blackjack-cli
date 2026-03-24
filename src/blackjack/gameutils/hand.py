RANK_SCORES = {
    1: 11,
    11: 10,
    12: 10,
    13: 10
}


class Hand:
    def __init__(self, cards=None, bet=0):
        self.cards = cards if cards is not None else []
        self.bet = bet
        self.is_standing = False
        self.is_doubled = False
        self._is_surrendered = False

    def add_card(self, card):
        self.cards.append(card)

    def score(self):
        total = 0
        ace_count = 0
        for card in self.cards:
            card_score = RANK_SCORES.get(card.rank, card.rank)
            total += card_score
            if card.rank == 1:
                ace_count += 1
        while total > 21 and ace_count > 0:
            total -= 10
            ace_count -= 1
        return total

    def is_bust(self):
        return self.score() > 21

    def can_split(self):
        return len(self.cards) == 2 and self.cards[0].rank == self.cards[1].rank

    def can_double(self):
        return len(self.cards) == 2

    def is_natural_blackjack(self):
        return len(self.cards) == 2 and self.score() == 21

    @property
    def is_surrendered(self):
        return self._is_surrendered

    @is_surrendered.setter
    def is_surrendered(self, value):
        self._is_surrendered = value
