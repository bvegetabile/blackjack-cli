import typer
from typing_extensions import Annotated

from .utils import clear_terminal
from .utils import print_game_header
from .utils import print_statement_with_deco
from .cardutils.deckofcards import DeckOfCards

# pipx install . --force

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
    def __init__(self, player_id=None, player_type=None):
        self.player_id = player_id
        self.player_type = player_type
        self.hand = []
        self.score = None
        self.last_player_action = None

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

    def score_hand(self,):
        score_with_ace_1 = 0 
        hand_score = 0
        for card in self.hand:
            card_score = RANK_SCORES.get(card.rank, card.rank)
            hand_score += card_score
            # Handling aces.
            if card.rank == 1:
                score_with_ace_1 += 1
            else:
                score_with_ace_1 += card_score
        if hand_score > 21:
            return score_with_ace_1
        else:
            return hand_score


class BlackjackGame:
    def __init__(self, nplayers=1, init_shuffled=True):
        self.nplayers = nplayers
        self.player_list = []
        # TODO Add Player Seat Randomization.
        for player_id in range(self.nplayers):
            if player_id == 0:
                self.player_list.append(
                    Player(
                        player_id=player_id+1, 
                        player_type="normal"
                    )
                )
            else: 
                self.player_list.append(
                    Player(
                        player_id=player_id+1, 
                        player_type="computer"
                    )
                )
        self.player_list.append(
            Player(
                player_id=None,
                player_type="dealer"
                )
        )

        # Initialize deck of cards + shuffle.
        self.deck = DeckOfCards()
        if init_shuffled:
            self.deck.shuffle()

        # deal cards
        for i in range(2):
            for player in self.player_list:
                new_card = self.deck.get_card()
                player.add_card_to_hand(new_card)

        # Show table:
        for player in self.player_list:
            if player.player_id is not None: 
                hfc = False
            else:
                hfc = True
            player.print_hand(hide_first_card=hfc)

        # Start game:
        while self.player_list[0].last_player_action != 'stand':
            player_action = input("Whats the move:")
            self.player_list[0].last_player_action = player_action
            if player_action == 'stand':
                break
            new_card = self.deck.get_card()
            self.player_list[0].add_card_to_hand(new_card)
            self.player_list[0].print_hand()
            current_score = self.player_list[0].score_hand()
            if current_score > 21:
                print("Bust.")
                break

        # Dealer actions 
        while self.player_list[-1].score_hand() <= 17:
            new_card = self.deck.get_card()
            self.player_list[-1].add_card_to_hand(new_card)
            self.player_list[-1].print_hand(hide_first_card=False)
            current_score = self.player_list[-1].score_hand()
            if current_score > 21:
                print("Bust.")
                break

        self.player_list[-1].print_hand(hide_first_card=False)

        # Print results. 
        print(80*'-')
        dealer_score = self.player_list[-1].score_hand()
        for player in self.player_list[:-1]:
            player_score = player.score_hand()
            score_results = f"| Hand Score {player_score}, Dealer Hand {dealer_score}."
            if player_score > dealer_score and player_score <= 21 and dealer_score <= 21:
                print(f"Player {player.player_id}: Wins. {score_results}")
            elif player_score <= 21 and dealer_score > 21:
                print(f"Player {player.player_id}: Wins. {score_results}")
            elif player_score == dealer_score and player_score <= 21: 
                print(f"Player {player.player_id}: Pushes. {score_results}")
            else:
                print(f"Player {player.player_id}: Loses. {score_results}")
        print(80*'-')



def startgame(
    nplayers: Annotated[
        int, typer.Option(help="The number of players (including you)")
    ] = 1,
    ndecks: Annotated[int, typer.Option(help="The number of decks")] = 1,
    minbid: Annotated[int, typer.Option(help="Casino table minimum bid")] = 25,
    init_cash: Annotated[int, typer.Option(help="Players initial wallet size.")] = 1000,
):
    # Clean inputs.
    if ndecks > 1:
        decks_plural = "s"
    else:
        decks_plural = ""

    # Initialize game.
    clear_terminal()

    print_game_header()

    print_statement_with_deco(
        f"You've chosen {nplayers} computer opponents",
        before=True,
        after=True,
        symbol="-",
    )

    print_statement_with_deco(
        statement=f"Playing the game with {ndecks} deck{decks_plural}.",
        after=True,
        symbol="-",
    )

    _ = BlackjackGame(nplayers=nplayers)


