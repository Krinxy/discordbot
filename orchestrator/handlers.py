import functools

from dependencies.auth import Auth


class Handlers:
    def __init__(self, bot, router):
        self.bot = bot
        self.music_routes = {
            "music_play": "play", "music_skip": "skip", "music_pause": "pause",
            "music_resume": "resume", "music_stop": "stop", "music_queue": "queue",
        }
        self.routes = ("logchannel", "export", "idle", "troll", "birthday", "export_movies", *self.music_routes)
        for name in self.routes:
            handler = getattr(self, name, None) or functools.partial(self._music, self.music_routes[name])
            router.add(name, handler)

    async def _music(self, action, interaction, **kwargs):
        await self.bot.music.handle(action, interaction, **kwargs)

    async def idle(self, interaction):
        await self.bot.music.handle("idle", interaction)

    async def troll(self, interaction):
        await self.bot.troll.toggle(interaction)

    @Auth.instance().user
    async def logchannel(self, interaction, channel):
        self.bot.log.set_channel(interaction.guild, channel)
        await interaction.response.send_message(f"Log channel is now {channel.mention}.")

    @Auth.instance().user
    async def export(self, interaction):
        path, count = self.bot.transfer.export()
        text = f"{count} request(s) exported to {path.name}." if path else "No new requests to export."
        await interaction.response.send_message(text, ephemeral=True)

    async def birthday(self, interaction, month, day):
        await self.bot.birthdays.set_birthday(interaction, month, day)

    @Auth.instance().user
    async def export_movies(self, interaction):
        count = await self.bot.watchlist_export.export()
        text = f"{count} film(s) exported." if count else "Nothing new to export."
        await interaction.response.send_message(text, ephemeral=True)
