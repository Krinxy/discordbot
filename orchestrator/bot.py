import time

import discord
from discord import app_commands
from discord.ext import commands

from dependencies.auth import Auth
from dependencies.database import Database
from dependencies.http import Http
from dependencies.logger import Logging
from dependencies.metrics import Metrics
from orchestrator.embeds import Embeds
from orchestrator.handlers import Handlers
from orchestrator.registry import ServiceRegistry
from orchestrator.router import Router
from orchestrator.voice import Voice
from services.admin_api import AdminApi
from services.announcements.birthdays import Birthdays
from services.announcements.birthdays.helper import BirthdayRepository
from services.announcements.free_games import FreeGames
from services.announcements.free_games.helper import FreeGamesRepository
from services.announcements.rss import Rss
from services.announcements.rss.helper import RssRepository
from services.announcements.twitch_watch import TwitchWatch
from services.announcements.twitch_watch.helper import TwitchWatchRepository
from services.announcements.webhooks import Webhooks
from services.announcements.webhooks.helper import WebhookRepository
from services.channel_logging.backfill import Backfill
from services.channel_logging.channel_watch import Watcher
from services.channel_logging.channel_watch.helper import WatcherRepository
from services.channel_logging.message_log import Log
from services.channel_logging.message_log.helper import LogRepository
from services.channel_logging.transfer import Transfer
from services.channel_logging.transfer.helper import TransferRepository
from services.media_requests.imdb import Imdb
from services.media_requests.tickets import Tickets
from services.media_requests.tickets.helper import TicketBlockedButton, TicketRepository
from services.media_requests.watchlist_export import WatchlistExport
from services.media_requests.watchlist_export.helper import WatchlistExportRepository
from services.voice.music import Music
from services.voice.troll import Troll
from services.voice.troll.helper import TrollRepository
from services.voice.voice_channels import VoiceChannels
from slash_commands.commands import CommandsCog


class MoisBot(commands.Bot):
    def __init__(self, settings):
        super().__init__(command_prefix="!", intents=self._build_intents())
        self.settings = settings
        self.db_path = settings.config_dir / "bot.db"
        self.export_dir = settings.base_dir / settings.get("requests", "export_dir", default="exports")
        self.db = Database(self.db_path)
        self.embeds = Embeds()
        self.voice = Voice()
        self.log = Log(LogRepository(self.db), self.embeds)
        self.transfer = Transfer(TransferRepository(self.db), self.export_dir)
        self.watcher = Watcher(WatcherRepository(self.db), settings)
        self.http_client = Http()
        self.auth = Auth.instance()
        ServiceRegistry.instance().route("/logging")(Logging)
        self.rss = Rss(RssRepository(self.db), self.http_client, self.embeds, self, settings)
        self.music = Music(self, self.voice)
        self.troll = Troll(TrollRepository(self.db), self, settings, self.voice)
        self.imdb = Imdb(self, self.http_client, self.voice, self.embeds, self.db, settings)
        self.tickets = Tickets(TicketRepository(self.db), self, settings, self.voice, self.imdb)
        self.voice_channels = VoiceChannels(self, settings)
        self.backfill = Backfill(self, self.tickets, self.watcher, settings)
        self.free_games = FreeGames(FreeGamesRepository(self.db), self.http_client, self.embeds, self, settings)
        self.twitch_watch = TwitchWatch(TwitchWatchRepository(self.db), self.http_client, self.embeds, self, settings)
        self.birthdays = Birthdays(BirthdayRepository(self.db), self, self.embeds, settings)
        self.webhooks = Webhooks(WebhookRepository(self.db), self, self.embeds, settings)
        self.watchlist_export = WatchlistExport(WatchlistExportRepository(self.db), self.http_client, settings)
        self.admin_api = AdminApi(self, settings)
        self.metrics = Metrics()
        self.router = Router(self.metrics)
        Handlers(self, self.router)
        self.events = {
            "ready": self._on_ready,
            "message": self._on_message,
            "message_delete": self._on_message_delete,
            "message_edit": self._on_message_edit,
            "reaction_add": self._on_reaction_add,
            "command_completion": self._on_command_completion,
            "voice_state_update": self._on_voice_state_update,
        }

    @staticmethod
    def _build_intents():
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.reactions = True
        intents.voice_states = True
        return intents

    @staticmethod
    def _should_log(author, guild):
        return not author.bot and guild is not None

    async def _on_ready(self):
        for guild in self.guilds:
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        print(f"Bot is ready: {self.user.name} ({len(self.guilds)} servers)")

    async def dispatch_message(self, message, backfill=False):
        if not await self.tickets.handle_message(message, backfill=backfill):
            self.watcher.handle_message(message)

    async def _on_message(self, message):
        await self.dispatch_message(message)

    async def _on_message_delete(self, message):
        if self._should_log(message.author, message.guild):
            await self.log.log_delete(message)

    async def _on_message_edit(self, before, after):
        if self._should_log(before.author, before.guild) and before.content != after.content:
            await self.log.log_edit(before, after)

    async def _on_reaction_add(self, payload):
        await self.tickets.handle_reaction(payload)

    async def _on_command_completion(self, interaction, command):
        self.transfer.record_command(interaction, command.qualified_name)

    async def _on_voice_state_update(self, member, before, after):
        await self.voice_channels.handle_voice_state_update(member, before, after)

    async def _on_command_error(self, interaction, error):
        original = getattr(error, "original", error)
        if isinstance(original, app_commands.CheckFailure):
            return
        text = "I'm missing permission for that (check role hierarchy)." if isinstance(original, discord.Forbidden) \
            else f"Error: {original}"
        send = interaction.followup.send if interaction.response.is_done() else interaction.response.send_message
        await send(text, ephemeral=True)

    async def setup_hook(self):
        self.db.init()
        await self.add_cog(CommandsCog(self))
        self.tree.on_error = self._on_command_error
        self.add_dynamic_items(TicketBlockedButton)
        self.rss.start()
        self.tickets.start()
        self.voice_channels.start()
        self.backfill.start()
        self.troll.start()
        self.free_games.start()
        self.twitch_watch.start()
        self.birthdays.start()
        await self.webhooks.start()
        await self.admin_api.start()

    async def close(self):
        self.rss.stop()
        self.tickets.stop()
        self.voice_channels.stop()
        self.backfill.stop()
        self.troll.stop()
        self.free_games.stop()
        self.twitch_watch.stop()
        self.birthdays.stop()
        await self.webhooks.stop()
        await self.admin_api.stop()
        await self.http_client.close()
        await super().close()

    async def on_ready(self):
        await self.handle_event("ready")

    async def on_app_command_completion(self, interaction, command):
        await self.handle_event("command_completion", interaction=interaction, command=command)

    async def on_message(self, message):
        await self.handle_event("message", message=message)

    async def on_message_delete(self, message):
        await self.handle_event("message_delete", message=message)

    async def on_message_edit(self, before, after):
        await self.handle_event("message_edit", before=before, after=after)

    async def on_raw_reaction_add(self, payload):
        await self.handle_event("reaction_add", payload=payload)

    async def on_voice_state_update(self, member, before, after):
        await self.handle_event("voice_state_update", member=member, before=before, after=after)

    async def handle_event(self, name, **kwargs):
        handler = self.events.get(name)
        if handler is None:
            return
        start = time.perf_counter()
        success = True
        try:
            await handler(**kwargs)
        except Exception:
            success = False
            raise
        finally:
            self.metrics.record(f"event:{name}", time.perf_counter() - start, success)
