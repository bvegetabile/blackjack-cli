"""Tests for session storage, serialization, and event logging."""

import json
import os
import tempfile

import pytest

from blackjack.storage import (
    GameDatabase,
    serialize_shoe,
    restore_shoe,
    serialize_players,
    restore_players,
    burned_counts,
    snapshot_visible_cards,
)
from blackjack.gameutils.card import Card
from blackjack.gameutils.deckofcards import DeckOfCards
from blackjack.gameutils.hand import Hand
from blackjack.gameutils.player import Player


@pytest.fixture
def tmp_db(tmp_path):
    """Return a GameDatabase backed by a temp file."""
    db = GameDatabase(str(tmp_path / "test.db"))
    yield db
    db.close()


# ── Schema / basic connectivity ───────────────────────────────────────────────

def test_db_creates_schema(tmp_db):
    """All four tables should exist after init."""
    tables = {
        row[0] for row in
        tmp_db._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert {"users", "sessions", "rounds", "events"} <= tables


# ── User lifecycle ────────────────────────────────────────────────────────────

def test_get_or_create_user_creates(tmp_db):
    uid = tmp_db.get_or_create_user("alice")
    assert uid is not None
    row = tmp_db._conn.execute("SELECT username FROM users WHERE user_id = ?", (uid,)).fetchone()
    assert row["username"] == "alice"


def test_get_or_create_user_idempotent(tmp_db):
    uid1 = tmp_db.get_or_create_user("bob")
    uid2 = tmp_db.get_or_create_user("bob")
    assert uid1 == uid2
    count = tmp_db._conn.execute("SELECT COUNT(*) FROM users WHERE username='bob'").fetchone()[0]
    assert count == 1


def test_list_users(tmp_db):
    tmp_db.get_or_create_user("alice")
    tmp_db.get_or_create_user("bob")
    users = tmp_db.list_users()
    names = {u["username"] for u in users}
    assert names == {"alice", "bob"}


# ── Session lifecycle ─────────────────────────────────────────────────────────

def test_create_session(tmp_db):
    uid = tmp_db.get_or_create_user("alice")
    config = {"nplayers": 1, "ndecks": 2, "minbid": 25, "init_cash": 1000, "animation_delay": 0.4}
    sid = tmp_db.create_session(uid, config)
    row = tmp_db._conn.execute("SELECT * FROM sessions WHERE session_id = ?", (sid,)).fetchone()
    assert row["status"] == "active"
    assert row["ndecks"] == 2


def test_anonymous_session(tmp_db):
    sid = tmp_db.create_session(None, {"nplayers": 1, "ndecks": 1, "minbid": 25, "init_cash": 500})
    row = tmp_db._conn.execute("SELECT user_id FROM sessions WHERE session_id = ?", (sid,)).fetchone()
    assert row["user_id"] is None


def test_get_active_sessions_scoped_to_user(tmp_db):
    uid_alice = tmp_db.get_or_create_user("alice")
    uid_bob = tmp_db.get_or_create_user("bob")
    sid_alice = tmp_db.create_session(uid_alice, {"nplayers": 1, "ndecks": 1, "minbid": 25, "init_cash": 1000})
    sid_bob   = tmp_db.create_session(uid_bob,   {"nplayers": 1, "ndecks": 1, "minbid": 25, "init_cash": 1000})
    # Sessions with round_num=0 are filtered out; advance each to round 1.
    tmp_db.update_session_state(sid_alice, round_num=1, last_bet=25, shoe_state='{}', player_states='[{"cash":975}]')
    tmp_db.update_session_state(sid_bob,   round_num=1, last_bet=25, shoe_state='{}', player_states='[{"cash":975}]')
    alice_sessions = tmp_db.get_active_sessions(uid_alice)
    assert len(alice_sessions) == 1


def test_complete_session(tmp_db):
    uid = tmp_db.get_or_create_user("carol")
    sid = tmp_db.create_session(uid, {"nplayers": 1, "ndecks": 1, "minbid": 25, "init_cash": 1000})
    tmp_db.complete_session(sid)
    active = tmp_db.get_active_sessions(uid)
    assert len(active) == 0


def test_update_session_state(tmp_db):
    uid = tmp_db.get_or_create_user("dave")
    sid = tmp_db.create_session(uid, {"nplayers": 1, "ndecks": 1, "minbid": 25, "init_cash": 1000})
    tmp_db.update_session_state(sid, round_num=5, last_bet=50, shoe_state='{"cards":[]}', player_states='[]')
    row = tmp_db.load_session(sid)
    assert row["round_num"] == 5
    assert row["last_bet"] == 50


# ── Round tracking ────────────────────────────────────────────────────────────

def test_start_and_complete_round(tmp_db):
    uid = tmp_db.get_or_create_user("eve")
    sid = tmp_db.create_session(uid, {"nplayers": 1, "ndecks": 1, "minbid": 25, "init_cash": 1000})
    rid = tmp_db.start_round(sid, round_num=1)
    assert rid > 0
    tmp_db.complete_round(rid, dealer_cards='[{"suit":"H","rank":10}]', dealer_score=20)
    row = tmp_db._conn.execute("SELECT * FROM rounds WHERE round_id = ?", (rid,)).fetchone()
    assert row["dealer_score"] == 20
    assert row["completed_at"] is not None


# ── Event logging ─────────────────────────────────────────────────────────────

def test_log_player_action_event(tmp_db):
    uid = tmp_db.get_or_create_user("frank")
    sid = tmp_db.create_session(uid, {"nplayers": 1, "ndecks": 1, "minbid": 25, "init_cash": 1000})
    rid = tmp_db.start_round(sid, 1)
    tmp_db.log_event(sid, rid, "PLAYER_ACTION",
                     player_id=1, player_type="normal", seat_position=0,
                     action="hit", player_hand_value=14, player_is_soft=0,
                     player_cash=975.0, bet=25.0,
                     can_hit=1, can_stand=1, can_double=0, can_split=0, can_surrender=0,
                     dealer_upcard_rank=7, dealer_upcard_suit="H",
                     ndecks=1, cards_remaining=48)
    row = tmp_db._conn.execute("SELECT * FROM events WHERE session_id = ?", (sid,)).fetchone()
    assert row["event_type"] == "PLAYER_ACTION"
    assert row["action"] == "hit"
    assert row["seat_position"] == 0


def test_log_payout_event(tmp_db):
    uid = tmp_db.get_or_create_user("grace")
    sid = tmp_db.create_session(uid, {"nplayers": 1, "ndecks": 1, "minbid": 25, "init_cash": 1000})
    rid = tmp_db.start_round(sid, 1)
    tmp_db.log_event(sid, rid, "PAYOUT",
                     player_id=1, player_type="normal", seat_position=0,
                     outcome="WIN", payout=25, cash_after=1025.0,
                     ndecks=1, cards_remaining=45)
    row = tmp_db._conn.execute("SELECT outcome, payout FROM events WHERE event_type='PAYOUT'").fetchone()
    assert row["outcome"] == "WIN"
    assert row["payout"] == 25


# ── Shoe serialization ────────────────────────────────────────────────────────

def test_serialize_restore_shoe_roundtrip():
    deck = DeckOfCards(ndecks=1)
    deck.shuffle()
    # Draw some cards to populate used_cards.
    for _ in range(10):
        deck.get_card()
    original_card_count = len(deck.cards)
    original_used = len(deck.used_cards)

    json_str = serialize_shoe(deck)

    # Restore into a fresh deck.
    new_deck = DeckOfCards(ndecks=1)
    restore_shoe(new_deck, json_str)

    assert len(new_deck.cards) == original_card_count
    assert len(new_deck.used_cards) == original_used
    # Verify order is preserved.
    assert new_deck.cards[0].suit == deck.cards[0].suit
    assert new_deck.cards[0].rank == deck.cards[0].rank


# ── Player serialization ──────────────────────────────────────────────────────

def test_serialize_restore_players_roundtrip():
    human = Player(player_id=1, player_type="normal", starting_cash=1000)
    human.update_cash(-100)
    human.stats["wins"] = 3
    dealer = Player(player_id=None, player_type="dealer")
    player_list = [human, dealer]

    json_str = serialize_players(player_list)

    # Restore into a fresh player.
    human2 = Player(player_id=1, player_type="normal", starting_cash=1000)
    dealer2 = Player(player_id=None, player_type="dealer")
    restore_players([human2, dealer2], json_str)

    assert human2.cash == human.cash
    assert human2.stats["wins"] == 3


# ── State helpers ─────────────────────────────────────────────────────────────

def test_burned_counts_empty():
    deck = DeckOfCards(ndecks=1)
    counts = burned_counts(deck)
    assert counts == [0] * 13


def test_burned_counts_after_draw():
    deck = DeckOfCards(ndecks=1)
    # Force-draw an Ace (rank 1) and a King (rank 13).
    deck.cards = [Card("H", 1), Card("S", 13)] + deck.cards
    deck.get_card()  # Ace
    deck.get_card()  # King
    counts = burned_counts(deck)
    assert counts[0] >= 1   # Aces
    assert counts[12] >= 1  # Kings


def test_snapshot_visible_cards_hides_hole():
    human = Player(player_id=1, player_type="normal", starting_cash=1000)
    human.hands[0].add_card(Card("H", 10))
    human.hands[0].add_card(Card("S", 7))

    dealer = Player(player_id=None, player_type="dealer")
    dealer.hands[0].add_card(Card("D", 5))   # hole card
    dealer.hands[0].add_card(Card("C", 1))   # upcard (Ace)

    player_list = [human, dealer]
    visible = snapshot_visible_cards(player_list, dealer_revealed=False)

    ranks = {v["rank"] for v in visible}
    # Human cards visible.
    assert 10 in ranks
    assert 7 in ranks
    # Dealer upcard (Ace=1) visible.
    assert 1 in ranks
    # Dealer hole card (5) should NOT be visible.
    assert 5 not in ranks


def test_snapshot_visible_cards_reveals_all():
    human = Player(player_id=1, player_type="normal", starting_cash=1000)
    human.hands[0].add_card(Card("H", 10))
    human.hands[0].add_card(Card("S", 7))

    dealer = Player(player_id=None, player_type="dealer")
    dealer.hands[0].add_card(Card("D", 5))   # hole card
    dealer.hands[0].add_card(Card("C", 1))   # upcard

    player_list = [human, dealer]
    visible = snapshot_visible_cards(player_list, dealer_revealed=True)

    ranks = {v["rank"] for v in visible}
    assert 5 in ranks   # Hole card now visible
    assert 1 in ranks


# ── Integration: game loop with DB ────────────────────────────────────────────

def test_game_logs_events_to_db(monkeypatch, tmp_path):
    """Verify that a game with DB enabled writes events to the database."""
    from blackjack.startgame import BlackjackGame
    from blackjack.storage import GameDatabase

    db = GameDatabase(str(tmp_path / "game.db"))
    uid = db.get_or_create_user("tester")
    sid = db.create_session(uid, {"nplayers": 1, "ndecks": 1, "minbid": 25,
                                   "init_cash": 1000, "animation_delay": 0})

    inputs = iter(["25", "s", "q"])
    monkeypatch.setattr("builtins.input", lambda _="": next(inputs))
    monkeypatch.setattr("blackjack.utils.clear_terminal", lambda: None)
    monkeypatch.setattr("time.sleep", lambda s: None)

    BlackjackGame(nplayers=1, animation_delay=0, db=db, session_id=sid)

    event_count = db._conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    assert event_count > 0
    db.close()


def test_session_resume_restores_cash(monkeypatch, tmp_path):
    """Verify that shoe and player state round-trip through checkpoint."""
    import json
    from blackjack.storage import GameDatabase, serialize_shoe, serialize_players
    from blackjack.gameutils.deckofcards import DeckOfCards
    from blackjack.gameutils.player import Player

    db = GameDatabase(str(tmp_path / "resume.db"))
    uid = db.get_or_create_user("resumetest")
    sid = db.create_session(uid, {"nplayers": 1, "ndecks": 1, "minbid": 25,
                                   "init_cash": 1000, "animation_delay": 0})

    # Simulate end-of-round state save.
    deck = DeckOfCards(ndecks=1)
    deck.shuffle()
    human = Player(player_id=1, player_type="normal", starting_cash=750)
    dealer = Player(player_id=None, player_type="dealer")
    player_list = [human, dealer]

    db.update_session_state(
        sid, round_num=3, last_bet=50,
        shoe_state=serialize_shoe(deck),
        player_states=serialize_players(player_list),
    )

    # Load and verify.
    resume_data = db.load_session(sid)
    ps = json.loads(resume_data["player_states"])
    assert ps[0]["cash"] == 750
    assert resume_data["round_num"] == 3

    db.close()
