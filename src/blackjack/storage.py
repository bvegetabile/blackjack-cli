"""Session persistence and event logging for blackjack-cli."""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DEFAULT_DB_PATH = Path.home() / ".blackjack" / "game.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id        TEXT PRIMARY KEY,
    username       TEXT NOT NULL UNIQUE,
    created_at     TEXT NOT NULL,
    last_played_at TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id      TEXT PRIMARY KEY,
    user_id         TEXT REFERENCES users(user_id),
    started_at      TEXT NOT NULL,
    last_played_at  TEXT NOT NULL,
    status          TEXT NOT NULL,
    nplayers        INTEGER,
    ndecks          INTEGER,
    minbid          INTEGER,
    init_cash       INTEGER,
    animation_delay REAL,
    round_num       INTEGER DEFAULT 0,
    last_bet        INTEGER,
    shoe_state      TEXT,
    player_states   TEXT
);

CREATE TABLE IF NOT EXISTS rounds (
    round_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    TEXT NOT NULL REFERENCES sessions(session_id),
    round_number  INTEGER NOT NULL,
    started_at    TEXT NOT NULL,
    completed_at  TEXT,
    reshuffled    INTEGER DEFAULT 0,
    dealer_cards  TEXT,
    dealer_score  INTEGER
);

CREATE TABLE IF NOT EXISTS events (
    event_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id         TEXT NOT NULL,
    round_id           INTEGER NOT NULL,
    occurred_at        TEXT NOT NULL,
    event_type         TEXT NOT NULL,
    player_id          INTEGER,
    player_type        TEXT,
    hand_index         INTEGER DEFAULT 0,
    seat_position      INTEGER,
    action             TEXT,
    card_suit          TEXT,
    card_rank          INTEGER,
    player_cards       TEXT,
    player_hand_value  INTEGER,
    player_is_soft     INTEGER,
    player_cash        REAL,
    bet                REAL,
    can_hit            INTEGER,
    can_stand          INTEGER,
    can_double         INTEGER,
    can_split          INTEGER,
    can_surrender      INTEGER,
    dealer_upcard_rank INTEGER,
    dealer_upcard_suit TEXT,
    ndecks             INTEGER,
    visible_cards      TEXT,
    burned_counts      TEXT,
    outcome            TEXT,
    payout             REAL,
    cash_after         REAL,
    cards_remaining    INTEGER
);
"""


class GameDatabase:
    def __init__(self, db_path: str):
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ── User management ────────────────────────────────────────────────────

    def get_or_create_user(self, username: str) -> str:
        """Return the user_id for username, creating a new record if needed."""
        row = self._conn.execute(
            "SELECT user_id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if row:
            self._conn.execute(
                "UPDATE users SET last_played_at = ? WHERE user_id = ?",
                (self._now(), row["user_id"]),
            )
            self._conn.commit()
            return row["user_id"]
        user_id = str(uuid.uuid4())
        self._conn.execute(
            "INSERT INTO users (user_id, username, created_at, last_played_at) VALUES (?, ?, ?, ?)",
            (user_id, username, self._now(), self._now()),
        )
        self._conn.commit()
        return user_id

    def list_users(self) -> list:
        """Return all users ordered by most recently played."""
        rows = self._conn.execute(
            "SELECT user_id, username FROM users ORDER BY last_played_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Session management ─────────────────────────────────────────────────

    def create_session(self, user_id: Optional[str], config: dict) -> str:
        """Create a new session and return its session_id."""
        session_id = str(uuid.uuid4())
        now = self._now()
        self._conn.execute(
            """INSERT INTO sessions
               (session_id, user_id, started_at, last_played_at, status,
                nplayers, ndecks, minbid, init_cash, animation_delay, round_num)
               VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, 0)""",
            (
                session_id, user_id, now, now,
                config.get("nplayers"), config.get("ndecks"),
                config.get("minbid"), config.get("init_cash"),
                config.get("animation_delay"),
            ),
        )
        self._conn.commit()
        return session_id

    def update_session_state(
        self, session_id: str, round_num: int, last_bet: Optional[int],
        shoe_state: str, player_states: str
    ):
        """Checkpoint session state after a completed round."""
        self._conn.execute(
            """UPDATE sessions SET round_num = ?, last_bet = ?, shoe_state = ?,
               player_states = ?, last_played_at = ? WHERE session_id = ?""",
            (round_num, last_bet, shoe_state, player_states, self._now(), session_id),
        )
        self._conn.commit()

    def complete_session(self, session_id: str):
        """Mark a session as completed (player quit)."""
        self._conn.execute(
            "UPDATE sessions SET status = 'completed', last_played_at = ? WHERE session_id = ?",
            (self._now(), session_id),
        )
        self._conn.commit()

    def get_active_sessions(self, user_id: Optional[str]) -> list:
        """Return active sessions with at least one completed round for the given user."""
        rows = self._conn.execute(
            """SELECT session_id, started_at, last_played_at, round_num,
                      player_states, ndecks, nplayers, last_bet, init_cash
               FROM sessions
               WHERE user_id IS ? AND status = 'active' AND round_num > 0
               ORDER BY last_played_at DESC""",
            (user_id,),
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("player_states"):
                ps = json.loads(d["player_states"])
                d["cash"] = ps[0]["cash"] if ps else 0
            else:
                d["cash"] = None
            result.append(d)
        return result

    def load_session(self, session_id: str) -> dict:
        """Return all columns for a session as a dict."""
        row = self._conn.execute(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        return dict(row) if row else {}

    # ── Round tracking ─────────────────────────────────────────────────────

    def start_round(self, session_id: str, round_num: int) -> int:
        """Insert a new round row and return its round_id."""
        cur = self._conn.execute(
            "INSERT INTO rounds (session_id, round_number, started_at) VALUES (?, ?, ?)",
            (session_id, round_num, self._now()),
        )
        self._conn.commit()
        return cur.lastrowid

    def complete_round(
        self, round_id: int, dealer_cards: str, dealer_score: int, reshuffled: bool = False
    ):
        """Finalize a round row with dealer result."""
        self._conn.execute(
            """UPDATE rounds SET completed_at = ?, reshuffled = ?, dealer_cards = ?, dealer_score = ?
               WHERE round_id = ?""",
            (self._now(), int(reshuffled), dealer_cards, dealer_score, round_id),
        )
        self._conn.commit()

    # ── Event logging ──────────────────────────────────────────────────────

    def log_event(self, session_id: str, round_id: int, event_type: str, **kwargs):
        """Insert one event row. Extra kwargs map directly to event column names."""
        columns = ["session_id", "round_id", "occurred_at", "event_type"] + list(kwargs.keys())
        values = [session_id, round_id, self._now(), event_type] + list(kwargs.values())
        placeholders = ", ".join("?" * len(values))
        col_str = ", ".join(columns)
        self._conn.execute(
            f"INSERT INTO events ({col_str}) VALUES ({placeholders})", values
        )
        self._conn.commit()

    def close(self):
        self._conn.close()


# ── Serialization helpers ──────────────────────────────────────────────────────


def serialize_shoe(deck) -> str:
    """Serialize deck state to JSON for checkpoint storage."""
    return json.dumps({
        "cards": [{"suit": c.suit, "rank": c.rank} for c in deck.cards],
        "used_cards": [{"suit": c.suit, "rank": c.rank} for c in deck.used_cards],
        "total_cards": deck.total_cards,
    })


def restore_shoe(deck, json_str: str):
    """Restore deck state from a JSON checkpoint string (mutates deck in place)."""
    from .gameutils.card import Card
    data = json.loads(json_str)
    deck.cards = [Card(d["suit"], d["rank"]) for d in data["cards"]]
    deck.used_cards = [Card(d["suit"], d["rank"]) for d in data["used_cards"]]
    deck.total_cards = data["total_cards"]


def serialize_players(player_list) -> str:
    """Serialize human + computer player states to JSON (excludes dealer)."""
    result = []
    for p in player_list[:-1]:
        result.append({
            "player_id": p.player_id,
            "player_type": p.player_type,
            "cash": p.cash,
            "prev_cash": p.prev_cash,
            "stats": p.stats,
        })
    return json.dumps(result)


def restore_players(player_list, json_str: str):
    """Restore player cash and stats from a JSON checkpoint (mutates players in place)."""
    data = json.loads(json_str)
    for d, player in zip(data, player_list[:-1]):
        player.cash = d["cash"]
        player.prev_cash = d["prev_cash"]
        player.stats = d["stats"]


def burned_counts(deck) -> list:
    """Return a length-13 list: count of each rank [A..K] seen since last reshuffle."""
    counts = [0] * 13
    for card in deck.used_cards:
        counts[card.rank - 1] += 1
    return counts


def snapshot_visible_cards(player_list, dealer_revealed: bool = False) -> list:
    """Return all currently visible cards across the table as a list of dicts.

    Dealer hole card is excluded unless dealer_revealed is True.
    """
    result = []
    for i, player in enumerate(player_list):
        if player.player_type == "dealer":
            cards = player.hands[0].cards
            if dealer_revealed:
                for card in cards:
                    result.append({"player_id": None, "seat": -1, "hand_index": 0,
                                   "suit": card.suit, "rank": card.rank})
            elif len(cards) > 1:
                # Only the upcard (index 1)
                c = cards[1]
                result.append({"player_id": None, "seat": -1, "hand_index": 0,
                                "suit": c.suit, "rank": c.rank})
        else:
            for hand_idx, hand in enumerate(player.hands):
                for card in hand.cards:
                    result.append({
                        "player_id": player.player_id,
                        "seat": i,
                        "hand_index": hand_idx,
                        "suit": card.suit,
                        "rank": card.rank,
                    })
    return result
