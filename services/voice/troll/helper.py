class TrollRepository:
    def __init__(self, db):
        self.db = db

    def get_troll_state(self, guild_id):
        with self.db.connect() as conn:
            return conn.execute("SELECT * FROM troll_state WHERE guild_id = ?", (guild_id,)).fetchone()

    def get_due_troll_guilds(self, now_ts):
        with self.db.connect() as conn:
            return conn.execute(
                "SELECT * FROM troll_state WHERE enabled = 1 AND next_troll_at <= ?", (now_ts,)
            ).fetchall()

    def set_troll_state(self, guild_id, enabled, next_troll_at):
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO troll_state (guild_id, enabled, next_troll_at) VALUES (?, ?, ?) "
                "ON CONFLICT (guild_id) DO UPDATE SET enabled = excluded.enabled, "
                "next_troll_at = excluded.next_troll_at",
                (guild_id, 1 if enabled else 0, next_troll_at),
            )
