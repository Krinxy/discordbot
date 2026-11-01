from discord.ext import tasks

from dependencies.logger import Logging, log
from orchestrator.registry import ServiceRegistry
from services.announcements.twitch_watch.util import TwitchAuth


@ServiceRegistry.instance().route("/twitch_watch")
class TwitchWatch:
    def __init__(self, db, http, embeds, bot, settings):
        self.db = db
        self.embeds = embeds
        self.bot = bot
        self.log = Logging.get_logger("twitch_watch")
        self.channels = settings.get("twitch", "channels", default=[])
        self.poll_seconds = settings.get("twitch", "poll_seconds", default=120)
        client_id = settings.twitch_client_id
        client_secret = settings.twitch_client_secret
        self.enabled = bool(client_id and client_secret and self.channels)
        self.auth = TwitchAuth(http, client_id, client_secret) if self.enabled else None
        if not self.enabled:
            self.log.critical("twitch client id/secret or channel list is not configured, twitch watch is disabled")
        self.loop = tasks.loop(seconds=self.poll_seconds)(self._run_poll_loop)

    async def _notify_live(self, entry, stream):
        channel = self.bot.get_channel(int(entry["channel_id"]))
        if channel is None:
            return
        await channel.send(embed=self.embeds.twitch_live(
            entry["login"], stream.get("title"), stream.get("game_name"), stream.get("thumbnail_url"),
        ))

    async def _check_channel(self, entry, live_logins):
        is_live = entry["login"] in live_logins
        state = self.db.get_state(entry["channel_id"], entry["login"])
        was_live = state is not None and state["is_live"]
        if is_live and not was_live:
            await self._notify_live(entry, live_logins[entry["login"]])
        self.db.set_state(entry["channel_id"], entry["login"], is_live)

    async def _run_poll_loop(self):
        await self.poll()

    @log
    async def poll(self):
        if not self.enabled:
            return
        streams = await self.auth.get_live_streams([entry["login"] for entry in self.channels])
        live_logins = {stream["user_login"].lower(): stream for stream in streams}
        for entry in self.channels:
            try:
                await self._check_channel(entry, live_logins)
            except Exception:
                self.log.exception("twitch check failed for %s", entry.get("login"))

    @log
    def start(self):
        if self.enabled and not self.loop.is_running():
            self.loop.start()

    @log
    def stop(self):
        if self.loop.is_running():
            self.loop.stop()
