class BirthdayRepository:
    def __init__(self, db):
        self.db = db

    def set_birthday(self, guild_id, user_id, month, day):
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO birthdays (guild_id, user_id, month, day, set_at) VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT (guild_id, user_id) DO UPDATE SET "
                "month = excluded.month, day = excluded.day, set_at = excluded.set_at",
                (guild_id, user_id, month, day, self.db.now()),
            )

    def get_birthdays_on(self, guild_id, month, day):
        with self.db.connect() as conn:
            return conn.execute(
                "SELECT * FROM birthdays WHERE guild_id = ? AND month = ? AND day = ?",
                (guild_id, month, day),
            ).fetchall()
