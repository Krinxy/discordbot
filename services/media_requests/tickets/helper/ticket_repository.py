class TicketRepository:
    def __init__(self, db):
        self.db = db

    def add_ticket(self, guild_id, channel_id, message_id, author_id, author, content, content_hash):
        with self.db.connect() as conn:
            now = self.db.now()
            conn.execute(
                "INSERT OR IGNORE INTO tickets "
                "(guild_id, channel_id, message_id, author_id, author, content, content_hash, "
                "status, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)",
                (guild_id, channel_id, message_id, author_id, author, content, content_hash, now, now),
            )
            row = conn.execute("SELECT id FROM tickets WHERE message_id = ?", (message_id,)).fetchone()
        return row["id"] if row else None

    def get_ticket_by_hash(self, channel_id, content_hash):
        with self.db.connect() as conn:
            return conn.execute(
                "SELECT * FROM tickets WHERE channel_id = ? AND content_hash = ? ORDER BY id DESC LIMIT 1",
                (channel_id, content_hash),
            ).fetchone()

    def get_ticket_by_message(self, message_id):
        with self.db.connect() as conn:
            return conn.execute(
                "SELECT * FROM tickets WHERE message_id = ?", (message_id,)
            ).fetchone()

    def get_ticket(self, ticket_id):
        with self.db.connect() as conn:
            return conn.execute(
                "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
            ).fetchone()

    def get_recent_tickets(self, limit):
        with self.db.connect() as conn:
            return conn.execute(
                "SELECT * FROM tickets ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()

    def get_tickets_by_status(self, status):
        with self.db.connect() as conn:
            return conn.execute(
                "SELECT * FROM tickets WHERE status = ? ORDER BY id ASC", (status,)
            ).fetchall()

    def get_open_tickets(self, channel_id):
        with self.db.connect() as conn:
            return conn.execute(
                "SELECT * FROM tickets WHERE channel_id = ? AND status != 'archive'", (channel_id,)
            ).fetchall()

    def set_ticket_message(self, ticket_id, message_id):
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE tickets SET message_id = ?, updated_at = ? WHERE id = ?",
                (message_id, self.db.now(), ticket_id),
            )

    def set_ticket_status(self, ticket_id, status, closed_at=None, archived_at=None):
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE tickets SET status = ?, updated_at = ?, "
                "closed_at = COALESCE(?, closed_at), archived_at = COALESCE(?, archived_at) "
                "WHERE id = ?",
                (status, self.db.now(), closed_at, archived_at, ticket_id),
            )

    def get_tickets_due_for_archive(self, cutoff_iso):
        with self.db.connect() as conn:
            return conn.execute(
                "SELECT * FROM tickets WHERE status = 'closed' AND closed_at <= ?",
                (cutoff_iso,),
            ).fetchall()

    def set_ticket_blocked(self, ticket_id, next_check_at):
        with self.db.connect() as conn:
            if next_check_at is None:
                conn.execute("DELETE FROM tickets_blocked WHERE ticket_id = ?", (ticket_id,))
            else:
                conn.execute(
                    "INSERT INTO tickets_blocked (ticket_id, next_check_at, pending) VALUES (?, ?, 0) "
                    "ON CONFLICT (ticket_id) DO UPDATE SET next_check_at = excluded.next_check_at, pending = 0",
                    (ticket_id, next_check_at),
                )

    def get_due_ticket_reminders(self, now_ts):
        with self.db.connect() as conn:
            return conn.execute(
                "SELECT * FROM tickets_blocked WHERE pending = 0 AND next_check_at <= ?",
                (now_ts,),
            ).fetchall()

    def set_reminder_pending(self, ticket_id):
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE tickets_blocked SET pending = 1 WHERE ticket_id = ?", (ticket_id,)
            )
