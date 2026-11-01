class LogRepository:
    def __init__(self, db):
        self.db = db

    def get_log_channel_id(self, guild_id):
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT value FROM guild_settings WHERE guild_id = ? AND key = 'log_channel_id'",
                (guild_id,),
            ).fetchone()
        return row["value"] if row else None

    def set_log_channel_id(self, guild_id, channel_id):
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO guild_settings (guild_id, key, value) VALUES (?, 'log_channel_id', ?) "
                "ON CONFLICT (guild_id, key) DO UPDATE SET value = excluded.value",
                (guild_id, str(channel_id)),
            )
