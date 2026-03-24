import random

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
    'r': 'surrender', 'surrender': 'surrender',
}


def get_player_action(can_split=False, can_double=False, can_surrender=False, score=None):
    """Display action menu, read input, validate, and return canonical action."""
    while True:
        print_action_menu(
            can_split=can_split,
            can_double=can_double,
            can_surrender=can_surrender,
        )
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
        if action == 'surrender' and not can_surrender:
            print("Surrender is not available.")
            continue

        return action


def get_player_bet(player, minbid, default_bet=None):
    """Prompt the human player for their bet amount. Enter uses default_bet."""
    if default_bet is None:
        default_bet = minbid
    # Clamp default to what the player can afford.
    default_bet = min(default_bet, player.cash)
    default_bet = max(default_bet, minbid)

    while True:
        try:
            raw = input(f"Bet (enter=${default_bet}) >>> ").strip()
            if raw.lower() in ('q', 'quit'):
                return None
            if raw == '':
                return default_bet
            bet = int(raw)
            if bet < minbid:
                print(f"Minimum bet is ${minbid}.")
                continue
            if bet > player.cash:
                print(f"You only have ${player.cash}.")
                continue
            return bet
        except ValueError:
            print("Enter a number.")


def calculate_payout(hand, dealer_hand):
    """Calculate the payout for a hand against the dealer. Returns the net cash change."""
    if hand.is_surrendered:
        return -hand.bet / 2

    player_score = hand.score()
    dealer_score = dealer_hand.score()

    if hand.is_bust():
        return -hand.bet

    # Natural blackjack (only on non-split, non-doubled hands with 2 cards).
    if hand.is_natural_blackjack() and not hand.is_doubled:
        if dealer_hand.is_natural_blackjack():
            return 0  # Push.
        return hand.bet * 1.5  # 3:2 payout.

    if dealer_hand.is_bust():
        return hand.bet

    if player_score > dealer_score:
        return hand.bet
    elif player_score == dealer_score:
        return 0
    else:
        return -hand.bet


class BlackjackGame:
    def __init__(self, nplayers=1, ndecks=1, minbid=25, init_cash=1000, init_shuffled=True):
        self.nplayers = nplayers
        self.minbid = minbid
        self.init_cash = init_cash

        # Create players once — they persist across rounds.
        self.player_list = []
        for player_id in range(self.nplayers):
            if player_id == 0:
                self.player_list.append(
                    Player(
                        player_id=player_id + 1,
                        player_type="normal",
                        starting_cash=init_cash,
                    )
                )
            else:
                self.player_list.append(
                    Player(
                        player_id=player_id + 1,
                        player_type="computer",
                        starting_cash=init_cash,
                    )
                )
        self.dealer = Player(player_id=None, player_type="dealer")
        self.player_list.append(self.dealer)

        # Game loop.
        last_bet = None
        while True:
            human = self.player_list[0]

            # Check if human is broke.
            if human.cash < self.minbid:
                print_table(self.player_list, dealer_reveal=True)
                print(f"\nYou're out of cash! Game over.")
                break

            # Eliminate broke computer players or give them a chance to buy back in.
            active_players = [human]
            for player in self.player_list[1:-1]:
                if player.cash < self.minbid:
                    if random.random() < 0.5:
                        player.cash = self.init_cash
                        active_players.append(player)
                    # else: eliminated this round
                else:
                    active_players.append(player)
            active_players.append(self.dealer)
            self.player_list = active_players

            # Reset hands for new round.
            for player in self.player_list:
                player.reset_hands()

            # Initialize deck of cards + shuffle.
            self.deck = DeckOfCards(ndecks=ndecks)
            if init_shuffled:
                self.deck.shuffle()

            # Collect bets (last round's hands stay visible).
            bet = get_player_bet(human, self.minbid, default_bet=last_bet)
            if bet is None:
                break
            last_bet = bet
            human.hands[0].bet = bet

            # Computer bets.
            for player in self.player_list[1:-1]:
                max_bet = min(player.cash, 5 * self.minbid)
                cpu_bet = random.randint(self.minbid, max(self.minbid, max_bet))
                player.hands[0].bet = cpu_bet

            # Deal cards.
            for _ in range(2):
                for player in self.player_list:
                    new_card = self.deck.get_card()
                    player.add_card_to_hand(new_card)

            # Show initial table.
            print_table(self.player_list, active_player_index=0)

            # Insurance check: if dealer's visible card (index 1) is an ace.
            insurance_bets = {}
            dealer_visible = self.dealer.hands[0].cards[1]
            if dealer_visible.rank == 1:
                # Human insurance.
                ins_cost = human.hands[0].bet // 2
                if ins_cost > 0 and ins_cost <= human.cash:
                    ins_input = input(f"Insurance? Costs ${ins_cost} (y/n) >>> ").strip().lower()
                    if ins_input in ('y', 'yes'):
                        insurance_bets[human.player_id] = ins_cost

                # Computer insurance (random).
                for player in self.player_list[1:-1]:
                    cpu_ins = player.hands[0].bet // 2
                    if cpu_ins > 0 and cpu_ins <= player.cash and random.random() < 0.3:
                        insurance_bets[player.player_id] = cpu_ins

            # Check for dealer natural blackjack.
            if self.dealer.hands[0].is_natural_blackjack():
                print_table(self.player_list, dealer_reveal=True)
                print("Dealer has blackjack!")

                # Settle insurance.
                for player in self.player_list[:-1]:
                    ins_bet = insurance_bets.get(player.player_id, 0)
                    if ins_bet > 0:
                        player.update_cash(ins_bet * 2)  # Insurance pays 2:1.

                # Settle hands.
                for player in self.player_list[:-1]:
                    for hand in player.hands:
                        payout = calculate_payout(hand, self.dealer.hands[0])
                        player.update_cash(int(payout))

                print_results_table(self.player_list, self.dealer)
                player_next = input("\nPress [return] to play again. Type [q] to quit. >>> ")
                if player_next.strip().lower() == 'q':
                    break
                continue

            # Lose insurance bets if dealer doesn't have blackjack.
            for player in self.player_list[:-1]:
                ins_bet = insurance_bets.get(player.player_id, 0)
                if ins_bet > 0:
                    player.update_cash(-ins_bet)

            # Human player turn.
            quit_game = False
            hand_idx = 0
            first_action = True
            while hand_idx < len(human.hands):
                hand = human.hands[hand_idx]
                is_first_action_on_hand = True
                while not hand.is_standing and not hand.is_bust():
                    can_split = (
                        hand.can_split()
                        and len(human.hands) < 4
                        and human.cash >= hand.bet
                    )
                    can_double = hand.can_double() and human.cash >= hand.bet
                    can_surrender = is_first_action_on_hand and first_action and len(human.hands) == 1

                    if len(human.hands) > 1:
                        print(f"  Playing Hand {hand_idx + 1} of {len(human.hands)}")

                    action = get_player_action(
                        can_split=can_split,
                        can_double=can_double,
                        can_surrender=can_surrender,
                        score=hand.score(),
                    )
                    is_first_action_on_hand = False
                    first_action = False

                    if action == 'quit':
                        quit_game = True
                        break

                    if action == 'surrender':
                        hand.is_surrendered = True
                        hand.is_standing = True
                        print_table(self.player_list, active_player_index=0)

                    elif action == 'stand':
                        hand.is_standing = True

                    elif action == 'double':
                        hand.bet *= 2
                        hand.add_card(self.deck.get_card())
                        hand.is_doubled = True
                        hand.is_standing = True
                        human.score = human.hands[0].score()
                        print_table(self.player_list, active_player_index=0)

                    elif action == 'split':
                        split_card = hand.cards.pop(1)
                        new_hand = Hand(cards=[split_card], bet=hand.bet)
                        human.hands.insert(hand_idx + 1, new_hand)
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
            while self.dealer.score_hand() <= 17:
                new_card = self.deck.get_card()
                self.dealer.add_card_to_hand(new_card)

            # Show final table with dealer revealed.
            print_table(self.player_list, dealer_reveal=True)

            # Calculate payouts.
            for player in self.player_list[:-1]:
                for hand in player.hands:
                    payout = calculate_payout(hand, self.dealer.hands[0])
                    player.update_cash(int(payout))

            # Print results.
            print_results_table(self.player_list, self.dealer)

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

    _ = BlackjackGame(
        nplayers=nplayers,
        ndecks=ndecks,
        minbid=minbid,
        init_cash=init_cash,
    )
