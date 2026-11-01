class ImdbRepository:
    def __init__(self, db):
        self.db = db

    def get_match(self, ticket_id):
        with self.db.connect() as conn:
            return conn.execute(
                "SELECT * FROM imdb_matches WHERE ticket_id = ?", (ticket_id,)
            ).fetchone()

    def set_match(self, ticket_id, imdb_id, title, year, poster_url, status):
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO imdb_matches (ticket_id, imdb_id, title, year, poster_url, status) "
                "VALUES (?, ?, ?, ?, ?, ?) "
                "ON CONFLICT (ticket_id) DO UPDATE SET "
                "imdb_id = excluded.imdb_id, title = excluded.title, year = excluded.year, "
                "poster_url = excluded.poster_url, status = excluded.status",
                (ticket_id, imdb_id, title, year, poster_url, status),
            )
