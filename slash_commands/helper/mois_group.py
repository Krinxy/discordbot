import discord
from discord import app_commands

from dependencies.auth import Auth
from slash_commands.helper.role_gate import RoleGate


class MoisGroup(app_commands.Group):
    role_gated_commands = {"idle", "troll"}
    open_commands = {"birthday"}

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        name = interaction.command.name if interaction.command is not None else None
        if name in self.open_commands:
            return True
        if name in self.role_gated_commands:
            return await RoleGate.check(interaction, "music", "allowed_role_ids")
        return await self._admin_check(interaction)

    @Auth.instance().user
    async def _admin_check(self, interaction: discord.Interaction) -> bool:
        return True
