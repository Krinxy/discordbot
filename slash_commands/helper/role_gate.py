class RoleGate:
    @staticmethod
    async def check(interaction, *config_path):
        allowed_role_ids = set(interaction.client.settings.get(*config_path, default=[]))
        member_role_ids = {role.id for role in getattr(interaction.user, "roles", [])}
        allowed = bool(allowed_role_ids) and bool(member_role_ids & allowed_role_ids)
        if not allowed:
            await interaction.response.send_message("No permission.", ephemeral=True)
        return allowed
