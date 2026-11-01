class TwitchWatchRepository:
    def __init__(self, db):
        self.db = db

    def get_state(self, channel_id, login):
        with self.db.connect() as conn:
            return conn.execute(
                "SELECT * FROM twitch_stream_state WHERE channel_id = ? AND login = ?",
                (channel_id, login),
            ).fetchone()

    def set_state(self, channel_id, login, is_live):
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO twitch_stream_state (channel_id, login, is_live, last_notified_at) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT (channel_id, login) DO UPDATE SET "
                "is_live = excluded.is_live, last_notified_at = excluded.last_notified_at",
                (channel_id, login, 1 if is_live else 0, self.db.now() if is_live else None),
            )
