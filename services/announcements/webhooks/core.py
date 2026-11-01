import json

from aiohttp import web

from dependencies.logger import Logging, log
from orchestrator.registry import ServiceRegistry
from services.announcements.webhooks.helper import (
    GenericParser, LidarrParser, PlexParser, RadarrParser, SonarrParser, UptimeKumaParser,
)


@ServiceRegistry.instance().route("/webhooks")
class Webhooks:
    def __init__(self, db, bot, embeds, settings):
        self.db = db
        self.bot = bot
        self.embeds = embeds
        self.log = Logging.get_logger("webhooks")
        self.host = settings.get("webhooks", "host", default="127.0.0.1")
        self.port = settings.get("webhooks", "port", default=8788)
        self.parsers = {
            "sonarr": SonarrParser(),
            "radarr": RadarrParser(),
            "lidarr": LidarrParser(),
            "plex": PlexParser(),
            "uptime_kuma": UptimeKumaParser(),
            "generic": GenericParser(),
        }
        self.runner = None
        self.app = web.Application()
        self.app.router.add_post("/webhook/{source_type}/{secret}", self._handle_webhook)

    @staticmethod
    async def _extract_payload(request):
        if request.content_type == "multipart/form-data":
            form = await request.post()
            raw = form.get("payload")
            return json.loads(raw) if raw else {}
        try:
            return await request.json()
        except (json.JSONDecodeError, ValueError):
            return {}

    async def _handle_webhook(self, request):
        source_type = request.match_info["source_type"]
        secret = request.match_info["secret"]
        source = self.db.get_source_by_secret(secret)
        if source is None or source["source_type"] != source_type or not source["enabled"]:
            return web.json_response({"error": "unauthorized"}, status=403)
        parser = self.parsers.get(source_type)
        if parser is None:
            return web.json_response({"error": "unknown source type"}, status=404)
        payload = await self._extract_payload(request)
        parsed = parser.parse(payload)
        if parsed is not None:
            channel = self.bot.get_channel(int(source["channel_id"]))
            if channel is not None:
                title, description = parsed
                await channel.send(embed=self.embeds.webhook_event(title, description))
        return web.json_response({"ok": True})

    @log
    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        await web.TCPSite(self.runner, self.host, self.port).start()
        self.log.info("webhook relay listening on %s:%s", self.host, self.port)

    @log
    async def stop(self):
        if self.runner is not None:
            await self.runner.cleanup()
