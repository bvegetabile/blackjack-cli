from random import shuffle
from .card import Card


class DeckOfCards:
    def __init__(self):
        SUITS = ["D", "C", "S", "H"]
        RANKS = [x for x in range(1, 14)]
        self.cards = []
        for suit in SUITS:
            for rank in RANKS:
                self.cards.append(Card(suit=suit, rank=rank))

        self.used_cards = []

    def shuffle(self):
        shuffle(self.cards)

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


if __name__ == "__main__":
    # TESTING A DECK OF CARDS
    deck = DeckOfCards()
    deck.print_cards()
    deck.shuffle()
    deck.print_cards()
    print(deck.get_card())
    print(deck.get_card())
    print(deck.get_card(from_top=False))
    deck.print_cards(unused=True)
    deck.print_cards(unused=False)
