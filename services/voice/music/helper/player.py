import asyncio
from collections import defaultdict, deque

import discord

from dependencies.logger import Logging


class Player:
    def __init__(self, bot):
        self.bot = bot
        self.log = Logging.get_logger("music.player")
        self.queues = defaultdict(deque)
        self.current = {}
        self.volumes = {}
        self.default_volume = 0.2
        self.ffmpeg_options = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn",
        }

    @staticmethod
    def is_busy(voice_client):
        return voice_client.is_playing() or voice_client.is_paused()

    def enqueue(self, guild_id, track):
        self.queues[guild_id].append(track)

    def current_title(self, guild_id):
        return self.current.get(guild_id)

    def pending_titles(self, guild_id):
        return [title for _, title in self.queues[guild_id]]

    def get_volume(self, guild_id):
        return self.volumes.get(guild_id, self.default_volume)

    def set_volume(self, guild_id, volume):
        self.volumes[guild_id] = max(0.0, min(2.0, volume))
        return self.volumes[guild_id]

    def clear(self, guild_id):
        self.queues[guild_id].clear()
        self.current.pop(guild_id, None)

    async def _update_channel_status(self, voice_client, title):
        try:
            await voice_client.channel.edit(status=title[:500])
        except (discord.Forbidden, discord.HTTPException):
            pass

    def advance(self, guild_id, voice_client, error=None):
        if error:
            self.log.error("playback error: %s", error)
        queue = self.queues[guild_id]
        if not queue:
            self.current.pop(guild_id, None)
            return
        stream_url, title = queue.popleft()
        self.current[guild_id] = title
        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(stream_url, **self.ffmpeg_options),
            volume=self.get_volume(guild_id),
        )
        voice_client.play(source, after=lambda err: self.advance(guild_id, voice_client, err))
        asyncio.run_coroutine_threadsafe(self._update_channel_status(voice_client, title), self.bot.loop)
