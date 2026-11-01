import json
from datetime import datetime, timezone

from dependencies.logger import log
from orchestrator.registry import ServiceRegistry


@ServiceRegistry.instance().route("/transfer")
class Transfer:
    def __init__(self, db, export_dir):
        self.db = db
        self.export_dir = export_dir

    @staticmethod
    def _to_dict(row):
        return {
            "id": row["id"],
            "guild_id": row["guild_id"],
            "user_id": row["user_id"],
            "type": row["type"],
            "payload": json.loads(row["payload"]),
            "created_at": row["created_at"],
        }

    def _write_file(self, data):
        self.export_dir.mkdir(exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = self.export_dir / f"requests_{stamp}.json"
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        return path

    def record_command(self, interaction, command_name):
        params = {name: str(value) for name, value in vars(interaction.namespace).items()}
        self.db.add_request(
            interaction.guild_id or 0,
            interaction.user.id,
            f"command:{command_name}",
            json.dumps(params, ensure_ascii=False),
        )

    @log
    def export(self):
        rows = self.db.get_open_requests()
        if not rows:
            return None, 0
        path = self._write_file([self._to_dict(row) for row in rows])
        self.db.set_requests_transferred([row["id"] for row in rows])
        return path, len(rows)
