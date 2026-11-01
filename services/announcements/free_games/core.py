from datetime import datetime, timedelta, timezone

from discord.ext import tasks

from dependencies.logger import Logging, log
from orchestrator.registry import ServiceRegistry
from services.announcements.free_games.util import FreeGamesFetcher


@ServiceRegistry.instance().route("/free_games")
class FreeGames:
    def __init__(self, db, http, embeds, bot, settings):
        self.db = db
        self.http = http
        self.embeds = embeds
        self.bot = bot
        self.log = Logging.get_logger("free_games")
        self.fetcher = FreeGamesFetcher()
        self.channel_id = settings.get("free_games", "channel_id", default=0)
        self.poll_seconds = settings.get("free_games", "poll_seconds", default=3600)
        self.retention_days = settings.get("free_games", "retention_days", default=90)
        if not self.channel_id:
            self.log.critical("free_games.channel_id is not set, free games will not be announced")
        self.loop = tasks.loop(seconds=self.poll_seconds)(self._run_poll_loop)

    async def _post_game(self, source, item_id, title, url, until):
        channel = self.bot.get_channel(int(self.channel_id))
        if channel is None:
            return
        await channel.send(embed=self.embeds.free_game(title, url, source, until))
        self.db.add_seen(source, item_id)

    async def _poll_source(self, source, fetch_coro):
        for item_id, title, url, until in await fetch_coro:
            if not item_id or self.db.get_seen(source, item_id) is not None:
                continue
            await self._post_game(source, item_id, title, url, until)

    async def _fetch_epic(self):
        data = await self.http.get_json(self.fetcher.epic_url)
        return self.fetcher.parse_epic(data)

    async def _fetch_steam(self):
        data = await self.http.get_json(self.fetcher.steam_url)
        return self.fetcher.parse_steam(data)

    def _prune_seen(self):
        cutoff = (datetime.now(timezone.utc) - timedelta(days=self.retention_days)).isoformat()
        self.db.delete_seen_older_than(cutoff)

    async def _run_poll_loop(self):
        await self.poll()

    @log
    async def poll(self):
        if not self.channel_id:
            return
        self._prune_seen()
        for source, fetch in (("epic", self._fetch_epic()), ("steam", self._fetch_steam())):
            try:
                await self._poll_source(source, fetch)
            except Exception:
                self.log.exception("free games poll failed for %s", source)

    @log
    def start(self):
        if not self.loop.is_running():
            self.loop.start()

    @log
    def stop(self):
        if self.loop.is_running():
            self.loop.stop()
