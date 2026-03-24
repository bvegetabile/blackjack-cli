from random import shuffle
from .card import Card


class DeckOfCards:
    def __init__(self, ndecks=1):
        SUITS = ["D", "C", "S", "H"]
        RANKS = [x for x in range(1, 14)]
        self.cards = []
        for _ in range(ndecks):
            for suit in SUITS:
                for rank in RANKS:
                    self.cards.append(Card(suit=suit, rank=rank))

        self.used_cards = []
        self.total_cards = len(self.cards)

    def shuffle(self):
        shuffle(self.cards)

    def reshuffle(self):
        """Return all used cards to the deck and shuffle."""
        self.cards.extend(self.used_cards)
        self.used_cards = []
        self.shuffle()

    def cards_remaining(self):
        return len(self.cards)

    def needs_reshuffle(self, threshold=0.25):
        """Returns True if remaining cards are below the threshold percentage."""
        return len(self.cards) < self.total_cards * threshold

    def print_cards(self, unused=True):
        if unused:
            print_cards = self.cards
        else:
            print_cards = self.used_cards

        for i, card in enumerate(print_cards):
            if i == len(print_cards) - 1:
                print(card)
            else:
                print(card, end=',')

    def get_card(self, from_top=True):
        if from_top:
            card = self.cards.pop(0)
        else:
            card = self.cards.pop(-1)

        self.used_cards.append(card)
        return card
