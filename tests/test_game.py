from blackjack.startgame import BlackjackGame


def test_game_smoke_test(monkeypatch):
    """Verify a game completes when the player stands then quits."""
    inputs = iter(["stand", "q"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    game = BlackjackGame(nplayers=1)
    assert len(game.player_list) == 2  # 1 human + 1 dealer


def test_game_with_computer_players(monkeypatch):
    """Verify a game with computer players completes."""
    inputs = iter(["stand", "q"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    game = BlackjackGame(nplayers=2)
    assert len(game.player_list) == 3  # 1 human + 1 computer + 1 dealer


def test_game_hit_then_stand(monkeypatch):
    """Verify a game where the player hits once then stands."""
    inputs = iter(["hit", "stand", "q"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    game = BlackjackGame(nplayers=1)
    # Player should have at least 3 cards (2 dealt + 1 hit)
    assert len(game.player_list[0].hand) >= 3


def test_game_multi_deck(monkeypatch):
    """Verify a game works with multiple decks."""
    inputs = iter(["stand", "q"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    game = BlackjackGame(nplayers=1, ndecks=2)
    assert game.deck is not None
