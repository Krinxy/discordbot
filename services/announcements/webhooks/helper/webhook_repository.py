class WebhookRepository:
    def __init__(self, db):
        self.db = db

    def get_source_by_secret(self, secret):
        with self.db.connect() as conn:
            return conn.execute(
                "SELECT * FROM webhook_sources WHERE secret = ?", (secret,)
            ).fetchone()

    def get_sources(self):
        with self.db.connect() as conn:
            return conn.execute("SELECT * FROM webhook_sources ORDER BY id").fetchall()

    def add_source(self, source_type, name, channel_id, secret):
        with self.db.connect() as conn:
            cursor = conn.execute(
                "INSERT INTO webhook_sources (source_type, name, secret, channel_id, enabled, created_at) "
                "VALUES (?, ?, ?, ?, 1, ?)",
                (source_type, name, secret, str(channel_id), self.db.now()),
            )
            return cursor.lastrowid

    def set_enabled(self, source_id, enabled):
        with self.db.connect() as conn:
            conn.execute("UPDATE webhook_sources SET enabled = ? WHERE id = ?", (1 if enabled else 0, source_id))
