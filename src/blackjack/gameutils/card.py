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
