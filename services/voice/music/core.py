from dependencies.logger import log
from orchestrator.registry import ServiceRegistry
from services.voice.music.helper import Player, SongResolver, VolumeView


@ServiceRegistry.instance().route("/music")
class Music:
    def __init__(self, bot, chat):
        self.chat = chat
        self.player = Player(bot)
        self.resolver = SongResolver()
        self.actions = {
            "idle": self._idle,
            "play": self._play,
            "skip": self._skip,
            "pause": self._pause,
            "resume": self._resume,
            "stop": self._stop,
            "queue": self._queue,
        }

    @staticmethod
    async def _ensure_voice(interaction):
        voice_client = interaction.guild.voice_client
        if voice_client is not None:
            return voice_client
        return await interaction.user.voice.channel.connect()

    @staticmethod
    async def _require_voice_client(interaction, predicate, fail_text):
        voice_client = interaction.guild.voice_client
        if voice_client is None or not predicate(voice_client):
            await interaction.response.send_message(fail_text, ephemeral=True)
            return None
        return voice_client

    async def _idle(self, interaction):
        if interaction.user.voice is None:
            await interaction.response.send_message("You need to be in a voice channel.", ephemeral=True)
            return
        if interaction.guild.voice_client is not None:
            await interaction.response.send_message("Already here.", ephemeral=True)
            return
        await self._ensure_voice(interaction)
        await interaction.response.send_message(self.chat.get("idle"))

    async def _play(self, interaction, link=None):
        if interaction.user.voice is None:
            await interaction.response.send_message("You need to be in a voice channel.", ephemeral=True)
            return
        await interaction.response.defer()
        try:
            stream_url, title = await self.resolver.resolve(link)
        except ValueError:
            await interaction.followup.send("This link is not allowed.", ephemeral=True)
            return
        voice_client = await self._ensure_voice(interaction)
        self.player.enqueue(interaction.guild_id, (stream_url, title))
        if self.player.is_busy(voice_client):
            await interaction.followup.send(self.chat.get("music_queued", title=title))
        else:
            self.player.advance(interaction.guild_id, voice_client)
            await interaction.followup.send(
                self.chat.get("music_playing", title=title),
                view=VolumeView(interaction.guild_id),
            )

    async def _skip(self, interaction):
        voice_client = await self._require_voice_client(
            interaction, lambda vc: vc.is_playing(), "Nothing is playing right now.",
        )
        if voice_client is None:
            return
        voice_client.stop()
        await interaction.response.send_message("Skipped.")

    async def _pause(self, interaction):
        voice_client = await self._require_voice_client(
            interaction, lambda vc: vc.is_playing(), "Nothing is playing right now.",
        )
        if voice_client is None:
            return
        voice_client.pause()
        await interaction.response.send_message("Paused.")

    async def _resume(self, interaction):
        voice_client = await self._require_voice_client(
            interaction, lambda vc: vc.is_paused(), "Nothing is paused.",
        )
        if voice_client is None:
            return
        voice_client.resume()
        await interaction.response.send_message("Resumed.")

    async def _stop(self, interaction):
        voice_client = interaction.guild.voice_client
        self.player.clear(interaction.guild_id)
        if voice_client is not None:
            await voice_client.disconnect()
        await interaction.response.send_message("Playback stopped.")

    async def _queue(self, interaction):
        current = self.player.current_title(interaction.guild_id)
        upcoming = self.player.pending_titles(interaction.guild_id)
        lines = [f"Now playing: {current}"] if current else []
        lines.extend(f"{i}. {title}" for i, title in enumerate(upcoming, start=1))
        await interaction.response.send_message("\n".join(lines) if lines else "The queue is empty.")

    @log
    async def handle(self, action, interaction, **kwargs):
        method = self.actions.get(action)
        if method is None:
            await interaction.response.send_message(self.chat.get("music_unknown_command"), ephemeral=True)
            return
        await method(interaction, **kwargs)
