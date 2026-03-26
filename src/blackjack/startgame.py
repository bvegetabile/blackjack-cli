import json
import random

import typer
from typing_extensions import Annotated

from .utils import clear_terminal
from .utils import print_game_header
from .utils import print_statement_with_deco
from .utils import print_table
from .utils import print_action_menu
from .utils import print_results_table
from .utils import print_player_stats
from .utils import print_game_over
from .utils import print_bust_message
from .utils import prompt_play_again
from .utils import print_blackjack_banner
from .utils import animate_dealer_reveal
from .gameutils.deckofcards import DeckOfCards
from .gameutils.hand import Hand
from .gameutils.player import Player

ACTION_MAP = {
    '': 'hit', 'h': 'hit', 'hit': 'hit',
    's': 'stand', 'stand': 'stand', '1': 'stand',
    'd': 'double', 'double': 'double',
    'p': 'split', 'split': 'split',
    'q': 'quit', 'quit': 'quit',
    'r': 'surrender', 'surrender': 'surrender',
    '?': 'hint', 'hint': 'hint',
}


def get_player_action(can_split=False, can_double=False, can_surrender=False, score=None, dealer_upcard_str=None):
    """Display action menu, read input, validate, and return canonical action."""
    while True:
        print_action_menu(
            can_split=can_split,
            can_double=can_double,
            can_surrender=can_surrender,
            dealer_upcard_str=dealer_upcard_str,
            player_score=score,
        )
        prompt = ">>> "
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

        return action  # includes 'hint' — caller handles it by looping back


def get_player_bet(player, minbid, default_bet=None, round_num=None):
    """Prompt the human player for their bet amount. Enter uses default_bet."""
    if default_bet is None:
        default_bet = minbid
    # Clamp default to what the player can afford.
    default_bet = min(default_bet, player.cash)
    default_bet = max(default_bet, minbid)

    from .utils import MENU_WIDTH
    if round_num is not None:
        print("\u2500" * MENU_WIDTH)
        print(f"  Round {round_num}  |  Cash: ${player.cash}")

    while True:
        try:
            raw = input(f"  Bet (enter=${default_bet}) >>> ").strip()
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
    if hand.is_even_money:
        return 0  # Already paid 1:1 at offer time.
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


def get_basic_strategy_hint(hand, dealer_upcard_rank, can_split, can_double):
    """Return the basic strategy recommendation as (action, reason)."""
    score = hand.score()
    # Check if we actually have a soft hand (an ace counted as 11)
    hard_total = sum(c.rank if c.rank <= 10 else 10 for c in hand.cards)
    ace_count = sum(1 for c in hand.cards if c.rank == 1)
    is_soft = ace_count > 0 and hard_total + 10 <= 21 and len(hand.cards) == 2

    dealer = dealer_upcard_rank
    if dealer >= 11:
        dealer = 10  # Face cards
    if dealer == 1:
        dealer = 11  # Ace

    # Pair splitting
    if can_split:
        pair_rank = hand.cards[0].rank
        if pair_rank == 1:
            return "SPLIT", "splitting aces gives two chances to hit 21"
        if pair_rank == 8:
            return "SPLIT", "16 is the worst hand; two separate 8s are far better"
        if pair_rank in (2, 3, 7) and dealer <= 7:
            return "SPLIT", "dealer is weak and likely to bust — split to win two bets"
        if pair_rank == 4 and dealer in (5, 6):
            return "SPLIT", "dealer is in their weakest range — split to maximize"
        if pair_rank == 6 and dealer <= 6:
            return "SPLIT", "dealer is likely to bust; split to put more money out"
        if pair_rank == 9 and dealer not in (7, 10, 11):
            return "SPLIT", "dealer is vulnerable; two 9s beat one 18"

    # Soft totals
    if is_soft:
        if score >= 19:
            return "STAND", "soft 19+ wins most hands; the risk of hitting outweighs any gain"
        if score == 18:
            if can_double and dealer in (3, 4, 5, 6):
                return "DOUBLE", "dealer is weak — get more money in on a strong hand"
            if dealer >= 9:
                return "HIT", "dealer's strong upcard makes 18 insufficient to win"
            return "STAND", "18 wins or pushes most of the time here"
        if score == 17 and can_double and dealer in (3, 4, 5, 6):
            return "DOUBLE", "dealer is weak; with an ace you can only improve"
        if score in (15, 16) and can_double and dealer in (4, 5, 6):
            return "DOUBLE", "dealer is likely to bust; an ace keeps you from busting on the double"
        if score in (13, 14) and can_double and dealer in (5, 6):
            return "DOUBLE", "dealer is at peak bust risk; you can't bust with an ace in hand"
        return "HIT", "you can't bust with an ace counted as 11 — always safe to improve"

    # Hard totals
    if score >= 17:
        return "STAND", "busting is too likely; let the dealer take the risk"
    if score >= 13 and dealer <= 6:
        return "STAND", "dealer must hit their weak hand and is likely to bust"
    if score == 12 and dealer in (4, 5, 6):
        return "STAND", "dealer's bust range — don't risk busting yourself"
    if score == 11:
        if can_double:
            return "DOUBLE", "11 is the best doubling hand — any 10-value card gives you 21"
        return "HIT", "11 is your strongest position; draw aggressively"
    if score == 10 and dealer <= 9:
        if can_double:
            return "DOUBLE", "10 vs a weak dealer is a prime doubling spot"
        return "HIT", "10 is strong against a weak dealer; draw aggressively"
    if score == 9 and dealer in (3, 4, 5, 6):
        if can_double:
            return "DOUBLE", "dealer is weak — put more money out on your 9"
        return "HIT", "dealer is weak; draw to improve before they bust"
    return "HIT", "your total is too low to stand — you must improve"


class BlackjackGame:
    def __init__(self, nplayers=1, ndecks=1, minbid=25, init_cash=1000, init_shuffled=True,
                 show_hints=False, show_history=False, animation_delay=0.4,
                 db=None, session_id=None, resume_data=None):
        self.nplayers = nplayers
        self.ndecks = ndecks
        self.minbid = minbid
        self.init_cash = init_cash
        self.show_hints = show_hints
        self.show_history = show_history
        self.animation_delay = animation_delay
        self.hand_history = []
        self.db = db
        self.session_id = session_id

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

        # Create shoe (persists across rounds).
        self.deck = DeckOfCards(ndecks=ndecks)
        if init_shuffled:
            self.deck.shuffle()

        # Resume from checkpoint if provided.
        last_bet = None
        round_num = 0
        if resume_data:
            from .storage import restore_shoe, restore_players
            round_num = resume_data.get("round_num", 0)
            last_bet = resume_data.get("last_bet")
            if resume_data.get("shoe_state"):
                restore_shoe(self.deck, resume_data["shoe_state"])
            if resume_data.get("player_states"):
                restore_players(self.player_list, resume_data["player_states"])

        # Game loop.
        reshuffled_this_round = False
        round_id = None
        while True:
            round_num += 1
            human = self.player_list[0]

            # Check if human is broke.
            if human.cash < self.minbid:
                print_table(self.player_list, dealer_reveal=True, round_num=round_num)
                print_game_over(human, round_num - 1)
                if self.show_history and self.hand_history:
                    self._print_history()
                restart = input("\nPlay again with fresh cash? (y/n) >>> ").strip().lower()
                if restart in ('y', 'yes'):
                    human.cash = self.init_cash
                    human.prev_cash = self.init_cash
                    human.stats = {
                        "wins": 0, "losses": 0, "pushes": 0,
                        "blackjacks": 0, "busts": 0, "surrenders": 0,
                        "peak_cash": self.init_cash, "streak": 0,
                    }
                    round_num = 0
                    last_bet = None
                    continue
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

            # Reshuffle shoe if penetration is high.
            reshuffled_this_round = False
            if self.deck.needs_reshuffle():
                print("  Reshuffling the shoe...")
                self.deck.reshuffle()
                reshuffled_this_round = True

            # Start round in DB.
            if self.db and self.session_id:
                round_id = self.db.start_round(self.session_id, round_num)
                if reshuffled_this_round:
                    self.db.log_event(self.session_id, round_id, 'RESHUFFLE',
                                      cards_remaining=self.deck.cards_remaining())

            # Collect bets (last round's hands stay visible).
            bet = get_player_bet(human, self.minbid, default_bet=last_bet, round_num=round_num)
            if bet is None:
                if self.db and self.session_id:
                    self.db.complete_session(self.session_id)
                break
            last_bet = bet
            human.hands[0].bet = bet

            # Computer bets.
            for player in self.player_list[1:-1]:
                max_bet = min(player.cash, 5 * self.minbid)
                cpu_bet = random.randint(self.minbid, max(self.minbid, max_bet))
                player.hands[0].bet = cpu_bet

            # Deal cards and log each deal.
            for _ in range(2):
                for seat, player in enumerate(self.player_list):
                    new_card = self.deck.get_card()
                    player.add_card_to_hand(new_card)
                    if self.db and self.session_id and round_id:
                        self.db.log_event(
                            self.session_id, round_id, 'DEAL',
                            player_id=player.player_id,
                            player_type=player.player_type,
                            seat_position=seat if player.player_type != 'dealer' else None,
                            card_suit=new_card.suit,
                            card_rank=new_card.rank,
                            ndecks=self.ndecks,
                            cards_remaining=self.deck.cards_remaining(),
                        )

            # Show initial table.
            print_table(self.player_list, active_player_index=0, round_num=round_num, stats_player=human)

            # Announce natural blackjacks.
            for player in self.player_list[:-1]:
                if player.hands[0].is_natural_blackjack():
                    name = f"Player {player.player_id}" if player.player_type == "normal" else f"Computer {player.player_id}"
                    print_blackjack_banner(name)

            # Insurance / even money check: if dealer's visible card (index 1) is an ace.
            insurance_bets = {}
            dealer_visible = self.dealer.hands[0].cards[1]
            dealer_upcard = dealer_visible
            if dealer_visible.rank == 1:
                # Even money: offer to human player if they have a natural blackjack.
                human_hand = human.hands[0]
                even_money_taken = False
                if human_hand.is_natural_blackjack():
                    em_input = input(
                        f"  Dealer shows Ace — you have Blackjack!\n"
                        f"  [E] Even Money (take +${human_hand.bet} guaranteed now)  [N] Decline >>> "
                    ).strip().lower()
                    em_action = 'yes' if em_input in ('e', 'even', 'even money') else 'no'
                    if self.db and self.session_id and round_id:
                        self.db.log_event(
                            self.session_id, round_id, 'EVEN_MONEY',
                            player_id=human.player_id, player_type='normal', seat_position=0,
                            action=em_action, bet=human_hand.bet, player_cash=human.cash,
                            dealer_upcard_rank=dealer_upcard.rank,
                            dealer_upcard_suit=dealer_upcard.suit,
                            ndecks=self.ndecks,
                            cards_remaining=self.deck.cards_remaining(),
                        )
                    if em_action == 'yes':
                        human.update_cash(human_hand.bet)
                        human_hand.is_even_money = True
                        human_hand.is_standing = True  # Hand resolved immediately.
                        even_money_taken = True

                if not even_money_taken:
                    # Regular insurance offer for human.
                    ins_cost = human_hand.bet // 2
                    if ins_cost > 0 and ins_cost <= human.cash:
                        ins_input = input(f"Insurance? Costs ${ins_cost} (y/n) >>> ").strip().lower()
                        ins_action = 'yes' if ins_input in ('y', 'yes') else 'no'
                        if self.db and self.session_id and round_id:
                            self.db.log_event(
                                self.session_id, round_id, 'INSURANCE',
                                player_id=human.player_id, player_type='normal', seat_position=0,
                                action=ins_action, bet=ins_cost, player_cash=human.cash,
                                dealer_upcard_rank=dealer_upcard.rank,
                                dealer_upcard_suit=dealer_upcard.suit,
                                ndecks=self.ndecks,
                                cards_remaining=self.deck.cards_remaining(),
                            )
                        if ins_action == 'yes':
                            insurance_bets[human.player_id] = ins_cost

                # Computer insurance (random).
                for player in self.player_list[1:-1]:
                    cpu_ins = player.hands[0].bet // 2
                    if cpu_ins > 0 and cpu_ins <= player.cash and random.random() < 0.3:
                        insurance_bets[player.player_id] = cpu_ins

            # Check for dealer natural blackjack.
            if self.dealer.hands[0].is_natural_blackjack():
                print_table(self.player_list, dealer_reveal=True, round_num=round_num)
                print("Dealer has blackjack!")

                # Settle insurance.
                for player in self.player_list[:-1]:
                    ins_bet = insurance_bets.get(player.player_id, 0)
                    if ins_bet > 0:
                        player.update_cash(ins_bet * 2)  # Insurance pays 2:1.

                # Settle hands and log payouts.
                for seat, player in enumerate(self.player_list[:-1]):
                    for hand_idx, hand in enumerate(player.hands):
                        payout = calculate_payout(hand, self.dealer.hands[0])
                        player.update_cash(int(payout))
                        if self.db and self.session_id and round_id:
                            from .utils import determine_outcome
                            outcome = determine_outcome(hand, self.dealer.hands[0])
                            self.db.log_event(
                                self.session_id, round_id, 'PAYOUT',
                                player_id=player.player_id, player_type=player.player_type,
                                seat_position=seat, hand_index=hand_idx,
                                outcome=outcome, payout=int(payout), cash_after=player.cash,
                                ndecks=self.ndecks,
                                cards_remaining=self.deck.cards_remaining(),
                            )

                self._checkpoint_round(round_id, round_num, last_bet, reshuffled_this_round)
                print_results_table(self.player_list, self.dealer)
                print_player_stats(human)
                player_next = prompt_play_again()
                if player_next.strip().lower() == 'q':
                    if self.db and self.session_id:
                        self.db.complete_session(self.session_id)
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

                    # Show basic strategy hint.
                    if self.show_hints:
                        dealer_upcard = self.dealer.hands[0].cards[1]
                        hint, reason = get_basic_strategy_hint(
                            hand, dealer_upcard.rank, can_split, can_double
                        )
                        print(f"  Hint: {hint} — {reason}")

                    dealer_upcard = self.dealer.hands[0].cards[1]
                    upcard_rank = dealer_upcard.rank if dealer_upcard.rank <= 10 else 10
                    upcard_str = f"{dealer_upcard} ({upcard_rank})"
                    action = get_player_action(
                        can_split=can_split,
                        can_double=can_double,
                        can_surrender=can_surrender,
                        score=hand.score(),
                        dealer_upcard_str=upcard_str,
                    )

                    # On-demand hint — show strategy and loop back without consuming the action.
                    if action == 'hint':
                        hint, reason = get_basic_strategy_hint(
                            hand, dealer_upcard.rank, can_split, can_double
                        )
                        print(f"\n  Strategy: {hint} — {reason}\n")
                        continue

                    is_first_action_on_hand = False
                    first_action = False

                    if action == 'quit':
                        quit_game = True
                        break

                    # Log the player action before applying it.
                    if self.db and self.session_id and round_id:
                        from .storage import burned_counts, snapshot_visible_cards
                        hard_total = sum(c.rank if c.rank <= 10 else 10 for c in hand.cards)
                        ace_count = sum(1 for c in hand.cards if c.rank == 1)
                        is_soft = ace_count > 0 and hard_total + 10 <= 21 and len(hand.cards) == 2
                        self.db.log_event(
                            self.session_id, round_id, 'PLAYER_ACTION',
                            player_id=human.player_id, player_type='normal', seat_position=0,
                            hand_index=hand_idx,
                            action=action,
                            player_cards=json.dumps([{"suit": c.suit, "rank": c.rank} for c in hand.cards]),
                            player_hand_value=hand.score(),
                            player_is_soft=int(is_soft),
                            player_cash=human.cash,
                            bet=hand.bet,
                            can_hit=1,
                            can_stand=1,
                            can_double=int(can_double),
                            can_split=int(can_split),
                            can_surrender=int(can_surrender),
                            dealer_upcard_rank=dealer_upcard.rank,
                            dealer_upcard_suit=dealer_upcard.suit,
                            ndecks=self.ndecks,
                            visible_cards=json.dumps(snapshot_visible_cards(self.player_list)),
                            burned_counts=json.dumps(burned_counts(self.deck)),
                            cards_remaining=self.deck.cards_remaining(),
                        )

                    if action == 'surrender':
                        hand.is_surrendered = True
                        hand.is_standing = True
                        print_table(self.player_list, active_player_index=0, round_num=round_num, stats_player=human)

                    elif action == 'stand':
                        hand.is_standing = True

                    elif action == 'double':
                        human.update_cash(-hand.bet)  # Deduct additional bet.
                        hand.bet *= 2
                        hand.add_card(self.deck.get_card())
                        hand.is_doubled = True
                        hand.is_standing = True
                        human.score = human.hands[0].score()
                        print_table(self.player_list, active_player_index=0, round_num=round_num, stats_player=human)

                    elif action == 'split':
                        human.update_cash(-hand.bet)  # Deduct bet for new hand.
                        splitting_aces = hand.cards[0].rank == 1
                        split_card = hand.cards.pop(1)
                        new_hand = Hand(cards=[split_card], bet=hand.bet)
                        human.hands.insert(hand_idx + 1, new_hand)
                        hand.add_card(self.deck.get_card())
                        new_hand.add_card(self.deck.get_card())
                        # Split aces: one card each, auto-stand.
                        if splitting_aces:
                            hand.is_split_ace = True
                            new_hand.is_split_ace = True
                            hand.is_standing = True
                            new_hand.is_standing = True
                        human.score = human.hands[0].score()
                        print_table(self.player_list, active_player_index=0, round_num=round_num, stats_player=human)

                    else:
                        # Hit.
                        hand.add_card(self.deck.get_card())
                        human.score = human.hands[0].score()
                        print_table(self.player_list, active_player_index=0, round_num=round_num, stats_player=human)
                        if hand.is_bust():
                            print_bust_message()

                if quit_game:
                    break
                hand_idx += 1

            if quit_game:
                if self.db and self.session_id:
                    self.db.complete_session(self.session_id)
                break

            # Computer player actions (hit on <=16, stand on >=17).
            for seat, player in enumerate(self.player_list[1:-1], start=1):
                while player.score_hand() <= 16:
                    new_card = self.deck.get_card()
                    player.add_card_to_hand(new_card)
                    if self.db and self.session_id and round_id:
                        self.db.log_event(
                            self.session_id, round_id, 'PLAYER_ACTION',
                            player_id=player.player_id, player_type='computer',
                            seat_position=seat,
                            action='hit',
                            player_hand_value=player.score_hand(),
                            card_suit=new_card.suit, card_rank=new_card.rank,
                            ndecks=self.ndecks,
                            cards_remaining=self.deck.cards_remaining(),
                        )

            # Dealer actions (S17: stand on all 17s).
            while self.dealer.score_hand() < 17:
                new_card = self.deck.get_card()
                self.dealer.add_card_to_hand(new_card)
                if self.db and self.session_id and round_id:
                    self.db.log_event(
                        self.session_id, round_id, 'DEALER_HIT',
                        card_suit=new_card.suit, card_rank=new_card.rank,
                        ndecks=self.ndecks,
                        cards_remaining=self.deck.cards_remaining(),
                    )

            # Animate dealer hole card reveal.
            animate_dealer_reveal(self.player_list, round_num, self.animation_delay)

            # Calculate payouts and record history.
            for seat, player in enumerate(self.player_list[:-1]):
                for hi, hand in enumerate(player.hands):
                    payout = calculate_payout(hand, self.dealer.hands[0])
                    player.update_cash(int(payout))

                    if player == human:
                        from .utils import determine_outcome
                        outcome = determine_outcome(hand, self.dealer.hands[0])
                        self.hand_history.append({
                            "round": round_num,
                            "player_cards": [str(c) for c in hand.cards],
                            "dealer_cards": [str(c) for c in self.dealer.hands[0].cards],
                            "player_score": hand.score(),
                            "dealer_score": self.dealer.score_hand(),
                            "bet": hand.bet,
                            "outcome": outcome,
                            "payout": int(payout),
                            "cash": human.cash,
                        })

                    if self.db and self.session_id and round_id:
                        from .utils import determine_outcome
                        outcome = determine_outcome(hand, self.dealer.hands[0])
                        self.db.log_event(
                            self.session_id, round_id, 'PAYOUT',
                            player_id=player.player_id, player_type=player.player_type,
                            seat_position=seat, hand_index=hi,
                            outcome=outcome, payout=int(payout), cash_after=player.cash,
                            ndecks=self.ndecks,
                            cards_remaining=self.deck.cards_remaining(),
                        )

            self._checkpoint_round(round_id, round_num, last_bet, reshuffled_this_round)

            # Print results and stats.
            print_results_table(self.player_list, self.dealer)
            print_player_stats(human)

            player_next_game = prompt_play_again()
            if player_next_game.strip().lower() == 'q':
                if self.db and self.session_id:
                    self.db.complete_session(self.session_id)
                if self.show_history and self.hand_history:
                    self._print_history()
                break


    def _checkpoint_round(self, round_id, round_num, last_bet, reshuffled):
        """Save session checkpoint and complete the round row in the DB."""
        if not self.db or not self.session_id:
            return
        from .storage import serialize_shoe, serialize_players
        dealer_cards = json.dumps([{"suit": c.suit, "rank": c.rank}
                                   for c in self.dealer.hands[0].cards])
        self.db.complete_round(
            round_id,
            dealer_cards=dealer_cards,
            dealer_score=self.dealer.score_hand(),
            reshuffled=reshuffled,
        )
        self.db.update_session_state(
            self.session_id,
            round_num=round_num,
            last_bet=last_bet,
            shoe_state=serialize_shoe(self.deck),
            player_states=serialize_players(self.player_list),
        )

    def _print_history(self):
        """Print hand history log."""
        print("\n" + "=" * 70)
        print("HAND HISTORY")
        print("=" * 70)
        print(f"  {'Rd':>3}  {'Your Hand':<20} {'Dealer':<20} {'Bet':>5}  {'Result':<10} {'Payout':>7}  {'Cash':>6}")
        print("-" * 70)
        for h in self.hand_history:
            cards = ", ".join(h["player_cards"])
            dcards = ", ".join(h["dealer_cards"])
            payout = h["payout"]
            payout_str = f"+${payout}" if payout > 0 else f"-${abs(payout)}" if payout < 0 else "$0"
            print(
                f"  {h['round']:>3}  {cards:<20} {dcards:<20} ${h['bet']:>4}  "
                f"{h['outcome']:<10} {payout_str:>7}  ${h['cash']:>5}"
            )
        print("=" * 70)


def _resolve_player(db, player_name_arg):
    """Verify or select the active player. Returns (username, user_id).

    If player_name_arg is given, skip confirmation and use it directly.
    Otherwise default to OS username but let the user confirm or switch.
    """
    import getpass
    from .utils import CYAN, RESET

    if player_name_arg:
        username = player_name_arg
        user_id = db.get_or_create_user(username)
        return username, user_id

    candidate = getpass.getuser()
    print(f"\n  Playing as: {CYAN}{candidate}{RESET}")
    confirm = input("  [Y] That's me   [N] Switch player >>> ").strip().lower()

    if confirm not in ('n', 'no'):
        user_id = db.get_or_create_user(candidate)
        return candidate, user_id

    # Switch player menu.
    users = db.list_users()
    if users:
        print("\n  Known players:")
        for i, u in enumerate(users, 1):
            print(f"    [{i}] {u['username']}")
    print("    [N] New player name")
    choice = input("\n  >>> ").strip()

    try:
        idx = int(choice) - 1
        username = users[idx]["username"]
    except (ValueError, IndexError):
        if choice.lower() == 'n' or choice == '':
            username = input("  Enter new player name >>> ").strip() or candidate
        else:
            username = choice or candidate

    user_id = db.get_or_create_user(username)
    return username, user_id


def _show_resume_menu(db, user_id, username):
    """Display active sessions and return (session_id, resume_data) or (None, None)."""
    from .utils import CYAN, RESET
    active = db.get_active_sessions(user_id)
    if not active:
        return None, None

    print(f"\n  Welcome back, {CYAN}{username}{RESET} — active sessions:")
    for i, s in enumerate(active, 1):
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(s["started_at"]).strftime("%b %d")
        except Exception:
            dt = "?"
        cash_str = f"${s['cash']}" if s.get("cash") is not None else "?"
        print(f"    [{i}] Started {dt}  |  Round {s['round_num']}  |  Cash {cash_str}")
    print("    [N] Start new session")

    choice = input("\n  >>> ").strip().lower()
    try:
        idx = int(choice) - 1
        selected = active[idx]
        resume_data = db.load_session(selected["session_id"])
        return selected["session_id"], resume_data
    except (ValueError, IndexError):
        return None, None


def startgame(
    nplayers: Annotated[
        int, typer.Option(help="The number of players (including you)")
    ] = 1,
    ndecks: Annotated[int, typer.Option(help="The number of decks")] = 1,
    minbid: Annotated[int, typer.Option(help="Casino table minimum bid")] = 25,
    init_cash: Annotated[int, typer.Option(help="Players initial wallet size.")] = 1000,
    hints: Annotated[bool, typer.Option(help="Show basic strategy hints")] = False,
    history: Annotated[bool, typer.Option(help="Show hand history at game over")] = False,
    animation_delay: Annotated[float, typer.Option(help="Seconds per row in dealer reveal animation (0 = instant)")] = 0.4,
    anonymous: Annotated[bool, typer.Option("--anonymous", help="Skip session storage — no history or resume")] = False,
    player_name: Annotated[str, typer.Option(help="Your player name (default: OS username)")] = None,
):
    decks_plural = "s" if ndecks > 1 else ""

    # Set up DB and resolve user unless running anonymously.
    db = None
    session_id = None
    resume_data = None

    if not anonymous:
        from .storage import GameDatabase, DEFAULT_DB_PATH
        db = GameDatabase(str(DEFAULT_DB_PATH))
        username, user_id = _resolve_player(db, player_name)
        session_id, resume_data = _show_resume_menu(db, user_id, username)

        if resume_data:
            # Restore game config from the saved session.
            nplayers = resume_data.get("nplayers", nplayers)
            ndecks = resume_data.get("ndecks", ndecks)
            minbid = resume_data.get("minbid", minbid)
            init_cash = resume_data.get("init_cash", init_cash)
        else:
            config = {
                "nplayers": nplayers, "ndecks": ndecks,
                "minbid": minbid, "init_cash": init_cash,
                "animation_delay": animation_delay,
            }
            session_id = db.create_session(user_id, config)

    # Initialize game display.
    clear_terminal()
    print_game_header()

    from .utils import HEADER_WIDTH
    print_statement_with_deco(
        f"  You've chosen {nplayers - 1} computer opponent{'s' if nplayers - 1 != 1 else ''}",
        before=True,
        after=True,
        n_symbols=HEADER_WIDTH,
        symbol="\u2500",
    )

    print_statement_with_deco(
        statement=f"  Playing the game with {ndecks} deck{decks_plural}.",
        after=True,
        n_symbols=HEADER_WIDTH,
        symbol="\u2500",
    )

    _ = BlackjackGame(
        nplayers=nplayers,
        ndecks=ndecks,
        minbid=minbid,
        init_cash=init_cash,
        show_hints=hints,
        show_history=history,
        animation_delay=animation_delay,
        db=db,
        session_id=session_id,
        resume_data=resume_data,
    )
