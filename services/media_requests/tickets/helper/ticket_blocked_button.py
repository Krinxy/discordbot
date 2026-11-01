import discord


class TicketBlockedButton(
    discord.ui.DynamicItem[discord.ui.Button],
    template=r"ticket_blocked:(?P<ticket_id>[0-9]+)",
):
    def __init__(self, ticket_id):
        super().__init__(
            discord.ui.Button(
                label="Still not possible",
                style=discord.ButtonStyle.secondary,
                custom_id=f"ticket_blocked:{ticket_id}",
            )
        )
        self.ticket_id = ticket_id

    @classmethod
    async def from_custom_id(cls, _interaction, _item, match):
        return cls(int(match["ticket_id"]))

    async def callback(self, interaction):
        await interaction.client.tickets.reset_reminder(self.ticket_id, interaction)
