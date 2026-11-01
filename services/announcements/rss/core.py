from datetime import datetime, timedelta, timezone

from discord.ext import tasks

from dependencies.logger import Logging, log
from orchestrator.registry import ServiceRegistry
from services.announcements.rss.util import FeedParser


@ServiceRegistry.instance().route("/rss")
class Rss:
    def __init__(self, db, http, embeds, bot, settings):
        self.db = db
        self.http = http
        self.embeds = embeds
        self.bot = bot
        self.log = Logging.get_logger("rss")
        self.feed_parser = FeedParser()
        self.poll_seconds = settings.get("rss", "poll_seconds", default=900)
        self.retention_days = settings.get("rss", "retention_days", default=90)
        self.loop = tasks.loop(seconds=self.poll_seconds)(self._run_poll_loop)

    async def _post_item(self, feed, item_id, title, link, published):
        channel = self.bot.get_channel(int(feed["channel_id"]))
        if channel is None:
            return
        await channel.send(embed=self.embeds.rss_item(feed["name"], title, link, published))
        self.db.add_seen(feed["url"], item_id, title, link, published)

    async def _poll_feed(self, feed):
        xml_text = await self.http.get_text(feed["url"])
        for item_id, title, link, published in self.feed_parser.parse_feed(xml_text):
            if not item_id or self.db.get_seen(feed["url"], item_id) is not None:
                continue
            await self._post_item(feed, item_id, title, link, published)

    def _prune_seen(self):
        cutoff = (datetime.now(timezone.utc) - timedelta(days=self.retention_days)).isoformat()
        self.db.delete_seen_older_than(cutoff)

    async def _run_poll_loop(self):
        await self.poll()

    @log
    async def poll(self):
        self._prune_seen()
        for feed in self.db.get_active_feeds():
            try:
                await self._poll_feed(feed)
            except Exception:
                self.log.exception("RSS feed failed: %s", feed["url"])

    @log
    def start(self):
        if not self.loop.is_running():
            self.loop.start()

    @log
    def stop(self):
        if self.loop.is_running():
            self.loop.stop()
