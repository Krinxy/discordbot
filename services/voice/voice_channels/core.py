import asyncio
import time
from collections import defaultdict

import discord
from discord.ext import tasks

from dependencies.logger import Logging, log
from orchestrator.registry import ServiceRegistry
from services.voice.voice_channels.util import SlotNaming


@ServiceRegistry.instance().route("/voice_channels")
class VoiceChannels:
    def __init__(self, bot, settings):
        self.bot = bot
        self.log = Logging.get_logger("voice_channels")
        self.slot_naming = SlotNaming()
        self.check_interval_seconds = settings.get("voice_channels", "check_interval_seconds", default=300)
        self.categories = settings.get("voice_channels", "categories", default=[])
        self.locks = defaultdict(asyncio.Lock)
        self.creation_times = defaultdict(list)
        self.check_loop = tasks.loop(seconds=self.check_interval_seconds)(self._run_check_loop)

    def _managed_channels(self, category, name_pool):
        afk_channel = category.guild.afk_channel
        managed = []
        for channel in category.voice_channels:
            if channel == afk_channel:
                continue
            slot = self.slot_naming.slot_from_name(channel.name, name_pool)
            if slot is not None:
                managed.append((slot, channel))
        return managed

    def _user_at_creation_limit(self, category_id, user_id, max_creations_per_user):
        window_start = time.monotonic() - self.check_interval_seconds
        key = (category_id, user_id)
        times = [t for t in self.creation_times[key] if t >= window_start]
        if times:
            self.creation_times[key] = times
        else:
            self.creation_times.pop(key, None)
        return len(times) >= max_creations_per_user

    def _record_creation(self, category_id, user_id):
        self.creation_times[(category_id, user_id)].append(time.monotonic())

    async def _create_channel(self, category, name_pool, occupied_slots, max_generic_channels):
        slot = self.slot_naming.next_free_slot(occupied_slots, name_pool, max_generic_channels)
        if slot is None:
            return
        try:
            await category.create_voice_channel(self.slot_naming.name_for_slot(slot, name_pool))
        except (discord.Forbidden, discord.HTTPException):
            self.log.exception("failed to create voice channel at slot %s", slot)

    async def _delete_channel(self, channel):
        try:
            await channel.delete()
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            self.log.exception("failed to delete voice channel %s", channel.id)

    async def _reconcile_category(self, category, entry, triggering_user_id):
        name_pool = entry["name_pool"]
        max_generic_channels = entry["max_generic_channels"]
        max_creations_per_user = entry.get("max_creations_per_user", 2)
        managed = self._managed_channels(category, name_pool)
        occupied_slots = {slot for slot, channel in managed if channel.members}
        empty = sorted((slot, channel) for slot, channel in managed if not channel.members)
        if not empty and len(managed) < max_generic_channels:
            throttled = triggering_user_id is not None and self._user_at_creation_limit(
                category.id, triggering_user_id, max_creations_per_user,
            )
            if not throttled:
                await self._create_channel(category, name_pool, occupied_slots, max_generic_channels)
                if triggering_user_id is not None:
                    self._record_creation(category.id, triggering_user_id)
        elif len(empty) >= 2:
            for _, channel in empty[1:]:
                await self._delete_channel(channel)

    async def _reconcile_locked(self, category, entry, triggering_user_id):
        key = (category.guild.id, category.id)
        async with self.locks[key]:
            await self._reconcile_category(category, entry, triggering_user_id)

    async def _reconcile_all(self, triggering_user_id):
        for entry in self.categories:
            category = self.bot.get_channel(int(entry["category_id"]))
            if not isinstance(category, discord.CategoryChannel):
                continue
            await self._reconcile_locked(category, entry, triggering_user_id)

    async def _run_check_loop(self):
        await self.check()

    @log
    async def check(self):
        await self._reconcile_all(triggering_user_id=None)

    @log
    async def handle_voice_state_update(self, member, before, after):
        await self._reconcile_all(triggering_user_id=member.id)

    @log
    def start(self):
        if self.categories and not self.check_loop.is_running():
            self.check_loop.start()

    @log
    def stop(self):
        if self.check_loop.is_running():
            self.check_loop.stop()
