from dependencies.logger import Logging, log
from orchestrator.registry import ServiceRegistry


@ServiceRegistry.instance().route("/watchlist_export")
class WatchlistExport:
    def __init__(self, db, http, settings):
        self.db = db
        self.http = http
        self.log = Logging.get_logger("watchlist_export")
        self.target_url = settings.get("watchlist_export", "target_url", default="")
        self.token = settings.watchlist_export_token
        self.enabled = bool(self.target_url and self.token)
        if not self.enabled:
            self.log.critical("watchlist_export.target_url or the export token is not set, export is disabled")

    @staticmethod
    def _to_payload(row):
        return {"imdb_id": row["imdb_id"], "title": row["title"], "year": row["year"], "poster_url": row["poster_url"]}

    @log
    async def export(self):
        if not self.enabled:
            return 0
        rows = self.db.get_unexported_matches()
        if not rows:
            return 0
        await self.http.post_json(
            self.target_url,
            json_body={"films": [self._to_payload(row) for row in rows]},
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.db.set_exported([row["ticket_id"] for row in rows])
        return len(rows)
