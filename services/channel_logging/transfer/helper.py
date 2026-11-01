class TransferRepository:
    def __init__(self, db):
        self.db = db

    def get_open_requests(self):
        with self.db.connect() as conn:
            return conn.execute(
                "SELECT * FROM requests WHERE transferred = 0 ORDER BY id"
            ).fetchall()

    def add_request(self, guild_id, user_id, request_type, payload):
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO requests (guild_id, user_id, type, payload, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (guild_id, user_id, request_type, payload, self.db.now()),
            )

    def set_requests_transferred(self, ids):
        if not ids:
            return
        with self.db.connect() as conn:
            conn.executemany(
                "UPDATE requests SET transferred = 1 WHERE id = ?", [(i,) for i in ids]
            )
