import calendar
from datetime import date

from discord.ext import tasks

from dependencies.logger import Logging, log
from orchestrator.registry import ServiceRegistry


@ServiceRegistry.instance().route("/birthdays")
class Birthdays:
    def __init__(self, db, bot, embeds, settings):
        self.db = db
        self.bot = bot
        self.embeds = embeds
        self.log = Logging.get_logger("birthdays")
        self.channel_id = settings.get("birthdays", "channel_id", default=0)
        self.check_interval_seconds = settings.get("birthdays", "check_interval_seconds", default=3600)
        self.leap_reference_year = 2000
        self.posted_today = set()
        self.last_checked_date = None
        if not self.channel_id:
            self.log.critical("birthdays.channel_id is not set, birthday announcements will not be posted")
        self.loop = tasks.loop(seconds=self.check_interval_seconds)(self._run_check_loop)

    def _max_day(self, month):
        return calendar.monthrange(self.leap_reference_year, month)[1]

    async def set_birthday(self, interaction, month, day):
        if not (1 <= month <= 12) or not (1 <= day <= self._max_day(month)):
            await interaction.response.send_message("That's not a valid date.", ephemeral=True)
            return
        self.db.set_birthday(interaction.guild_id, interaction.user.id, month, day)
        await interaction.response.send_message("Your birthday has been saved.", ephemeral=True)

    async def _post_birthday(self, guild, member):
        channel = self.bot.get_channel(int(self.channel_id))
        if channel is None:
            return
        await channel.send(embed=self.embeds.birthday(member))

    async def _check_guild(self, guild, today):
        for row in self.db.get_birthdays_on(guild.id, today.month, today.day):
            key = (guild.id, row["user_id"])
            if key in self.posted_today:
                continue
            member = guild.get_member(row["user_id"])
            if member is not None:
                await self._post_birthday(guild, member)
            self.posted_today.add(key)

    async def _run_check_loop(self):
        await self.check()

    @log
    async def check(self):
        if not self.channel_id:
            return
        today = date.today()
        if today != self.last_checked_date:
            self.posted_today.clear()
            self.last_checked_date = today
        for guild in self.bot.guilds:
            try:
                await self._check_guild(guild, today)
            except Exception:
                self.log.exception("birthday check failed for guild %s", guild.id)

    @log
    def start(self):
        if not self.loop.is_running():
            self.loop.start()

    @log
    def stop(self):
        if self.loop.is_running():
            self.loop.stop()
