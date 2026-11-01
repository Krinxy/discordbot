import functools

import discord

from dependencies.auth import Auth


class ImdbPickerView(discord.ui.View):
    def __init__(self, bot, ticket_id, message, candidates):
        super().__init__(timeout=300)
        self.bot = bot
        self.ticket_id = ticket_id
        self.message = message
        self.prompt_message = None
        for candidate in candidates:
            label = f"{candidate['title']} ({candidate['year']})"[:80]
            button = discord.ui.Button(label=label, style=discord.ButtonStyle.secondary)
            button.callback = functools.partial(self._pick, candidate)
            self.add_item(button)

    @Auth.instance().user
    async def _pick(self, candidate, interaction):
        self.stop()
        await interaction.response.defer()
        try:
            await interaction.message.delete()
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            pass
        await interaction.client.tickets.finalize_imdb(self.ticket_id, self.message, candidate)

    async def on_timeout(self):
        if self.prompt_message is not None:
            try:
                await self.prompt_message.delete()
            except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                pass
        await self.bot.tickets.cancel_imdb(self.ticket_id, self.message)
