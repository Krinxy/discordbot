class RssRepository:
    def __init__(self, db):
        self.db = db

    def get_seen(self, feed_url, item_id):
        with self.db.connect() as conn:
            return conn.execute(
                "SELECT 1 FROM rss_seen WHERE feed_url = ? AND item_id = ?",
                (feed_url, item_id),
            ).fetchone()

    def add_seen(self, feed_url, item_id, title, link, published_at):
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO rss_seen (feed_url, item_id, title, link, published_at, posted_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (feed_url, item_id, title, link, published_at, self.db.now()),
            )

    def get_feeds(self):
        with self.db.connect() as conn:
            return conn.execute("SELECT * FROM rss_feeds ORDER BY id").fetchall()

    def get_active_feeds(self):
        with self.db.connect() as conn:
            return conn.execute("SELECT * FROM rss_feeds WHERE enabled = 1 ORDER BY id").fetchall()

    def add_feed(self, url, channel_id, name):
        with self.db.connect() as conn:
            cursor = conn.execute(
                "INSERT INTO rss_feeds (url, channel_id, name, enabled, created_at) VALUES (?, ?, ?, 1, ?)",
                (url, str(channel_id), name, self.db.now()),
            )
            return cursor.lastrowid

    def set_feed_enabled(self, feed_id, enabled):
        with self.db.connect() as conn:
            conn.execute("UPDATE rss_feeds SET enabled = ? WHERE id = ?", (1 if enabled else 0, feed_id))

    def delete_seen_older_than(self, cutoff_iso):
        with self.db.connect() as conn:
            conn.execute("DELETE FROM rss_seen WHERE posted_at < ?", (cutoff_iso,))
