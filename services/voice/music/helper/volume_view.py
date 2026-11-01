import discord


class VolumeView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    async def _adjust(self, interaction, delta):
        player = interaction.client.music.player
        volume = player.set_volume(self.guild_id, player.get_volume(self.guild_id) + delta)
        voice_client = interaction.guild.voice_client
        if voice_client is not None and voice_client.source is not None:
            voice_client.source.volume = volume
        await interaction.response.send_message(f"Volume: {int(volume * 100)}%", ephemeral=True)

    @discord.ui.button(label="Volume -", style=discord.ButtonStyle.secondary)
    async def volume_down(self, interaction, button):
        await self._adjust(interaction, -0.1)

    @discord.ui.button(label="Volume +", style=discord.ButtonStyle.secondary)
    async def volume_up(self, interaction, button):
        await self._adjust(interaction, 0.1)
