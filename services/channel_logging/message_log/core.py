import discord

from dependencies.logger import log
from orchestrator.registry import ServiceRegistry


@ServiceRegistry.instance().route("/message_log")
class Log:
    def __init__(self, db, embeds):
        self.db = db
        self.embeds = embeds

    def get_channel(self, guild):
        if (channel_id := self.db.get_log_channel_id(guild.id)) is None:
            return None
        channel = guild.get_channel(int(channel_id))
        return channel if isinstance(channel, discord.TextChannel) else None

    def set_channel(self, guild, channel):
        self.db.set_log_channel_id(guild.id, channel.id)

    @log
    async def log_delete(self, message):
        await self.log_embed(message.guild, self.embeds.message_deleted(message))

    @log
    async def log_edit(self, before, after):
        await self.log_embed(before.guild, self.embeds.message_edited(before, after))

    async def log_embed(self, guild, embed):
        channel = self.get_channel(guild)
        if channel is None:
            return
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass
