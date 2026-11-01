class WatcherRepository:
    def __init__(self, db):
        self.db = db

    def add_watched_message(self, guild_id, channel_id, channel_name, author_id, author, content, message_id):
        with self.db.connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO watched_messages "
                "(guild_id, channel_id, channel_name, author_id, author, content, created_at, message_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (guild_id, channel_id, channel_name, author_id, author, content, self.db.now(), message_id),
            )

    def get_watched_message(self, message_id):
        with self.db.connect() as conn:
            return conn.execute(
                "SELECT * FROM watched_messages WHERE message_id = ?", (message_id,)
            ).fetchone()

    def get_recent_watched_messages(self, limit):
        with self.db.connect() as conn:
            return conn.execute(
                "SELECT * FROM watched_messages ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
