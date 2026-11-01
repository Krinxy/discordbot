import discord
from discord import app_commands
from discord.ext import commands

from slash_commands.helper import MoisGroup, MusicGroup


class CommandsCog(commands.Cog):
    mois = MoisGroup(name="mois", description="Mois D Zois commands")
    music = MusicGroup(name="music", description="Music commands", parent=mois)

    def __init__(self, bot):
        self.bot = bot

    @mois.command(name="logchannel", description="Sets the channel for log messages")
    @app_commands.default_permissions(manage_guild=True)
    async def logchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.bot.router.dispatch("logchannel", interaction, channel=channel)

    @mois.command(name="export", description="Exports all new requests as JSON")
    @app_commands.default_permissions(manage_guild=True)
    async def export(self, interaction: discord.Interaction):
        await self.bot.router.dispatch("export", interaction)

    @mois.command(name="idle", description="Joins your voice channel and just hangs out")
    async def idle(self, interaction: discord.Interaction):
        await self.bot.router.dispatch("idle", interaction)

    @mois.command(name="troll", description="Toggles troll mode: randomly joins a channel and plays a sound while idle")
    async def troll(self, interaction: discord.Interaction):
        await self.bot.router.dispatch("troll", interaction)

    @mois.command(name="birthday", description="Sets your birthday (month, day)")
    async def birthday(self, interaction: discord.Interaction, month: int, day: int):
        await self.bot.router.dispatch("birthday", interaction, month=month, day=day)

    @mois.command(name="export_movies", description="Pushes the collected film recommendations to the configured API")
    @app_commands.default_permissions(manage_guild=True)
    async def export_movies(self, interaction: discord.Interaction):
        await self.bot.router.dispatch("export_movies", interaction)

    @music.command(name="play", description="Plays a link or adds it to the queue")
    async def music_play(self, interaction: discord.Interaction, link: str):
        await self.bot.router.dispatch("music_play", interaction, link=link)

    @music.command(name="skip", description="Skips the current track")
    async def music_skip(self, interaction: discord.Interaction):
        await self.bot.router.dispatch("music_skip", interaction)

    @music.command(name="pause", description="Pauses playback")
    async def music_pause(self, interaction: discord.Interaction):
        await self.bot.router.dispatch("music_pause", interaction)

    @music.command(name="resume", description="Resumes playback")
    async def music_resume(self, interaction: discord.Interaction):
        await self.bot.router.dispatch("music_resume", interaction)

    @music.command(name="stop", description="Stops playback and leaves the voice channel")
    async def music_stop(self, interaction: discord.Interaction):
        await self.bot.router.dispatch("music_stop", interaction)

    @music.command(name="queue", description="Shows the current queue")
    async def music_queue(self, interaction: discord.Interaction):
        await self.bot.router.dispatch("music_queue", interaction)
