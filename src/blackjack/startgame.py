import typer
from typing_extensions import Annotated

from .utils import clear_terminal
from .utils import print_game_header
from .utils import print_statement_with_deco
from .gameutils.deckofcards import DeckOfCards
from .gameutils.player import Player

# pipx install . --force

STAND_INPUTS = [
    'stand',
    's',
    '1'
]


class BlackjackGame:
    def __init__(self, nplayers=1, ndecks=1, init_shuffled=True):
        self.nplayers = nplayers
        self.game_state = None
        while self.game_state is None:
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
            self.deck = DeckOfCards(ndecks=ndecks)
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
                player_action = input("Whats your move, type: '1' or 'stand', [return] for 'hit'\n>>> ")
                print(80*'.')
                self.player_list[0].last_player_action = player_action
                if player_action.lower() in STAND_INPUTS:
                    break
                new_card = self.deck.get_card()
                self.player_list[0].add_card_to_hand(new_card)
                self.player_list[0].print_hand()
                current_score = self.player_list[0].score_hand()
                if current_score > 21:
                    print("Bust.")
                    break

            # Computer player actions (hit on <=16, stand on >=17)
            for player in self.player_list[1:-1]:
                while player.score_hand() <= 16:
                    new_card = self.deck.get_card()
                    player.add_card_to_hand(new_card)
                player.print_hand()

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
        
            player_next_game = input("Press [return] to play again. Type [q] to quit.>>> ")
            if player_next_game == 'q':
                break


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

    _ = BlackjackGame(nplayers=nplayers, ndecks=ndecks)

