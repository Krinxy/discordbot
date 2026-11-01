import asyncio
from urllib.parse import quote

import aiohttp
import discord

from dependencies.logger import Logging
from orchestrator.registry import ServiceRegistry
from services.media_requests.imdb.helper import ImdbPickerView, ImdbRepository
from services.media_requests.imdb.util import ImdbLinkResolver


@ServiceRegistry.instance().route("/imdb")
class Imdb:
    def __init__(self, bot, http, chat, embeds, db, settings):
        self.bot = bot
        self.http = http
        self.chat = chat
        self.embeds = embeds
        self.db = ImdbRepository(db)
        self.log = Logging.get_logger("imdb")
        self.link_resolver = ImdbLinkResolver()
        self.base_url = "https://v2.sg.media-imdb.com/suggestion"
        self.max_query_length = 100
        self.title_categories = {"movie", "tvSeries", "tvMovie", "tvMiniSeries", "video"}
        self.person_blacklist = {
            name.lower() for name in settings.get("tickets", "blacklist", "person_names", default=[])
        }
        self.tag_blacklist = set(settings.get("tickets", "blacklist", "tags", default=[]))

    @staticmethod
    def _first_char(text):
        for char in text.strip().lower():
            if char.isalnum():
                return char
        return "a"

    async def _fetch(self, query):
        trimmed = query.strip()[: self.max_query_length]
        url = f"{self.base_url}/{self._first_char(trimmed)}/{quote(trimmed, safe='')}.json"
        try:
            data = await self.http.get_json(url)
        except (aiohttp.ClientError, ValueError, asyncio.TimeoutError):
            self.log.exception("imdb suggest request failed for %s", query)
            return None
        return data.get("d", [])

    def _candidates_from_json(self, raw):
        candidates = []
        for entry in raw:
            qid = entry.get("qid")
            if qid not in self.title_categories or qid in self.tag_blacklist:
                continue
            candidates.append({
                "id": entry.get("id"),
                "title": entry.get("l"),
                "year": entry.get("y") or entry.get("yr"),
                "poster_url": entry.get("i", {}).get("imageUrl"),
                "stars": entry.get("s", ""),
            })
        return candidates

    def _is_blacklisted(self, candidate):
        stars = (candidate.get("stars") or "").lower()
        return any(name in stars for name in self.person_blacklist)

    async def resolve(self, text):
        title_id = self.link_resolver.resolve(text)
        if title_id is not None:
            raw = await self._fetch(title_id)
            if raw is None:
                return "error", []
            candidates = self._candidates_from_json(raw)
            return ("single", candidates[:1]) if candidates else ("none", [])
        raw = await self._fetch(text)
        if raw is None:
            return "error", []
        candidates = self._candidates_from_json(raw)
        if not candidates:
            return "none", []
        if len(candidates) == 1:
            return "single", candidates
        return "ambiguous", candidates[:5]

    async def _replace_message(self, message, text, delete_after=None, embed=None):
        try:
            anchor = await message.channel.send(text, embed=embed, delete_after=delete_after)
        except discord.HTTPException:
            return None
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            pass
        return anchor

    async def cancel(self, ticket_id, message, status, chat_key):
        self.db.set_match(ticket_id, None, None, None, None, status)
        await self._replace_message(message, self.chat.get(chat_key), delete_after=300)

    async def finalize(self, ticket_id, message, candidate):
        if candidate is None:
            await self.cancel(ticket_id, message, "no_match", "imdb_no_match")
            return None, "no_match"
        if self._is_blacklisted(candidate):
            self.db.set_match(
                ticket_id, candidate["id"], candidate["title"], candidate["year"], candidate["poster_url"],
                "blacklisted",
            )
            await self._replace_message(message, self.chat.get("imdb_person_blacklisted"), delete_after=300)
            return None, "blacklisted"
        self.db.set_match(
            ticket_id, candidate["id"], candidate["title"], candidate["year"], candidate["poster_url"], "matched",
        )
        embed = self.embeds.imdb_match(candidate["title"], candidate["year"], candidate["poster_url"])
        text = self.chat.get("imdb_match", title=candidate["title"], year=candidate["year"])
        anchor = await self._replace_message(message, text, embed=embed)
        return anchor, "matched"

    async def prompt_pick(self, ticket_id, message, candidates):
        self.db.set_match(ticket_id, None, None, None, None, "pending")
        view = ImdbPickerView(self.bot, ticket_id, message, candidates)
        options = "\n".join(f"- {c['title']} ({c['year']})" for c in candidates)
        text = self.chat.get("imdb_ambiguous_prompt", options=options)
        try:
            view.prompt_message = await message.reply(text, view=view, mention_author=False)
        except discord.HTTPException:
            pass
