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
    _patch_game(monkeypatch, [])
    game = BlackjackGame(nplayers=1, init_cash=10, minbid=25)
    # Game should end immediately — human has $10 but min bet is $25.
    assert game.player_list[0].cash == 10
