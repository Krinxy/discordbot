import hmac
import secrets

from aiohttp import web

from dependencies.logger import Logging, log
from dependencies.url_safety import UrlSafety
from orchestrator.registry import ServiceRegistry
from services.admin_api.helper import ServiceManifest


@ServiceRegistry.instance().route("/admin_api")
class AdminApi:
    def __init__(self, bot, settings):
        self.bot = bot
        self.log = Logging.get_logger("admin_api")
        self.manifest = ServiceManifest()
        self.host = settings.get("admin_api", "host", default="127.0.0.1")
        self.port = settings.get("admin_api", "port", default=8787)
        self.api_key = settings.admin_api_key
        self.ticket_review_statuses = {"closed", "currently_not_possible"}
        self.runner = None
        if not self.api_key:
            self.log.critical("AdminApiKey is not set, admin API will deny every request")
        self.app = web.Application(middlewares=[self._auth_middleware])
        self.app.router.add_get("/services", self._handle_services)
        self.app.router.add_get("/metrics", self._handle_metrics)
        self.app.router.add_get("/services/tickets", self._handle_tickets)
        self.app.router.add_get("/services/tickets/queue", self._handle_tickets_queue)
        self.app.router.add_post("/services/tickets/{ticket_id}/status", self._handle_ticket_status)
        self.app.router.add_get("/services/watcher", self._handle_watcher)
        self.app.router.add_get("/services/transfer", self._handle_transfer)
        self.app.router.add_post("/services/transfer/export", self._handle_transfer_export)
        self.app.router.add_get("/services/log", self._handle_log)
        self.app.router.add_post("/services/log/{guild_id}", self._handle_log_set)
        self.app.router.add_get("/services/rss", self._handle_rss)
        self.app.router.add_post("/services/rss", self._handle_rss_add)
        self.app.router.add_post("/services/rss/{feed_id}/enabled", self._handle_rss_set_enabled)
        self.app.router.add_get("/services/webhooks", self._handle_webhooks)
        self.app.router.add_post("/services/webhooks", self._handle_webhooks_add)
        self.app.router.add_post("/services/webhooks/{source_id}/enabled", self._handle_webhooks_set_enabled)
        self.app.router.add_get("/services/logs", self._handle_system_logs)
        self.app.router.add_get("/services/{slug}", self._handle_service_detail)

    @staticmethod
    def _row_to_dict(row):
        return dict(row)

    @web.middleware
    async def _auth_middleware(self, request, handler):
        expected = f"Bearer {self.api_key}" if self.api_key else None
        provided = request.headers.get("Authorization", "")
        if expected is None or not hmac.compare_digest(provided, expected):
            return web.json_response({"error": "unauthorized"}, status=401)
        return await handler(request)

    async def _handle_services(self, request):
        return web.json_response(self.manifest.tiles())

    async def _handle_metrics(self, request):
        return web.json_response(self.bot.metrics.snapshot)

    async def _handle_tickets(self, request):
        rows = self.bot.tickets.db.get_recent_tickets(limit=50)
        return web.json_response([self._row_to_dict(row) for row in rows])

    async def _handle_tickets_queue(self, request):
        rows = self.bot.tickets.db.get_tickets_by_status("open")
        return web.json_response([self._row_to_dict(row) for row in rows])

    async def _handle_ticket_status(self, request):
        ticket_id = int(request.match_info["ticket_id"])
        body = await request.json()
        status = body.get("status")
        if status not in self.ticket_review_statuses:
            return web.json_response({"error": "invalid status"}, status=400)
        closed_at = self.bot.db.now() if status == "closed" else None
        self.bot.tickets.db.set_ticket_status(ticket_id, status, closed_at=closed_at)
        return web.json_response({"id": ticket_id, "status": status})

    async def _handle_watcher(self, request):
        rows = self.bot.watcher.db.get_recent_watched_messages(limit=50)
        return web.json_response([self._row_to_dict(row) for row in rows])

    async def _handle_transfer(self, request):
        rows = self.bot.transfer.db.get_open_requests()
        return web.json_response({
            "open_count": len(rows),
            "requests": [self._row_to_dict(row) for row in rows],
        })

    async def _handle_transfer_export(self, request):
        path, count = self.bot.transfer.export()
        return web.json_response({"path": path.name if path else None, "count": count})

    async def _handle_log(self, request):
        guilds = [
            {
                "guild_id": guild.id,
                "guild_name": guild.name,
                "log_channel_id": self.bot.log.db.get_log_channel_id(guild.id),
            }
            for guild in self.bot.guilds
        ]
        return web.json_response(guilds)

    async def _handle_log_set(self, request):
        guild_id = int(request.match_info["guild_id"])
        body = await request.json()
        channel_id = int(body["channel_id"])
        self.bot.log.db.set_log_channel_id(guild_id, channel_id)
        return web.json_response({"guild_id": guild_id, "log_channel_id": str(channel_id)})

    async def _handle_rss(self, request):
        rows = self.bot.rss.db.get_feeds()
        return web.json_response([self._row_to_dict(row) for row in rows])

    async def _handle_rss_add(self, request):
        body = await request.json()
        url = body.get("url", "").strip()
        name = body.get("name", "").strip()
        try:
            channel_id = int(body.get("channel_id"))
        except (TypeError, ValueError):
            return web.json_response({"error": "channel_id must be a discord channel id"}, status=400)
        if not url or not name:
            return web.json_response({"error": "url and name are required"}, status=400)
        if not UrlSafety.is_safe(url):
            return web.json_response({"error": "url is not allowed"}, status=400)
        feed_id = self.bot.rss.db.add_feed(url, channel_id, name)
        return web.json_response({"id": feed_id, "url": url, "channel_id": str(channel_id), "name": name, "enabled": 1})

    async def _handle_rss_set_enabled(self, request):
        feed_id = int(request.match_info["feed_id"])
        body = await request.json()
        self.bot.rss.db.set_feed_enabled(feed_id, bool(body.get("enabled")))
        return web.json_response({"id": feed_id, "enabled": bool(body.get("enabled"))})

    def _webhook_to_dict(self, row):
        data = self._row_to_dict(row)
        data["secret"] = None
        return data

    async def _handle_webhooks(self, request):
        rows = self.bot.webhooks.db.get_sources()
        return web.json_response([self._webhook_to_dict(row) for row in rows])

    async def _handle_webhooks_add(self, request):
        body = await request.json()
        source_type = body.get("source_type", "").strip()
        name = body.get("name", "").strip()
        if source_type not in self.bot.webhooks.parsers:
            return web.json_response({"error": "unknown source_type"}, status=400)
        try:
            channel_id = int(body.get("channel_id"))
        except (TypeError, ValueError):
            return web.json_response({"error": "channel_id must be a discord channel id"}, status=400)
        if not name:
            return web.json_response({"error": "name is required"}, status=400)
        secret = secrets.token_urlsafe(24)
        source_id = self.bot.webhooks.db.add_source(source_type, name, channel_id, secret)
        return web.json_response({
            "id": source_id, "source_type": source_type, "name": name,
            "channel_id": str(channel_id), "secret": secret,
            "url": f"/webhook/{source_type}/{secret}",
        })

    async def _handle_webhooks_set_enabled(self, request):
        source_id = int(request.match_info["source_id"])
        body = await request.json()
        self.bot.webhooks.db.set_enabled(source_id, bool(body.get("enabled")))
        return web.json_response({"id": source_id, "enabled": bool(body.get("enabled"))})

    async def _handle_system_logs(self, request):
        if Logging.buffer_handler is None:
            return web.json_response([])
        limit = min(int(request.query.get("limit", 200)), 500)
        return web.json_response(Logging.buffer_handler.snapshot(limit=limit))

    async def _handle_service_detail(self, request):
        entry = self.manifest.tile_by_slug(request.match_info["slug"])
        if entry is None:
            return web.json_response({"error": "unknown service"}, status=404)
        return web.json_response({"slug": entry["slug"], "on_hold": entry["on_hold"], "detail": None})

    @log
    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        await web.TCPSite(self.runner, self.host, self.port).start()
        self.log.info("admin API listening on %s:%s", self.host, self.port)

    @log
    async def stop(self):
        if self.runner is not None:
            await self.runner.cleanup()
