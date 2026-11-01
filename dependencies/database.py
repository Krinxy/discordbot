import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone


class Database:
    def __init__(self, path):
        self.path = path

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    @staticmethod
    def now():
        return datetime.now(timezone.utc).isoformat()

    def init(self):
        with self.connect() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id INTEGER NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    PRIMARY KEY (guild_id, key)
                )"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    transferred INTEGER NOT NULL DEFAULT 0
                )"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS watched_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    channel_name TEXT NOT NULL,
                    author_id INTEGER NOT NULL,
                    author TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    message_id INTEGER
                )"""
            )
            try:
                conn.execute("ALTER TABLE watched_messages ADD COLUMN message_id INTEGER")
            except sqlite3.OperationalError:
                pass
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_watched_messages_message_id "
                "ON watched_messages(message_id)"
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS rss_seen (
                    feed_url TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    link TEXT NOT NULL,
                    published_at TEXT,
                    posted_at TEXT NOT NULL,
                    PRIMARY KEY (feed_url, item_id)
                )"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL UNIQUE,
                    author_id INTEGER NOT NULL,
                    author TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'open',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    closed_at TEXT,
                    archived_at TEXT
                )"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS tickets_blocked (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id INTEGER NOT NULL UNIQUE,
                    next_check_at INTEGER NOT NULL,
                    pending INTEGER NOT NULL DEFAULT 0
                )"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS rss_feeds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                )"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS troll_state (
                    guild_id INTEGER PRIMARY KEY,
                    enabled INTEGER NOT NULL DEFAULT 0,
                    next_troll_at INTEGER
                )"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS imdb_matches (
                    ticket_id INTEGER PRIMARY KEY,
                    imdb_id TEXT,
                    title TEXT,
                    year TEXT,
                    poster_url TEXT,
                    status TEXT NOT NULL
                )"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS free_games_seen (
                    source TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    posted_at TEXT NOT NULL,
                    PRIMARY KEY (source, item_id)
                )"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS twitch_stream_state (
                    channel_id INTEGER NOT NULL,
                    login TEXT NOT NULL,
                    is_live INTEGER NOT NULL DEFAULT 0,
                    last_notified_at TEXT,
                    PRIMARY KEY (channel_id, login)
                )"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS birthdays (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    day INTEGER NOT NULL,
                    set_at TEXT NOT NULL,
                    PRIMARY KEY (guild_id, user_id)
                )"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS webhook_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    secret TEXT NOT NULL UNIQUE,
                    channel_id TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                )"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS film_export_state (
                    ticket_id INTEGER PRIMARY KEY,
                    exported_at TEXT NOT NULL
                )"""
            )
