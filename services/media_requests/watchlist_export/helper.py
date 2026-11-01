class WatchlistExportRepository:
    def __init__(self, db):
        self.db = db

    def get_unexported_matches(self):
        with self.db.connect() as conn:
            return conn.execute(
                "SELECT * FROM imdb_matches WHERE status = 'matched' "
                "AND ticket_id NOT IN (SELECT ticket_id FROM film_export_state)"
            ).fetchall()

    def set_exported(self, ticket_ids):
        with self.db.connect() as conn:
            conn.executemany(
                "INSERT INTO film_export_state (ticket_id, exported_at) VALUES (?, ?) "
                "ON CONFLICT (ticket_id) DO UPDATE SET exported_at = excluded.exported_at",
                [(ticket_id, self.db.now()) for ticket_id in ticket_ids],
            )
