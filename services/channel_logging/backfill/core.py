import discord
from discord.ext import tasks

from dependencies.logger import Logging, log
from orchestrator.registry import ServiceRegistry


@ServiceRegistry.instance().route("/backfill")
class Backfill:
    def __init__(self, bot, tickets, watcher, settings):
        self.bot = bot
        self.tickets = tickets
        self.watcher = watcher
        self.log = Logging.get_logger("backfill")
        self.channels = settings.get("watch", "channels", default=[])
        self.check_interval_seconds = settings.get("watch", "backfill_interval_seconds", default=600)
        self.loop = tasks.loop(seconds=self.check_interval_seconds)(self._run_loop)

    async def _backfill_channel(self, entry):
        channel_id = int(entry["channel_id"])
        is_ticket_channel = bool(entry.get("tickets"))
        is_known = self.tickets.db.get_ticket_by_message if is_ticket_channel else self.watcher.db.get_watched_message
        try:
            channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
            count = 0
            async for message in channel.history(limit=None, oldest_first=True):
                if is_known(message.id) is not None:
                    continue
                await self.bot.dispatch_message(message, backfill=True)
                count += 1
            if count:
                self.log.info("backfilled %s messages in #%s", count, channel.name)
            if is_ticket_channel:
                await self.tickets.backfill_reactions(channel)
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            self.log.exception("backfill failed for channel %s", channel_id)

    async def _run_loop(self):
        await self.run()

    @log
    async def run(self):
        for entry in self.channels:
            await self._backfill_channel(entry)

    @log
    def start(self):
        if self.channels and not self.loop.is_running():
            self.loop.start()

    @log
    def stop(self):
        if self.loop.is_running():
            self.loop.stop()
