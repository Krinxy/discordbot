import time
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import discord
from discord.ext import tasks

from dependencies.auth import Auth
from dependencies.logger import Logging, log
from orchestrator.registry import ServiceRegistry
from services.media_requests.tickets.helper import TicketBlockedButton
from services.media_requests.tickets.util import ContentHasher


@ServiceRegistry.instance().route("/tickets")
class Tickets:
    def __init__(self, db, bot, settings, chat, imdb):
        self.db = db
        self.bot = bot
        self.chat = chat
        self.imdb = imdb
        self.log = Logging.get_logger("tickets")
        self.content_hasher = ContentHasher()
        self.emojis = {
            status: discord.PartialEmoji.from_str(value)
            for status, value in settings.get("tickets", "emojis", default={}).items()
        }
        self.emoji_status = {self._emoji_key(emoji): status for status, emoji in self.emojis.items()}
        self.archive_after_days = settings.get("tickets", "archive_after_days", default=3)
        self.reminder_interval_days = settings.get("tickets", "reminder_interval_days", default=2)
        self.check_interval_seconds = settings.get("tickets", "check_interval_seconds", default=3600)
        self.reminder_user_ids = self._verified_reminder_user_ids(settings.reminder_user_ids)
        self.ticket_channels = {
            int(entry["channel_id"]): entry.get("name", "")
            for entry in settings.get("watch", "channels", default=[])
            if entry.get("tickets")
        }
        self.allowed_role_ids = set(settings.get("tickets", "allowed_role_ids", default=[]))
        self.blacklisted_user_ids = settings.blacklisted_ticket_user_ids
        self.archive_loop = tasks.loop(seconds=self.check_interval_seconds)(self._run_archive_loop)
        self.reminder_loop = tasks.loop(seconds=self.check_interval_seconds)(self._run_reminder_loop)

    def _verified_reminder_user_ids(self, reminder_user_ids):
        auth = Auth.instance()
        verified = []
        for reminder_user_id in reminder_user_ids:
            if not auth.enabled or auth.hash_id(reminder_user_id) not in auth.policy.users:
                self.log.critical("a configured reminder_user_id is not an authorized hashed user, skipping it")
                continue
            verified.append(reminder_user_id)
        return verified

    @staticmethod
    def _now_iso():
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _emoji_key(emoji):
        return emoji.id if emoji.id is not None else str(emoji)

    async def _duplicate_reply(self, message, existing):
        text = self.chat.get("ticket_duplicate", status=existing["status"])
        try:
            async with message.channel.typing():
                await message.reply(text, delete_after=300, mention_author=False)
        except discord.HTTPException:
            pass
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            pass

    async def _reject(self, message, chat_key):
        text = self.chat.get(chat_key)
        try:
            await message.reply(text, delete_after=300, mention_author=False)
        except discord.HTTPException:
            pass
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            pass

    async def _set_reaction(self, message, old_status, new_status):
        old_emoji = self.emojis.get(old_status)
        if old_emoji:
            try:
                await message.remove_reaction(old_emoji, message.guild.me)
            except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                pass
        new_emoji = self.emojis.get(new_status)
        if new_emoji:
            try:
                await message.add_reaction(new_emoji)
            except (discord.Forbidden, discord.HTTPException):
                pass

    async def _run_archive_loop(self):
        await self.check_archive()

    async def _run_reminder_loop(self):
        await self.check_reminders()

    @log
    async def check_archive(self):
        cutoff = (datetime.now(timezone.utc) - timedelta(days=self.archive_after_days)).isoformat()
        for ticket in self.db.get_tickets_due_for_archive(cutoff):
            try:
                channel_id = ticket["channel_id"]
                channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
                message = await channel.fetch_message(ticket["message_id"])
                await message.delete()
            except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                pass
            self.db.set_ticket_status(ticket["id"], "archive", archived_at=self._now_iso())
            self.db.set_ticket_blocked(ticket["id"], None)

    async def _send_reminder_dm(self, user_id, ticket):
        user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
        view = discord.ui.View(timeout=None)
        view.add_item(TicketBlockedButton(ticket["id"]))
        link = f"https://discord.com/channels/{ticket['guild_id']}/{ticket['channel_id']}/{ticket['message_id']}"
        text = self.chat.get("ticket_reminder", content=ticket["content"][:500], link=link)
        async with user.typing():
            await user.send(text, view=view)

    @log
    async def check_reminders(self):
        if not self.reminder_user_ids:
            return
        now_ts = int(time.time())
        for row in self.db.get_due_ticket_reminders(now_ts):
            if (ticket := self.db.get_ticket(row["ticket_id"])) is None:
                self.db.set_ticket_blocked(row["ticket_id"], None)
                continue
            for user_id in self.reminder_user_ids:
                try:
                    await self._send_reminder_dm(user_id, ticket)
                except (discord.Forbidden, discord.HTTPException):
                    self.log.exception("reminder DM failed for ticket %s", ticket["id"])
            self.db.set_reminder_pending(row["ticket_id"])

    async def reset_reminder(self, ticket_id, interaction):
        next_check_at = int(time.time()) + self.reminder_interval_days * 86400
        self.db.set_ticket_blocked(ticket_id, next_check_at)
        await interaction.response.send_message("Got it, I'll check back again in a few days.", ephemeral=True)

    async def handle_message(self, message, backfill=False):
        if message.channel.id not in self.ticket_channels:
            return False
        if message.author.bot or message.guild is None:
            return False
        if not backfill:
            member_role_ids = {role.id for role in message.author.roles}
            if not (self.allowed_role_ids and member_role_ids & self.allowed_role_ids):
                await self._reject(message, "tickets_role_required")
                return True
            if message.author.id in self.blacklisted_user_ids:
                await self._reject(message, "tickets_user_blacklisted")
                return True
        content_hash = self.content_hasher.hash(message.content)
        if (existing := self.db.get_ticket_by_hash(message.channel.id, content_hash)) is not None:
            if not backfill:
                await self._duplicate_reply(message, existing)
            return True
        ticket_id = self.db.add_ticket(
            message.guild.id, message.channel.id, message.id,
            message.author.id, str(message.author), message.content[:2000], content_hash,
        )
        if backfill:
            await self._react_open(message)
            return True
        await self._resolve_imdb(ticket_id, message)
        return True

    async def _react_open(self, message):
        open_emoji = self.emojis.get("open")
        if open_emoji:
            try:
                await message.add_reaction(open_emoji)
            except (discord.Forbidden, discord.HTTPException):
                pass

    async def _resolve_imdb(self, ticket_id, message):
        kind, candidates = await self.imdb.resolve(message.content)
        if kind == "single":
            await self.finalize_imdb(ticket_id, message, candidates[0])
        elif kind == "ambiguous":
            await self.imdb.prompt_pick(ticket_id, message, candidates)
        elif kind == "error":
            await self._react_open(message)
        else:
            await self.finalize_imdb(ticket_id, message, None)

    async def finalize_imdb(self, ticket_id, message, candidate):
        anchor, status = await self.imdb.finalize(ticket_id, message, candidate)
        if anchor is not None:
            self.db.set_ticket_message(ticket_id, anchor.id)
            await self._react_open(anchor)
        elif status in ("no_match", "blacklisted"):
            self.db.set_ticket_status(ticket_id, "archive", archived_at=self._now_iso())

    async def cancel_imdb(self, ticket_id, message):
        await self.imdb.cancel(ticket_id, message, "timeout", "imdb_pick_timeout")
        self.db.set_ticket_status(ticket_id, "archive", archived_at=self._now_iso())

    async def handle_reaction(self, payload):
        if payload.user_id == self.bot.user.id:
            return
        if payload.channel_id not in self.ticket_channels:
            return
        if (ticket := self.db.get_ticket_by_message(payload.message_id)) is None:
            return
        if (status := self.emoji_status.get(self._emoji_key(payload.emoji))) is None:
            return
        await self._apply_status(payload, ticket, status)

    @Auth.instance().user
    async def _apply_status(self, payload, ticket, status):
        channel = self.bot.get_channel(payload.channel_id) or await self.bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        old_status = ticket["status"]
        if status == "archive":
            self.db.set_ticket_status(ticket["id"], "archive", archived_at=self._now_iso())
            self.db.set_ticket_blocked(ticket["id"], None)
            try:
                await message.delete()
            except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                pass
            return
        closed_at = self._now_iso() if status == "closed" else None
        self.db.set_ticket_status(ticket["id"], status, closed_at=closed_at)
        due = int(time.time()) + self.reminder_interval_days * 86400 if status == "currently_not_possible" else None
        self.db.set_ticket_blocked(ticket["id"], due)
        await self._set_reaction(message, old_status, status)

    async def backfill_reactions(self, channel):
        for row in self.db.get_open_tickets(channel.id):
            ticket = dict(row)
            try:
                message = await channel.fetch_message(ticket["message_id"])
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                continue
            for reaction in message.reactions:
                emoji = discord.PartialEmoji.from_str(str(reaction.emoji))
                status = self.emoji_status.get(self._emoji_key(emoji))
                if status is None or status == ticket["status"]:
                    continue
                async for user in reaction.users():
                    if user.bot:
                        continue
                    member = message.guild.get_member(user.id)
                    payload = SimpleNamespace(
                        user_id=user.id, member=member, channel_id=channel.id, message_id=message.id,
                    )
                    await self._apply_status(payload, ticket, status)
                    ticket["status"] = status
                    break

    @log
    def start(self):
        if self.ticket_channels and not self.archive_loop.is_running():
            self.archive_loop.start()
        if self.ticket_channels and not self.reminder_loop.is_running():
            self.reminder_loop.start()

    @log
    def stop(self):
        if self.archive_loop.is_running():
            self.archive_loop.stop()
        if self.reminder_loop.is_running():
            self.reminder_loop.stop()
