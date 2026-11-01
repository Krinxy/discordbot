class FreeGamesRepository:
    def __init__(self, db):
        self.db = db

    def get_seen(self, source, item_id):
        with self.db.connect() as conn:
            return conn.execute(
                "SELECT 1 FROM free_games_seen WHERE source = ? AND item_id = ?",
                (source, item_id),
            ).fetchone()

    def add_seen(self, source, item_id):
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO free_games_seen (source, item_id, posted_at) VALUES (?, ?, ?)",
                (source, item_id, self.db.now()),
            )

    def delete_seen_older_than(self, cutoff_iso):
        with self.db.connect() as conn:
            conn.execute("DELETE FROM free_games_seen WHERE posted_at < ?", (cutoff_iso,))
