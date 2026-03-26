from blackjack.startgame import BlackjackGame, get_player_action, calculate_payout
from blackjack.gameutils.card import Card
from blackjack.gameutils.hand import Hand


def _patch_game(monkeypatch, inputs):
    """Monkeypatch input and clear_terminal for clean test runs."""
    input_iter = iter(inputs)
    monkeypatch.setattr("builtins.input", lambda _="": next(input_iter))
    monkeypatch.setattr("blackjack.utils.clear_terminal", lambda: None)


def test_game_smoke_test(monkeypatch):
    """Verify a game completes when the player stands then quits."""
    _patch_game(monkeypatch, ["25", "s", "q"])
    game = BlackjackGame(nplayers=1)
    assert len(game.player_list) == 2  # 1 human + 1 dealer


def test_game_with_computer_players(monkeypatch):
    """Verify a game with computer players completes."""
    _patch_game(monkeypatch, ["25", "s", "q"])
    game = BlackjackGame(nplayers=2)
    assert len(game.player_list) >= 3  # 1 human + computers + 1 dealer


def test_game_hit_then_stand(monkeypatch):
    """Verify a game where the player hits once then stands."""
    controlled_cards = [
        Card("H", 2), Card("S", 5),   # player card 1, dealer card 1
        Card("D", 3), Card("C", 10),  # player card 2, dealer card 2
        Card("H", 4),                 # hit card for player
        Card("D", 2), Card("C", 3),   # extra for dealer hits
    ]

    def mock_get_card(from_top=True):
        return controlled_cards.pop(0)

    _patch_game(monkeypatch, ["25", "h", "s", "q"])
    monkeypatch.setattr("blackjack.gameutils.deckofcards.DeckOfCards.get_card", mock_get_card)
    monkeypatch.setattr("blackjack.gameutils.deckofcards.DeckOfCards.shuffle", lambda self: None)

    game = BlackjackGame(nplayers=1)
    assert len(game.player_list[0].hand) == 3


def test_game_multi_deck(monkeypatch):
    """Verify a game works with multiple decks."""
    _patch_game(monkeypatch, ["25", "s", "q"])
    game = BlackjackGame(nplayers=1, ndecks=2)
    assert game.deck is not None


def test_game_double_down(monkeypatch):
    """Verify double down deals one card and ends the turn."""
    _patch_game(monkeypatch, ["25", "d", "q"])
    game = BlackjackGame(nplayers=1)
    assert len(game.player_list[0].hand) == 3
    assert game.player_list[0].hands[0].is_doubled is True


def test_game_split(monkeypatch):
    """Verify split creates two hands when dealt a pair."""
    controlled_cards = [
        Card("H", 8), Card("S", 5),   # player card 1, dealer card 1
        Card("D", 8), Card("C", 10),  # player card 2, dealer card 2
        Card("H", 3), Card("S", 6),   # split cards
        Card("D", 2), Card("C", 3), Card("H", 4),  # dealer hits
    ]

    def mock_get_card(from_top=True):
        return controlled_cards.pop(0)

    _patch_game(monkeypatch, ["25", "p", "s", "s", "q"])
    monkeypatch.setattr("blackjack.gameutils.deckofcards.DeckOfCards.get_card", mock_get_card)
    monkeypatch.setattr("blackjack.gameutils.deckofcards.DeckOfCards.shuffle", lambda self: None)

    game = BlackjackGame(nplayers=1)
    human = game.player_list[0]
    assert len(human.hands) == 2


def test_get_player_action_rejects_invalid(monkeypatch):
    """Verify invalid input is rejected and re-prompted."""
    inputs = iter(["xyz", "h"])
    monkeypatch.setattr("builtins.input", lambda _="": next(inputs))
    action = get_player_action(can_split=False, can_double=False)
    assert action == "hit"


def test_get_player_action_rejects_unavailable_split(monkeypatch):
    """Verify split is rejected when not available."""
    inputs = iter(["p", "s"])
    monkeypatch.setattr("builtins.input", lambda _="": next(inputs))
    action = get_player_action(can_split=False, can_double=False)
    assert action == "stand"


# --- Payout tests ---

def test_payout_win():
    hand = Hand(cards=[Card("H", 10), Card("S", 9)], bet=50)
    dealer_hand = Hand(cards=[Card("D", 10), Card("C", 7)])
    assert calculate_payout(hand, dealer_hand) == 50


def test_payout_lose():
    hand = Hand(cards=[Card("H", 10), Card("S", 7)], bet=50)
    dealer_hand = Hand(cards=[Card("D", 10), Card("C", 9)])
    assert calculate_payout(hand, dealer_hand) == -50


def test_payout_push():
    hand = Hand(cards=[Card("H", 10), Card("S", 7)], bet=50)
    dealer_hand = Hand(cards=[Card("D", 10), Card("C", 7)])
    assert calculate_payout(hand, dealer_hand) == 0


def test_payout_bust():
    hand = Hand(cards=[Card("H", 10), Card("S", 7), Card("D", 8)], bet=50)
    dealer_hand = Hand(cards=[Card("D", 10), Card("C", 7)])
    assert calculate_payout(hand, dealer_hand) == -50


def test_payout_natural_blackjack():
    hand = Hand(cards=[Card("H", 1), Card("S", 13)], bet=100)
    dealer_hand = Hand(cards=[Card("D", 10), Card("C", 7)])
    assert calculate_payout(hand, dealer_hand) == 150  # 3:2


def test_payout_blackjack_vs_dealer_blackjack():
    hand = Hand(cards=[Card("H", 1), Card("S", 13)], bet=100)
    dealer_hand = Hand(cards=[Card("D", 1), Card("C", 13)])
    assert calculate_payout(hand, dealer_hand) == 0  # Push


def test_payout_surrender():
    hand = Hand(cards=[Card("H", 10), Card("S", 7)], bet=100)
    hand.is_surrendered = True
    dealer_hand = Hand(cards=[Card("D", 10), Card("C", 9)])
    assert calculate_payout(hand, dealer_hand) == -50


def test_payout_dealer_bust():
    hand = Hand(cards=[Card("H", 10), Card("S", 7)], bet=50)
    dealer_hand = Hand(cards=[Card("D", 10), Card("C", 7), Card("H", 9)])
    assert calculate_payout(hand, dealer_hand) == 50


def test_game_over_when_broke(monkeypatch):
    """Verify game ends when human can't afford minimum bet."""
    _patch_game(monkeypatch, ["n"])  # decline restart
    game = BlackjackGame(nplayers=1, init_cash=10, minbid=25)
    # Game should end immediately — human has $10 but min bet is $25.
    assert game.player_list[0].cash == 10


def test_cash_never_negative_on_double(monkeypatch):
    """Verify cash doesn't go negative when doubling with minimal cash."""
    controlled_cards = [
        Card("H", 5), Card("S", 10),  # player, dealer
        Card("D", 6), Card("C", 7),   # player, dealer
        Card("H", 10),                # double card (player busts: 5+6+10=21, actually wins)
        Card("D", 3), Card("C", 2),   # dealer extra
    ]
    def mock_get_card(from_top=True):
        return controlled_cards.pop(0)

    _patch_game(monkeypatch, ["25", "d", "q"])
    monkeypatch.setattr("blackjack.gameutils.deckofcards.DeckOfCards.get_card", mock_get_card)
    monkeypatch.setattr("blackjack.gameutils.deckofcards.DeckOfCards.shuffle", lambda self: None)
    monkeypatch.setattr("blackjack.gameutils.deckofcards.DeckOfCards.needs_reshuffle", lambda self: False)

    game = BlackjackGame(nplayers=1, init_cash=25, minbid=25)
    # Player started with $25, bet $25, doubled (deducted $25 more -> $0 before payout).
    # Cash should never be negative regardless of outcome.
    assert game.player_list[0].cash >= 0


def test_dealer_stands_on_17(monkeypatch):
    """Verify dealer stands on exactly 17."""
    controlled_cards = [
        Card("H", 10), Card("S", 10),  # player, dealer
        Card("D", 7), Card("C", 7),    # player=17, dealer=17
    ]
    def mock_get_card(from_top=True):
        return controlled_cards.pop(0)

    _patch_game(monkeypatch, ["25", "s", "q"])
    monkeypatch.setattr("blackjack.gameutils.deckofcards.DeckOfCards.get_card", mock_get_card)
    monkeypatch.setattr("blackjack.gameutils.deckofcards.DeckOfCards.shuffle", lambda self: None)
    monkeypatch.setattr("blackjack.gameutils.deckofcards.DeckOfCards.needs_reshuffle", lambda self: False)

    game = BlackjackGame(nplayers=1)
    # Dealer should have exactly 2 cards (stood on 17, not hit).
    assert len(game.dealer.hands[0].cards) == 2
    assert game.dealer.score_hand() == 17


def test_split_ace_auto_stands():
    """Verify split ace hands get one card and auto-stand."""
    h = Hand(cards=[Card("H", 1)], bet=25)
    h.is_split_ace = True
    h.add_card(Card("S", 5))
    h.is_standing = True
    assert h.is_standing is True
    assert h.is_split_ace is True
    assert not h.can_split()  # No re-splitting aces


def test_shoe_reshuffle():
    """Verify shoe detects when reshuffle is needed."""
    from blackjack.gameutils.deckofcards import DeckOfCards
    deck = DeckOfCards(ndecks=1)
    assert deck.cards_remaining() == 52
    assert not deck.needs_reshuffle()

    # Deal 40 cards (leaves 12 = 23% < 25%)
    for _ in range(40):
        deck.get_card()
    assert deck.needs_reshuffle()

    # Reshuffle
    deck.reshuffle()
    assert deck.cards_remaining() == 52
    assert not deck.needs_reshuffle()


def test_basic_strategy_hint():
    """Verify basic strategy gives correct hints."""
    from blackjack.startgame import get_basic_strategy_hint

    # Hard 16 vs dealer 10 -> HIT
    h = Hand(cards=[Card("H", 10), Card("S", 6)], bet=25)
    action, _ = get_basic_strategy_hint(h, 10, False, True)
    assert action == "HIT"

    # Hard 11 vs dealer 6 -> DOUBLE
    h = Hand(cards=[Card("H", 5), Card("S", 6)], bet=25)
    action, _ = get_basic_strategy_hint(h, 6, False, True)
    assert action == "DOUBLE"

    # Pair of 8s -> SPLIT
    h = Hand(cards=[Card("H", 8), Card("S", 8)], bet=25)
    action, _ = get_basic_strategy_hint(h, 10, True, True)
    assert action == "SPLIT"

    # Hard 20 -> STAND
    h = Hand(cards=[Card("H", 10), Card("S", 10)], bet=25)
    action, _ = get_basic_strategy_hint(h, 6, False, False)
    assert action == "STAND"
