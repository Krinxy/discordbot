import discord
from discord import app_commands

from slash_commands.helper.role_gate import RoleGate


class MusicGroup(app_commands.Group):
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await RoleGate.check(interaction, "music", "allowed_role_ids")
