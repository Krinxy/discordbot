import asyncio
import random
import time

import discord
from discord.ext import tasks

from dependencies.logger import Logging, log
from orchestrator.registry import ServiceRegistry
from services.voice.music.helper import Player
from services.voice.voice_channels.util import SlotNaming


@ServiceRegistry.instance().route("/troll")
class Troll:
    def __init__(self, db, bot, settings, chat):
        self.db = db
        self.bot = bot
        self.chat = chat
        self.log = Logging.get_logger("troll")
        self.sound_dir = settings.base_dir / "config" / settings.get("troll", "sound_dir", default="troll_sounds")
        self.interval_min_seconds = settings.get("troll", "interval_min_seconds", default=600)
        self.interval_max_seconds = settings.get("troll", "interval_max_seconds", default=1800)
        self.check_interval_seconds = settings.get("troll", "check_interval_seconds", default=60)
        self.soundboard_wait_seconds = 5
        self.arrival_delay_seconds = 2
        self.voice_channel_categories_by_id = {
            int(entry["category_id"]): entry for entry in settings.get("voice_channels", "categories", default=[])
        }
        self.loop = tasks.loop(seconds=self.check_interval_seconds)(self._run_loop)

    def _local_sound_files(self):
        if not self.sound_dir.is_dir():
            return []
        return [path for path in self.sound_dir.iterdir() if path.suffix.lower() in (".mp3", ".ogg", ".wav", ".m4a")]

    async def _fetch_soundboard_sounds(self, guild):
        try:
            sounds = await guild.fetch_soundboard_sounds()
        except (discord.Forbidden, discord.HTTPException):
            return []
        return [sound for sound in sounds if sound.available]

    async def _pick_sound(self, guild):
        pool = [("soundboard", sound) for sound in await self._fetch_soundboard_sounds(guild)]
        pool.extend(("local", path) for path in self._local_sound_files())
        return random.choice(pool) if pool else None

    def _is_voice_channels_managed(self, channel):
        entry = self.voice_channel_categories_by_id.get(channel.category_id)
        if entry is None:
            return False
        return SlotNaming.slot_from_name(channel.name, entry["name_pool"]) is not None

    def _pick_target_channel(self, guild):
        candidates = [
            channel for channel in guild.voice_channels
            if channel != guild.afk_channel
            and not self._is_voice_channels_managed(channel)
            and any(not member.bot for member in channel.members)
        ]
        return random.choice(candidates) if candidates else None

    async def _play_local(self, voice_client, path):
        voice_client.play(discord.FFmpegPCMAudio(str(path)))
        while voice_client.is_playing():
            await asyncio.sleep(0.5)

    async def _play_soundboard(self, voice_client, channel, sound):
        try:
            await channel.send_sound(sound)
            await asyncio.sleep(self.soundboard_wait_seconds)
            return True
        except (discord.Forbidden, discord.HTTPException):
            self.log.exception("soundboard send failed, falling back to a local sound")
            return False

    async def _play(self, voice_client, channel, kind, sound):
        if kind == "local":
            await self._play_local(voice_client, sound)
            return
        if await self._play_soundboard(voice_client, channel, sound):
            return
        local_files = self._local_sound_files()
        if local_files:
            await self._play_local(voice_client, random.choice(local_files))

    async def _troll_guild(self, guild):
        voice_client = guild.voice_client
        if voice_client is not None and Player.is_busy(voice_client):
            return
        channel = self._pick_target_channel(guild)
        if channel is None:
            return
        picked = await self._pick_sound(guild)
        if picked is None:
            return
        kind, sound = picked
        try:
            if voice_client is not None:
                await voice_client.move_to(channel)
            else:
                voice_client = await channel.connect()
            await asyncio.sleep(self.arrival_delay_seconds)
            await self._play(voice_client, channel, kind, sound)
        except (discord.Forbidden, discord.HTTPException, asyncio.TimeoutError):
            self.log.exception("troll fire failed")
        finally:
            if voice_client is not None and voice_client.is_connected():
                await voice_client.disconnect()

    def _random_next_troll_at(self):
        return int(time.time()) + random.randint(self.interval_min_seconds, self.interval_max_seconds)

    async def _run_loop(self):
        await self.check()

    @log
    async def check(self):
        now_ts = int(time.time())
        for row in self.db.get_due_troll_guilds(now_ts):
            guild = self.bot.get_guild(row["guild_id"])
            if guild is None:
                continue
            await self._troll_guild(guild)
            self.db.set_troll_state(row["guild_id"], True, self._random_next_troll_at())

    async def toggle(self, interaction):
        current = self.db.get_troll_state(interaction.guild_id)
        enabled = not (current is not None and current["enabled"])
        next_troll_at = self._random_next_troll_at() if enabled else None
        self.db.set_troll_state(interaction.guild_id, enabled, next_troll_at)
        text = self.chat.get("troll_enabled" if enabled else "troll_disabled")
        await interaction.response.send_message(text)

    @log
    def start(self):
        if not self.loop.is_running():
            self.loop.start()

    @log
    def stop(self):
        if self.loop.is_running():
            self.loop.stop()
