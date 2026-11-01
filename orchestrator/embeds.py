from datetime import datetime, timezone

import discord


class Embeds:
    def __init__(self):
        self.color_log = discord.Color.blurple()
        self.color_rss = discord.Color.orange()
        self.color_imdb = discord.Color.gold()
        self.color_free_game = discord.Color.green()
        self.color_twitch_live = discord.Color.purple()
        self.color_birthday = discord.Color.magenta()
        self.color_webhook = discord.Color.teal()

    @staticmethod
    def _base(title, color):
        return discord.Embed(title=title, color=color, timestamp=datetime.now(timezone.utc))

    def message_deleted(self, message):
        embed = self._base("Message deleted", self.color_log)
        embed.add_field(name="Author", value=f"{message.author.mention} (`{message.author}`)", inline=False)
        embed.add_field(name="Channel", value=message.channel.mention, inline=False)
        embed.add_field(name="Content", value=message.content[:1024] or "*no text*", inline=False)
        return embed

    def message_edited(self, before, after):
        embed = self._base("Message edited", self.color_log)
        embed.add_field(name="Author", value=f"{before.author.mention} (`{before.author}`)", inline=False)
        embed.add_field(name="Channel", value=before.channel.mention, inline=False)
        embed.add_field(name="Before", value=before.content[:1024] or "*no text*", inline=False)
        embed.add_field(name="After", value=after.content[:1024] or "*no text*", inline=False)
        return embed

    def rss_item(self, feed_name, title, link, published):
        embed = self._base(title or feed_name, self.color_rss)
        if link:
            embed.url = link
        for name, value in (("Feed", feed_name), ("Published", published)):
            if value:
                embed.add_field(name=name, value=value, inline=False)
        return embed

    def imdb_match(self, title, year, poster_url):
        embed = self._base(title, self.color_imdb)
        if year:
            embed.add_field(name="Year", value=str(year), inline=False)
        if poster_url:
            embed.set_image(url=poster_url)
        return embed

    def free_game(self, title, url, source, until):
        embed = self._base(title, self.color_free_game)
        embed.url = url
        embed.add_field(name="Source", value=source, inline=True)
        if until:
            embed.add_field(name="Free until", value=until, inline=True)
        return embed

    def twitch_live(self, login, title, game, thumbnail_url):
        embed = self._base(f"{login} is now live", self.color_twitch_live)
        embed.url = f"https://twitch.tv/{login}"
        if title:
            embed.add_field(name="Title", value=title, inline=False)
        if game:
            embed.add_field(name="Game", value=game, inline=False)
        if thumbnail_url:
            embed.set_image(url=thumbnail_url)
        return embed

    def birthday(self, member):
        embed = self._base("Birthday", self.color_birthday)
        embed.description = f"Happy birthday, {member.mention}!"
        return embed

    def webhook_event(self, title, description):
        embed = self._base(title, self.color_webhook)
        if description:
            embed.description = description[:4096]
        return embed
