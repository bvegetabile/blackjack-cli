import typer
from typing_extensions import Annotated

from .utils import clear_terminal
from .utils import print_game_header
from .utils import print_statement_with_deco
from .utils import print_table
from .utils import print_action_menu
from .utils import print_results_table
from .gameutils.deckofcards import DeckOfCards
from .gameutils.hand import Hand
from .gameutils.player import Player

# pipx install . --force

ACTION_MAP = {
    '': 'hit', 'h': 'hit', 'hit': 'hit',
    's': 'stand', 'stand': 'stand', '1': 'stand',
    'd': 'double', 'double': 'double',
    'p': 'split', 'split': 'split',
    'q': 'quit', 'quit': 'quit',
}


def get_player_action(can_split=False, can_double=False, score=None):
    """Display action menu, read input, validate, and return canonical action."""
    while True:
        print_action_menu(can_split=can_split, can_double=can_double)
        prompt = f"Score: {score} >>> " if score is not None else ">>> "
        raw = input(prompt).strip().lower()
        action = ACTION_MAP.get(raw)

        if action is None:
            print("Invalid input. Try again.")
            continue
        if action == 'double' and not can_double:
            print("Double down is not available.")
            continue
        if action == 'split' and not can_split:
            print("Split is not available.")
            continue

        return action


class BlackjackGame:
    def __init__(self, nplayers=1, ndecks=1, init_shuffled=True):
        self.nplayers = nplayers
        self.game_state = None
        while self.game_state is None:
            self.player_list = []
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

            # Deal cards.
            for i in range(2):
                for player in self.player_list:
                    new_card = self.deck.get_card()
                    player.add_card_to_hand(new_card)

            # Show initial table.
            print_table(self.player_list, active_player_index=0)

            # Human player turn.
            human = self.player_list[0]
            quit_game = False
            hand_idx = 0
            while hand_idx < len(human.hands):
                hand = human.hands[hand_idx]
                while not hand.is_standing and not hand.is_bust():
                    can_split = hand.can_split() and len(human.hands) < 4
                    can_double = hand.can_double()

                    if len(human.hands) > 1:
                        print(f"  Playing Hand {hand_idx + 1} of {len(human.hands)}")

                    action = get_player_action(
                        can_split=can_split,
                        can_double=can_double,
                        score=hand.score(),
                    )

                    if action == 'quit':
                        quit_game = True
                        break

                    if action == 'stand':
                        hand.is_standing = True

                    elif action == 'double':
                        hand.add_card(self.deck.get_card())
                        hand.is_doubled = True
                        hand.is_standing = True
                        print_table(self.player_list, active_player_index=0)

                    elif action == 'split':
                        # Move second card to a new hand.
                        split_card = hand.cards.pop(1)
                        new_hand = Hand(cards=[split_card])
                        human.hands.insert(hand_idx + 1, new_hand)
                        # Deal one new card to each hand.
                        hand.add_card(self.deck.get_card())
                        new_hand.add_card(self.deck.get_card())
                        human.score = human.hands[0].score()
                        print_table(self.player_list, active_player_index=0)

                    else:
                        # Hit.
                        hand.add_card(self.deck.get_card())
                        human.score = human.hands[0].score()
                        print_table(self.player_list, active_player_index=0)
                        if hand.is_bust():
                            print("Bust!")

                if quit_game:
                    break
                hand_idx += 1

            if quit_game:
                break

            # Computer player actions (hit on <=16, stand on >=17).
            for player in self.player_list[1:-1]:
                while player.score_hand() <= 16:
                    new_card = self.deck.get_card()
                    player.add_card_to_hand(new_card)

            # Dealer actions.
            while self.player_list[-1].score_hand() <= 17:
                new_card = self.deck.get_card()
                self.player_list[-1].add_card_to_hand(new_card)

            # Show final table with dealer revealed.
            print_table(self.player_list, dealer_reveal=True)

            # Print results.
            print_results_table(self.player_list)

            player_next_game = input("\nPress [return] to play again. Type [q] to quit. >>> ")
            if player_next_game.strip().lower() == 'q':
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
