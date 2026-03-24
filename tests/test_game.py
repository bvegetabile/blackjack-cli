from blackjack.startgame import BlackjackGame, get_player_action


def _patch_game(monkeypatch, inputs):
    """Monkeypatch input and clear_terminal for clean test runs."""
    input_iter = iter(inputs)
    monkeypatch.setattr("builtins.input", lambda _="": next(input_iter))
    monkeypatch.setattr("blackjack.utils.clear_terminal", lambda: None)


def test_game_smoke_test(monkeypatch):
    """Verify a game completes when the player stands then quits."""
    _patch_game(monkeypatch, ["s", "q"])
    game = BlackjackGame(nplayers=1)
    assert len(game.player_list) == 2  # 1 human + 1 dealer


def test_game_with_computer_players(monkeypatch):
    """Verify a game with computer players completes."""
    _patch_game(monkeypatch, ["s", "q"])
    game = BlackjackGame(nplayers=2)
    assert len(game.player_list) == 3  # 1 human + 1 computer + 1 dealer


def test_game_hit_then_stand(monkeypatch):
    """Verify a game where the player hits once then stands."""
    from blackjack.gameutils.card import Card

    # Use controlled cards to avoid bust: player gets 2+3, hit gets 4 = 9 total.
    controlled_cards = [
        Card("H", 2), Card("S", 5),   # player card 1, dealer card 1
        Card("D", 3), Card("C", 10),  # player card 2, dealer card 2
        Card("H", 4),                 # hit card for player
        Card("D", 2), Card("C", 3),   # extra for dealer hits
    ]

    def mock_get_card(from_top=True):
        return controlled_cards.pop(0)

    _patch_game(monkeypatch, ["h", "s", "q"])
    monkeypatch.setattr("blackjack.gameutils.deckofcards.DeckOfCards.get_card", mock_get_card)
    monkeypatch.setattr("blackjack.gameutils.deckofcards.DeckOfCards.shuffle", lambda self: None)

    game = BlackjackGame(nplayers=1)
    assert len(game.player_list[0].hand) == 3


def test_game_multi_deck(monkeypatch):
    """Verify a game works with multiple decks."""
    _patch_game(monkeypatch, ["s", "q"])
    game = BlackjackGame(nplayers=1, ndecks=2)
    assert game.deck is not None


def test_game_double_down(monkeypatch):
    """Verify double down deals one card and ends the turn."""
    _patch_game(monkeypatch, ["d", "q"])
    game = BlackjackGame(nplayers=1)
    # Player should have exactly 3 cards (2 dealt + 1 double)
    assert len(game.player_list[0].hand) == 3
    assert game.player_list[0].hands[0].is_doubled is True


def test_game_split(monkeypatch):
    """Verify split creates two hands when dealt a pair."""
    from blackjack.gameutils.card import Card

    # Build a deck where the player gets a pair of 8s.
    controlled_cards = [
        Card("H", 8), Card("S", 5),   # player card 1, dealer card 1
        Card("D", 8), Card("C", 10),  # player card 2, dealer card 2
        # After split: new cards for each hand, then stand both.
        Card("H", 3), Card("S", 6),
        # Extra cards for dealer hits.
        Card("D", 2), Card("C", 3), Card("H", 4),
    ]

    def mock_get_card(from_top=True):
        return controlled_cards.pop(0)

    _patch_game(monkeypatch, ["p", "s", "s", "q"])
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
