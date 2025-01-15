from dataclasses import dataclass

DIAMOND_SHAPE = "\u25C6"
CLUB_SHAPE = "\u2663"
HEART_SHAPE = "\u2665"
SPADE_SHAPE = "\u2660"

SHAPE_MAPPING = {
    "D": DIAMOND_SHAPE,
    "C": CLUB_SHAPE,
    "H": HEART_SHAPE,
    "S": SPADE_SHAPE,
}

RANK_MAPPING = {
    1: "A",
    11: "J",
    12: "Q",
    13: "K"
}


@dataclass
class Card:
    suit: str
    rank: int

    def __repr__(self):
        rank_disp = RANK_MAPPING.get(self.rank, self.rank)
        suit_disp = SHAPE_MAPPING.get(self.suit, self.suit)
        return f"{rank_disp}{suit_disp}"

    def __str__(self):
        rank_disp = RANK_MAPPING.get(self.rank, self.rank)
        suit_disp = SHAPE_MAPPING.get(self.suit, self.suit)
        return f"{rank_disp}{suit_disp}"


# class DeckOfCards:
#     def __init__(self):
#         SUITS = ["D", "C", "S", "H"]
#         RANKS = [x for x in range(1, 14)]
#         self.cards = []
#         for suit in SUITS:
#             for rank in RANKS:
#                 self.cards.append(Card(suit=suit, rank=rank))

#         self.used_cards = []

#     def shuffle(self):
#         shuffle(self.cards)

#     def print_cards(self, unused=True):
#         if unused:
#             print_cards = self.cards
#         else:
#             print_cards = self.used_cards

#         for i, card in enumerate(print_cards):
#             if i == len(print_cards) - 1:
#                 print(card)
#             else:
#                 print(card, end=',')

#     def get_card(self, from_top=True):
#         if from_top:
#             card = self.cards.pop(0)
#         else:
#             card = self.cards.pop(-1)

#         self.used_cards.append(card)
#         return card


if __name__ == "__main__":
    # TESTING CARDS
    SUITS = ["D", "C", "S", "H"]
    RANKS = [x for x in range(1, 14)]
    for suit in SUITS:
        for j, rank in enumerate(RANKS):
            card = Card(suit=suit, rank=rank)
            if j == len(RANKS) - 1:
                print(card)
            else:
                print(card, end=", ")
